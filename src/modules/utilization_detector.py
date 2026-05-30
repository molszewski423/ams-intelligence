"""
AMS Intelligence — Module 2: Antibiotic Utilization Signal Detector

Cross-references antimicrobial utilization patterns (DOT/1000 patient-days
from NHSN) against FAERS adverse outcome signals to:
  - Identify utilization anomalies (spikes, sustained elevation)
  - Flag correlations between high utilization and resistance/outcome signals
  - Generate plain-language clinical summaries for the AMS team

Drug classes supported: fluoroquinolones, carbapenems, vancomycin,
cephalosporins_1g, cephalosporins_3g, piperacillin_tazo, azithromycin,
metronidazole, trimethoprim_sulfa
"""

from __future__ import annotations
import statistics
from dataclasses import dataclass, field
from datetime import datetime, date

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from config import OLLAMA_BASE_URL, REASON_MODEL
from data_sources.nhsn_client import load_nhsn_data, get_national_benchmark, NHSNRecord
from data_sources.faers_client import fetch_reaction_counts, fetch_total_reports
from shared.disproportionality import compute_signals, SignalResult

# Map drug class names → FAERS search terms
DRUG_CLASS_FAERS_TERMS: dict[str, list[str]] = {
    "fluoroquinolones":   ["ciprofloxacin", "levofloxacin", "moxifloxacin"],
    "carbapenems":        ["meropenem", "imipenem", "ertapenem", "doripenem"],
    "vancomycin":         ["vancomycin"],
    "cephalosporins_1g":  ["cefazolin", "cephalexin", "cefadroxil"],
    "cephalosporins_3g":  ["ceftriaxone", "cefdinir", "cefpodoxime", "ceftazidime"],
    "piperacillin_tazo":  ["piperacillin", "tazobactam"],
    "azithromycin":       ["azithromycin", "azithromicin"],
    "metronidazole":      ["metronidazole"],
    "trimethoprim_sulfa": ["trimethoprim", "sulfamethoxazole"],
}

# Resistance-relevant outcomes to flag
RESISTANCE_OUTCOMES = [
    "therapeutic failure", "drug ineffective", "drug resistance",
    "treatment failure", "clinical failure", "infection",
    "clostridium difficile infection",
]

_SUMMARY_SYSTEM = """\
You are a clinical pharmacist leading an antimicrobial stewardship program.
You are reviewing cross-referenced utilization and adverse outcome data for
a drug class. Provide a concise, actionable AMS summary:
- Identify whether utilization is above/below national benchmarks
- Correlate utilization spikes with adverse signal emergence
- Recommend specific AMS interventions (restriction, review criteria, de-escalation targets)
- Flag any C. difficile or resistance-driven concerns
Keep the summary to 4-6 sentences, plain clinical language suitable for a P&T committee.
"""


@dataclass
class UtilizationAnomaly:
    year: int
    quarter: int
    dot_per_1000: float
    benchmark: float
    deviation_pct: float    # % above/below benchmark
    anomaly_type: str       # "spike" / "sustained_high" / "low" / "normal"


@dataclass
class UtilizationSignalReport:
    drug_class: str
    start_year: int
    end_year: int
    nhsn_records: list[NHSNRecord]
    benchmark: float
    anomalies: list[UtilizationAnomaly]
    faers_signals: list[SignalResult]
    ams_category_counts: dict[str, int]
    correlation_flags: list[str]
    anomaly_score: float        # 0.0–1.0
    overall_flag: str           # "critical" / "watch" / "routine"
    llm_summary: str
    data_sources: list[str]
    pdf_path: str | None = None
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())


