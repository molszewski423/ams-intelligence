"""
AMS Intelligence — Module 1: Resistance Trend Analyzer

Fetches FAERS adverse event data for a primary antibiotic and a comparator,
computes PRR/ROR disproportionality signals, performs temporal pre/post
analysis around a formulary-change cutoff, integrates WHONET/ATLAS resistance
rates, and generates a structured LLM interpretation + PDF summary.

Primary use case: cefazolin vs cefpodoxime (formulary switch analysis).
"""

from __future__ import annotations
import json
import time
from dataclasses import dataclass, field
from datetime import datetime, date

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from config import OLLAMA_BASE_URL, REASON_MODEL, OUTPUT_DIR
from data_sources.faers_client import (
    fetch_reaction_counts, fetch_total_reports,
    fetch_yearly_counts, categorize_reactions,
)
from data_sources.whonet_client import load_whonet_data, resistance_trend_summary
from data_sources.atlas_client import load_atlas_data
from shared.disproportionality import compute_signals, temporal_compare, SignalResult
from shared.pdf_exporter import generate_resistance_full_report

_SYSTEM_PROMPT = """\
You are a clinical pharmacist and antimicrobial stewardship specialist with expertise
in pharmacovigilance signal detection and formulary management.

You are interpreting FAERS disproportionality analysis (PRR/ROR) for antimicrobial
safety signals. Apply strict AMS clinical reasoning:
- Consider confounding by indication (last-resort drugs have high AE rates unrelated to drug)
- Distinguish mechanistic signals from noise
- Reference relevant clinical trial data and resistance surveillance context
- Flag signals requiring immediate formulary committee review
- Be concise, evidence-based, and clinically actionable

Format key_findings as a JSON array of strings (5-7 findings, each < 120 characters).
End with: INTERPRETATION: <3-5 sentence clinical interpretation paragraph>
"""

_INTERPRETATION_TEMPLATE = """\
Drug analyzed: {drug}
Comparator: {comparator}
Analysis period: {period}
Total drug FAERS reports: {drug_total:,}
Total comparator FAERS reports: {bg_total:,}

Top Evans-positive signals (PRR ≥ 2, N ≥ 3, chi² ≥ 4):
{signal_table}

Pre-cutoff ({pre_period}) vs Post-cutoff ({post_period}) top PRR changes:
{temporal_table}

AMS reaction category breakdown for {drug}:
{category_table}

Provide key_findings JSON array and INTERPRETATION paragraph.
"""


@dataclass
class ResistanceAnalysis:
    drug: str
    comparator: str
    start_year: int
    cutoff_year: int
    end_year: int
    drug_total: int
    bg_total: int
    signals: list[SignalResult]
    pre_signals: list[SignalResult]
    post_signals: list[SignalResult]
    temporal_compare: list[dict]
    yearly_data: dict[int, dict[str, int]]
    ams_categories: dict[str, int]
    whonet_summary: dict
    atlas_records: list
    key_findings: list[str]
    interpretation: str
    pdf_path: str | None = None
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())


def _format_signal_table(signals: list[SignalResult], n: int = 10) -> str:
    top = [s for s in signals if s.signal][:n]
    if not top:
        return "No Evans-positive signals detected."
    lines = ["Reaction PT | N | PRR | ROR | chi²"]
    for s in top:
        lines.append(f"{s.reaction_pt} | {s.drug_cases} | {s.prr:.2f} | {s.ror:.2f} | {s.chi2:.1f}")
    return "\n".join(lines)


def _format_temporal_table(compare: list[dict], n: int = 8) -> str:
    top = sorted(compare, key=lambda r: abs(r["delta"]), reverse=True)[:n]
    if not top:
        return "Insufficient data for temporal comparison."
    lines = ["Reaction PT | Pre PRR | Post PRR | Delta"]
    for r in top:
        lines.append(f"{r['reaction_pt']} | {r['pre_prr']:.2f} | {r['post_prr']:.2f} | {r['delta']:+.2f}")
    return "\n".join(lines)


def _parse_llm_response(response: str) -> tuple[list[str], str]:
    """Extract key_findings list and INTERPRETATION paragraph from LLM output."""
    import re
    findings: list[str] = []
    interpretation = ""

    # Try JSON array for findings
    json_match = re.search(r'\[([^\]]+)\]', response, re.S)
    if json_match:
        try:
            findings = json.loads(f"[{json_match.group(1)}]")
        except Exception:
            findings = [line.strip().lstrip('-•1234567890. ')
                        for line in json_match.group(1).splitlines()
                        if line.strip()]

    # Extract INTERPRETATION paragraph
    interp_match = re.search(r'INTERPRETATION:\s*(.+)', response, re.S)
    if interp_match:
        interpretation = interp_match.group(1).strip()
    elif not interpretation:
        interpretation = response.strip()[-1000:]

    return findings[:7], interpretation