def _detect_anomalies(records: list[NHSNRecord], benchmark: float) -> list[UtilizationAnomaly]:
    if not records:
        return []
    values = [r.dot_per_1000 for r in records]
    mean   = statistics.mean(values)
    stdev  = statistics.stdev(values) if len(values) > 1 else 0.0
    anomalies = []
    for r in records:
        dev_pct = (r.dot_per_1000 - benchmark) / benchmark * 100
        if r.dot_per_1000 > mean + 2 * stdev:
            atype = "spike"
        elif dev_pct > 25:
            atype = "sustained_high"
        elif dev_pct < -25:
            atype = "low"
        else:
            atype = "normal"
        anomalies.append(UtilizationAnomaly(
            year=r.year, quarter=r.quarter,
            dot_per_1000=r.dot_per_1000, benchmark=benchmark,
            deviation_pct=round(dev_pct, 1), anomaly_type=atype,
        ))
    return anomalies


def _anomaly_score(anomalies: list[UtilizationAnomaly]) -> float:
    """Normalised 0–1 score: higher = more concerning."""
    if not anomalies:
        return 0.0
    n_bad = sum(1 for a in anomalies if a.anomaly_type in ("spike", "sustained_high"))
    return min(1.0, round(n_bad / len(anomalies) * 1.5, 2))


def _correlation_flags(anomalies: list[UtilizationAnomaly], signals: list[SignalResult]) -> list[str]:
    flags = []
    spike_years = {a.year for a in anomalies if a.anomaly_type == "spike"}
    if spike_years:
        flags.append(f"Utilization spikes detected in {sorted(spike_years)} — review formulary restrictions")
    cdiff = next((s for s in signals if "clostridium" in s.reaction_pt or "difficile" in s.reaction_pt), None)
    if cdiff and cdiff.signal:
        flags.append(f"C. difficile signal active (PRR {cdiff.prr:.1f}) — audit concurrent antibiotic use")
    resist = next((s for s in signals if "resist" in s.reaction_pt or "failure" in s.reaction_pt), None)
    if resist and resist.signal:
        flags.append(f"Treatment failure signal (PRR {resist.prr:.1f}) — de-escalation protocol review recommended")
    high_util = [a for a in anomalies if a.deviation_pct > 40]
    if high_util:
        flags.append(f"{len(high_util)} periods >40% above national benchmark — prospective audit indicated")
    return flags or ["No critical correlation flags identified — continue routine monitoring"]


def detect_utilization_signals(
    drug_class: str = "fluoroquinolones",
    start_year: int = 2018,
    end_year: int | None = None,
    run_llm: bool = True,
) -> UtilizationSignalReport:
    """
    Full utilization signal detection pipeline:
    1. Load NHSN DOT data → detect anomalies vs benchmark
    2. Fetch FAERS signals for drug class agents
    3. Cross-reference and flag correlations
    4. LLM plain-language summary
    """
    end       = end_year or date.today().year
    benchmark = get_national_benchmark(drug_class)

    # ── NHSN utilization ─────────────────────────────────────────────────────
    nhsn_records = load_nhsn_data(drug_class, start_year, end)
    anomalies    = _detect_anomalies(nhsn_records, benchmark)
    a_score      = _anomaly_score(anomalies)

    # ── FAERS signals for drug class ──────────────────────────────────────────
    faers_terms = DRUG_CLASS_FAERS_TERMS.get(drug_class, [drug_class])
    drug_counts  = {}
    bg_counts    = {}

    for term in faers_terms[:2]:   # limit API calls — use top 2 agents
        drug_counts.update(fetch_reaction_counts(term, start_year, end))

    # Background: carbapenems as universal comparator
    for bg_term in ["meropenem", "piperacillin"]:
        bg_counts.update(fetch_reaction_counts(bg_term, start_year, end))

    from collections import Counter
    drug_c = Counter(drug_counts)
    bg_c   = Counter(bg_counts)

    drug_total = max(1, fetch_total_reports(faers_terms[0], start_year, end))
    bg_total   = max(1, fetch_total_reports("meropenem", start_year, end))

    signals    = compute_signals(drug_c, drug_total, bg_c, bg_total, min_drug_cases=2)

    # AMS category breakdown
    from data_sources.faers_client import categorize_reactions
    ams_cats = categorize_reactions(drug_c)

    # Correlation flags
    cor_flags = _correlation_flags(anomalies, signals)

    # Overall risk flag
    n_signals = sum(1 for s in signals if s.signal)
    if a_score > 0.5 or n_signals > 8:
        overall = "critical"
    elif a_score > 0.25 or n_signals > 3:
        overall = "watch"
    else:
        overall = "routine"

    # ── LLM summary ──────────────────────────────────────────────────────────
    llm_summary = "LLM summary unavailable — check Ollama service."
    if run_llm:
        try:
            llm = ChatOllama(model=REASON_MODEL, base_url=OLLAMA_BASE_URL,
                             temperature=0.05, think=False)
            prompt = ChatPromptTemplate.from_messages([
                ("system", _SUMMARY_SYSTEM),
                ("human", (
                    "Drug class: {drug_class}\n"
                    "Analysis period: {period}\n"
                    "National DOT/1000 patient-days benchmark: {benchmark}\n"
                    "Observed values (mean): {obs_mean:.1f}\n"
                    "Anomalies: {n_anomalies} periods flagged ({anomaly_types})\n"
                    "FAERS Evans-positive signals: {n_signals}\n"
                    "Top FAERS signals: {top_signals}\n"
                    "Correlation flags:\n{flags}\n\n"
                    "Provide AMS plain-language summary."
                )),
            ])
            chain = prompt | llm | StrOutputParser()

            obs_vals = [r.dot_per_1000 for r in nhsn_records]
            top_sigs = "; ".join(
                f"{s.reaction_pt} (PRR {s.prr:.1f})"
                for s in signals[:5] if s.signal
            ) or "None"
            atypes = ", ".join(set(a.anomaly_type for a in anomalies if a.anomaly_type != "normal"))

            llm_summary = chain.invoke({
                "drug_class":    drug_class.replace("_", " ").title(),
                "period":        f"{start_year}–{end}",
                "benchmark":     benchmark,
                "obs_mean":      statistics.mean(obs_vals) if obs_vals else 0.0,
                "n_anomalies":   sum(1 for a in anomalies if a.anomaly_type != "normal"),
                "anomaly_types": atypes or "none",
                "n_signals":     n_signals,
                "top_signals":   top_sigs,
                "flags":         "\n".join(f"• {f}" for f in cor_flags),
            })
        except Exception as e:
            llm_summary = f"LLM error: {e}"

    data_sources = ["NHSN (demo)" if not nhsn_records or nhsn_records[0].source == "demo" else "NHSN (file)",
                    "FAERS (live API)"]

    # ── PDF report (full, with charts) ───────────────────────────────────────
    from shared.pdf_exporter import generate_utilization_full_report
    pdf_path = None
    try:
        pdf_path = generate_utilization_full_report(
            drug_class=drug_class,
            period=f"{start_year}–{end}",
            nhsn_records=nhsn_records,
            benchmark=benchmark,
            anomalies=anomalies,
            faers_signals=signals,
            ams_categories=ams_cats,
            correlation_flags=cor_flags,
            anomaly_score=a_score,
            overall_flag=overall,
            llm_summary=llm_summary,
            data_sources=data_sources,
        )
    except Exception:
        pass

    return UtilizationSignalReport(
        drug_class=drug_class,
        start_year=start_year,
        end_year=end,
        nhsn_records=nhsn_records,
        benchmark=benchmark,
        anomalies=anomalies,
        faers_signals=signals,
        ams_category_counts=ams_cats,
        correlation_flags=cor_flags,
        anomaly_score=a_score,
        overall_flag=overall,
        llm_summary=llm_summary,
        data_sources=data_sources,
        pdf_path=str(pdf_path) if pdf_path else None,
    )