def run_resistance_analysis(
    drug: str = "cefazolin",
    comparator: str = "cefpodoxime",
    cutoff_year: int = 2020,
    start_year: int = 2015,
    end_year: int | None = None,
    organism: str = "Staphylococcus aureus",
    run_llm: bool = True,
) -> ResistanceAnalysis:
    """
    Full resistance trend analysis pipeline.

    1. Fetch FAERS counts for drug + comparator (full period, pre, post)
    2. Compute PRR/ROR signals + temporal comparison
    3. Load WHONET resistance rates + ATLAS MIC data
    4. Run LLM interpretation via LangChain
    5. Generate PDF summary
    """
    end = end_year or date.today().year

    # ── FAERS fetch ───────────────────────────────────────────────────────────
    drug_counts_full = fetch_reaction_counts(drug, start_year, end)
    bg_counts_full   = fetch_reaction_counts(comparator, start_year, end)
    drug_total       = fetch_total_reports(drug, start_year, end)
    bg_total         = fetch_total_reports(comparator, start_year, end)
    time.sleep(0.5)

    drug_counts_pre  = fetch_reaction_counts(drug, start_year, cutoff_year - 1)
    bg_counts_pre    = fetch_reaction_counts(comparator, start_year, cutoff_year - 1)
    drug_total_pre   = fetch_total_reports(drug, start_year, cutoff_year - 1)
    bg_total_pre     = fetch_total_reports(comparator, start_year, cutoff_year - 1)
    time.sleep(0.5)

    drug_counts_post = fetch_reaction_counts(drug, cutoff_year, end)
    bg_counts_post   = fetch_reaction_counts(comparator, cutoff_year, end)
    drug_total_post  = fetch_total_reports(drug, cutoff_year, end)
    bg_total_post    = fetch_total_reports(comparator, cutoff_year, end)

    # ── Disproportionality ────────────────────────────────────────────────────
    signals      = compute_signals(drug_counts_full, drug_total, bg_counts_full, bg_total)
    pre_signals  = compute_signals(drug_counts_pre, drug_total_pre, bg_counts_pre, bg_total_pre)
    post_signals = compute_signals(drug_counts_post, drug_total_post, bg_counts_post, bg_total_post)
    temp_compare = temporal_compare(pre_signals, post_signals)

    # ── Yearly trend data (top 5 reactions) ───────────────────────────────────
    top5 = [s.reaction_pt for s in signals[:5]]
    yearly_data = fetch_yearly_counts(drug, top5, start_year, end) if top5 else {}

    # ── AMS category breakdown ────────────────────────────────────────────────
    ams_cats = categorize_reactions(drug_counts_full)

    # ── External resistance data ──────────────────────────────────────────────
    whonet_recs    = load_whonet_data(organism, drug, start_year, end)
    whonet_summary = resistance_trend_summary(whonet_recs)
    atlas_recs     = load_atlas_data(organism, drug, start_year, end)

    # ── LLM interpretation ────────────────────────────────────────────────────
    key_findings   = []
    interpretation = "LLM interpretation unavailable — check Ollama service."

    if run_llm:
        try:
            llm = ChatOllama(model=REASON_MODEL, base_url=OLLAMA_BASE_URL,
                             temperature=0.05, think=False)
            prompt = ChatPromptTemplate.from_messages([
                ("system", _SYSTEM_PROMPT),
                ("human", _INTERPRETATION_TEMPLATE),
            ])
            chain = prompt | llm | StrOutputParser()

            cat_lines = "\n".join(f"{k}: {v}" for k, v in ams_cats.items() if v > 0)
            response = chain.invoke({
                "drug":           drug.capitalize(),
                "comparator":     comparator.capitalize(),
                "period":         f"{start_year}–{end}",
                "drug_total":     drug_total,
                "bg_total":       bg_total,
                "signal_table":   _format_signal_table(signals),
                "pre_period":     f"{start_year}–{cutoff_year - 1}",
                "post_period":    f"{cutoff_year}–{end}",
                "temporal_table": _format_temporal_table(temp_compare),
                "category_table": cat_lines or "No data",
            })
            key_findings, interpretation = _parse_llm_response(response)
        except Exception as e:
            interpretation = f"LLM error: {e}"

    # ── PDF report (full, with charts) ───────────────────────────────────────
    pdf_path = None
    try:
        pdf_path = generate_resistance_full_report(
            drug=drug,
            comparator=comparator,
            period=f"{start_year}–{end}",
            cutoff_year=cutoff_year,
            drug_total=drug_total,
            bg_total=bg_total,
            signals=signals,
            pre_signals=pre_signals,
            post_signals=post_signals,
            temporal_compare=temp_compare,
            ams_categories=ams_cats,
            whonet_summary=whonet_summary,
            atlas_records=atlas_recs,
            key_findings=key_findings,
            interpretation=interpretation,
        )
    except Exception:
        pass

    return ResistanceAnalysis(
        drug=drug,
        comparator=comparator,
        start_year=start_year,
        cutoff_year=cutoff_year,
        end_year=end,
        drug_total=drug_total,
        bg_total=bg_total,
        signals=signals,
        pre_signals=pre_signals,
        post_signals=post_signals,
        temporal_compare=temp_compare,
        yearly_data=yearly_data,
        ams_categories=ams_cats,
        whonet_summary=whonet_summary,
        atlas_records=atlas_recs,
        key_findings=key_findings,
        interpretation=interpretation,
        pdf_path=str(pdf_path) if pdf_path else None,
    )
