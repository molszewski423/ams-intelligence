"""
AMS Intelligence — PDF Report Exporter

Full research reports with embedded matplotlib visualizations using fpdf2.
Color scheme: AMS green (#2E7D32).
"""

from __future__ import annotations
import io
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from fpdf import FPDF

from config import OUTPUT_DIR

# ── Color palette ─────────────────────────────────────────────────────────────
GREEN    = (46, 125, 50)
GREEN_LT = (232, 245, 233)
AMBER    = (230, 119, 0)
AMBER_LT = (255, 243, 224)
RED      = (198, 40, 40)
RED_LT   = (255, 235, 238)
GREY_LT  = (245, 245, 245)
WHITE    = (255, 255, 255)
BLACK    = (33, 33, 33)
GREY_MID = (117, 117, 117)


def _s(text: str) -> str:
    """Replace Unicode chars unsupported by fpdf2 built-in latin-1 fonts."""
    return (
        str(text)
        .replace("—", "-")   # em-dash
        .replace("–", "-")   # en-dash
        .replace("‘", "'")   # left single quote
        .replace("’", "'")   # right single quote
        .replace("“", '"')   # left double quote
        .replace("”", '"')   # right double quote
        .replace("•", "-")   # bullet
        .replace("·", "-")   # middle dot
        .encode("latin-1", errors="replace").decode("latin-1")
    )


def _wrap_text(pdf: "AMSReport", text: str, width: float, size: float) -> list[str]:
    pdf.set_font_size(size)
    words, lines, current = _s(str(text)).split(), [], ""
    for word in words:
        test = (current + " " + word).strip()
        if pdf.get_string_width(test) <= width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [""]


def _embed_figure(pdf: "AMSReport", fig, max_width: float = 190, padding: float = 4) -> None:
    """Save a matplotlib figure to BytesIO and embed it in the PDF at current Y."""
    fig_w, fig_h = fig.get_size_inches()
    img_h = max_width * (fig_h / fig_w)
    if pdf.get_y() + img_h > pdf.h - 22:
        pdf.add_page()
        pdf.set_y(28)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor="white")
    buf.seek(0)
    pdf.image(buf, x=10, y=pdf.get_y(), w=max_width, h=img_h)
    pdf.set_y(pdf.get_y() + img_h + padding)
    plt.close(fig)


class AMSReport(FPDF):
    def __init__(self, title: str = "AMS Intelligence Report"):
        super().__init__(orientation="P", unit="mm", format="A4")
        self._title = _s(title)
        self._divider_pages: set[int] = set()
        self.set_margins(10, 18, 10)
        self.set_auto_page_break(auto=True, margin=20)
        self.t_margin = 28

    def normalize_text(self, text: str) -> str:  # safety net for any stray unicode
        return _s(text)

    def header(self):
        self.set_fill_color(*GREEN)
        self.rect(0, 0, 210, 13, "F")
        self.set_xy(10, 2)
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*WHITE)
        self.cell(130, 5, self._title[:70], ln=False)
        self.set_xy(145, 2)
        self.set_font("Helvetica", "", 7.5)
        self.cell(55, 5, "Michael Olszewski, PharmD, BCPS, BCCCP", align="R", ln=True)
        self.set_xy(145, 7)
        self.set_font("Helvetica", "", 7)
        self.cell(55, 4, f"Page {self.page_no()}", align="R")
        self.set_text_color(*BLACK)

    def footer(self):
        self.set_y(-14)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(*GREY_MID)
        self.set_draw_color(*GREEN)
        self.set_line_width(0.3)
        self.line(10, self.get_y(), 200, self.get_y())
        self.set_xy(10, self.get_y() + 1)
        self.cell(100, 4, "AMS Intelligence · Research summary — not for regulatory submission · Senior reviewer sign-off required")
        self.cell(90, 4, f"Generated {datetime.now():%Y-%m-%d %H:%M}", align="R")
        self.set_text_color(*BLACK)
        self.set_draw_color(0, 0, 0)
        self.set_line_width(0.2)

    def section(self, number: str, title: str):
        self.ln(3)
        self.set_fill_color(*GREEN_LT)
        self.rect(10, self.get_y(), 190, 8, "F")
        self.set_xy(12, self.get_y() + 1.5)
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*GREEN)
        self.cell(186, 5, f"{number}. {title.upper()}")
        self.set_text_color(*BLACK)
        self.ln(10)

    def kpi_row(self, items: list[tuple[str, str, str]]):
        """items = [(label, value, flag)] where flag = normal|warning|alert"""
        colors = {"normal": GREEN_LT, "warning": AMBER_LT, "alert": RED_LT}
        borders = {"normal": GREEN,   "warning": AMBER,    "alert": RED}
        n = len(items)
        w = 190 // n
        y0 = self.get_y()
        for i, (label, value, flag) in enumerate(items):
            x0 = 10 + i * w
            self.set_fill_color(*colors.get(flag, GREEN_LT))
            self.rect(x0, y0, w - 2, 16, "F")
            self.set_draw_color(*borders.get(flag, GREEN))
            self.set_line_width(0.4)
            self.rect(x0, y0, w - 2, 16)
            self.set_xy(x0 + 2, y0 + 2)
            self.set_font("Helvetica", "B", 13)
            self.set_text_color(*borders.get(flag, GREEN))
            self.cell(w - 4, 7, str(value))
            self.set_xy(x0 + 2, y0 + 9)
            self.set_font("Helvetica", "", 7.5)
            self.set_text_color(*BLACK)
            self.cell(w - 4, 5, label)
        self.set_draw_color(0, 0, 0)
        self.set_line_width(0.2)
        self.set_y(y0 + 19)

    def data_table(self, rows: list[dict], cols: list[tuple[str, int, str]]):
        self.set_fill_color(*GREEN)
        self.set_text_color(*WHITE)
        self.set_font("Helvetica", "B", 8)
        self.set_x(10)
        for hdr, w, _ in cols:
            self.cell(w, 6, hdr, fill=True, border=0)
        self.ln()
        self.set_font("Helvetica", "", 7.5)
        for i, row in enumerate(rows):
            self.set_fill_color(*GREY_LT) if i % 2 == 0 else self.set_fill_color(*WHITE)
            self.set_text_color(*BLACK)
            self.set_x(10)
            for key, w, align in cols:
                self.cell(w, 5.5, str(row.get(key, ""))[:32], fill=True, border=0, align=align)
            self.ln()
        self.set_text_color(*BLACK)
        self.ln(2)

    def callout(self, label: str, text: str, color=GREEN):
        self.ln(2)
        self.set_font("Helvetica", "B", 8.5)
        self.set_text_color(*color)
        for ln_text in _wrap_text(self, label, 178, 8.5):
            self.set_x(12); self.cell(178, 5, ln_text, ln=True)
        self.set_font("Helvetica", "", 8.5)
        self.set_text_color(*BLACK)
        for ln_text in _wrap_text(self, text, 178, 8.5):
            self.set_x(12); self.cell(178, 5, ln_text, ln=True)
        self.ln(3)

    def disclaimer(self):
        self.ln(4)
        self.set_fill_color(*AMBER_LT)
        y0 = self.get_y()
        if y0 + 14 > self.h - 20:
            self.add_page()
            y0 = 28
        self.rect(10, y0, 190, 14, "F")
        self.set_xy(12, y0 + 2)
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(*AMBER)
        self.cell(186, 4, "DRAFT — FOR AMS CLINICAL REVIEW ONLY", ln=True)
        self.set_xy(12, y0 + 7)
        self.set_font("Helvetica", "", 7.5)
        self.set_text_color(*BLACK)
        self.multi_cell(186, 4,
            "All signals require validation against patient-level data before formulary or policy action. "
            "FAERS is a spontaneous reporting system subject to reporting bias and confounding. "
            "Senior pharmacist and P&T committee sign-off required before implementation.")


# ── Chart builders ────────────────────────────────────────────────────────────

def _prr_bar_chart(signals: list, drug: str, comparator: str) -> plt.Figure:
    top = [s for s in signals if s.signal][:20]
    if not top:
        fig, ax = plt.subplots(figsize=(10, 2))
        ax.text(0.5, 0.5, "No Evans-positive signals detected.", ha="center", va="center",
                fontsize=12, color="gray")
        ax.axis("off")
        return fig

    labels = [s.reaction_pt[:40] + "…" if len(s.reaction_pt) > 40 else s.reaction_pt for s in top]
    prrs   = [s.prr for s in top]
    lo     = [max(0, s.prr - s.prr_ci_lo) for s in top]
    hi     = [s.prr_ci_hi - s.prr for s in top]
    ns     = [s.drug_cases for s in top]
    colors = ["#c62828" if p >= 5 else "#e65100" if p >= 3 else "#2e7d32" for p in prrs]

    fig, ax = plt.subplots(figsize=(11, max(4, len(labels) * 0.45)))
    ax.barh(range(len(labels)), prrs, xerr=[lo, hi], color=colors,
            alpha=0.85, edgecolor="white", capsize=3, height=0.65)
    ax.axvline(2.0, color="black", linestyle="--", linewidth=1.2)
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, fontsize=8.5)
    ax.set_xlabel("PRR (with 95% CI)", fontsize=10)
    ax.set_title(f"{drug.capitalize()} vs {comparator.capitalize()} — FAERS Disproportionality (Evans Criteria)",
                 fontsize=11, fontweight="bold")
    ax.invert_yaxis()
    for i, (p, n) in enumerate(zip(prrs, ns)):
        ax.text(p + max(hi[i], 0.05) + 0.1, i, f"N={n}", va="center", fontsize=7.5, color="dimgray")
    patches = [
        mpatches.Patch(color="#c62828", alpha=0.85, label="PRR ≥ 5 (strong)"),
        mpatches.Patch(color="#e65100", alpha=0.85, label="PRR 3–5 (moderate)"),
        mpatches.Patch(color="#2e7d32", alpha=0.85, label="PRR 2–3 (threshold)"),
        plt.Line2D([0], [0], color="black", linestyle="--", label="Evans threshold (2.0)"),
    ]
    ax.legend(handles=patches, fontsize=8, loc="lower right")
    ax.grid(axis="x", linestyle="--", alpha=0.3)
    fig.tight_layout()
    return fig


def _temporal_delta_chart(temporal: list, cutoff_year: int) -> plt.Figure:
    top = sorted(temporal, key=lambda r: abs(r["delta"]), reverse=True)[:14]
    if not top:
        fig, ax = plt.subplots(figsize=(10, 2))
        ax.text(0.5, 0.5, "Insufficient data for temporal comparison.", ha="center",
                va="center", fontsize=11, color="gray")
        ax.axis("off")
        return fig

    pts    = [r["reaction_pt"][:38] for r in top]
    deltas = [r["delta"] for r in top]
    colors = ["#c62828" if d > 0 else "#2e7d32" for d in deltas]

    fig, ax = plt.subplots(figsize=(11, max(4, len(pts) * 0.48)))
    ax.barh(pts, deltas, color=colors, alpha=0.8, edgecolor="white", height=0.65)
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_xlabel(f"ΔPRR  (Post-{cutoff_year} minus Pre-{cutoff_year})", fontsize=10)
    ax.set_title(f"PRR Change Around {cutoff_year} Formulary-Change Cutoff", fontsize=11, fontweight="bold")
    ax.invert_yaxis()
    ax.grid(axis="x", linestyle="--", alpha=0.3)
    fig.tight_layout()
    return fig


def _ams_category_chart(ams_categories: dict, drug: str) -> plt.Figure:
    cats = {k: v for k, v in ams_categories.items() if v > 0}
    if not cats:
        fig, ax = plt.subplots(figsize=(8, 2))
        ax.text(0.5, 0.5, "No AMS category data available.", ha="center", va="center",
                fontsize=11, color="gray")
        ax.axis("off")
        return fig

    fig, ax = plt.subplots(figsize=(10, 3.5))
    pal = ["#1b5e20", "#2e7d32", "#388e3c", "#43a047", "#66bb6a", "#a5d6a7"]
    ax.barh(list(cats.keys()), list(cats.values()),
            color=pal[:len(cats)], alpha=0.85, edgecolor="white")
    ax.set_xlabel("FAERS Case Count", fontsize=10)
    ax.set_title(f"AMS-Relevant Adverse Event Categories — {drug.capitalize()}", fontsize=11, fontweight="bold")
    ax.grid(axis="x", linestyle="--", alpha=0.3)
    fig.tight_layout()
    return fig


def _nhsn_trend_chart(nhsn_records: list, anomalies: list, benchmark: float, drug_class: str) -> plt.Figure:
    if not nhsn_records:
        fig, ax = plt.subplots(figsize=(10, 3))
        ax.text(0.5, 0.5, "No NHSN data available.", ha="center", va="center",
                fontsize=11, color="gray")
        ax.axis("off")
        return fig

    labels = [f"{r.year} Q{r.quarter}" if r.quarter else str(r.year) for r in nhsn_records]
    values = [r.dot_per_1000 for r in nhsn_records]
    anom_map = {(a.year, a.quarter): a.anomaly_type for a in anomalies}

    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(range(len(labels)), values, color="#2e7d32", linewidth=2, marker="o", markersize=5)
    ax.axhline(benchmark, color="#c62828", linestyle="--", linewidth=1.5,
               label=f"National benchmark ({benchmark:.0f})")
    for i, r in enumerate(nhsn_records):
        atype = anom_map.get((r.year, r.quarter), "normal")
        if atype == "spike":
            ax.axvspan(i - 0.5, i + 0.5, alpha=0.25, color="#c62828")
        elif atype == "sustained_high":
            ax.axvspan(i - 0.5, i + 0.5, alpha=0.15, color="#e65100")

    step = max(1, len(labels) // 12)
    ax.set_xticks(list(range(len(labels)))[::step])
    ax.set_xticklabels(labels[::step], rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("DOT / 1000 Patient-Days", fontsize=10)
    ax.set_title(f"{drug_class.replace('_',' ').title()} — Utilization Trend",
                 fontsize=11, fontweight="bold")
    patches = [
        mpatches.Patch(color="#c62828", alpha=0.25, label="Spike anomaly"),
        mpatches.Patch(color="#e65100", alpha=0.15, label="Sustained high"),
        plt.Line2D([0], [0], color="#c62828", linestyle="--", label=f"Benchmark ({benchmark:.0f})"),
    ]
    ax.legend(handles=patches, fontsize=8)
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    fig.tight_layout()
    return fig


def _faers_signal_chart(signals: list, drug_class: str) -> plt.Figure | None:
    top = [s for s in signals if s.signal][:15]
    if not top:
        return None
    labels = [s.reaction_pt[:38] + "…" if len(s.reaction_pt) > 38 else s.reaction_pt for s in top]
    prrs   = [s.prr for s in top]
    colors = ["#c62828" if p >= 5 else "#e65100" if p >= 3 else "#2e7d32" for p in prrs]

    fig, ax = plt.subplots(figsize=(11, max(3.5, len(labels) * 0.42)))
    ax.barh(range(len(labels)), prrs, color=colors, alpha=0.85, edgecolor="white", height=0.65)
    ax.axvline(2.0, color="black", linestyle="--", linewidth=1.0)
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, fontsize=8.5)
    ax.set_xlabel("PRR", fontsize=10)
    ax.set_title(f"{drug_class.replace('_',' ').title()} — FAERS Adverse Event Signals",
                 fontsize=11, fontweight="bold")
    ax.invert_yaxis()
    ax.grid(axis="x", linestyle="--", alpha=0.3)
    fig.tight_layout()
    return fig


# ── Public report generators ──────────────────────────────────────────────────

def generate_resistance_full_report(
    drug: str,
    comparator: str,
    period: str,
    cutoff_year: int,
    drug_total: int,
    bg_total: int,
    signals: list,
    pre_signals: list,
    post_signals: list,
    temporal_compare: list,
    ams_categories: dict,
    whonet_summary: dict,
    atlas_records: list,
    key_findings: list[str],
    interpretation: str,
) -> Path:
    ts      = datetime.now().strftime("%Y%m%d_%H%M%S")
    out     = OUTPUT_DIR / f"resistance_{drug}_{ts}.pdf"
    n_sig   = sum(1 for s in signals if s.signal)
    n_str   = sum(1 for s in signals if s.signal_strength == "strong")
    top_prr = f"{signals[0].prr:.2f}" if signals else "—"

    pdf = AMSReport(title=f"Resistance Trend Report — {drug.capitalize()} vs {comparator.capitalize()}")
    pdf.add_page()
    pdf.set_y(28)

    # ── Cover ────────────────────────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(*GREEN)
    pdf.set_x(10); pdf.cell(190, 10, "RESISTANCE TREND ANALYSIS", ln=True)
    pdf.set_font("Helvetica", "", 12)
    pdf.set_text_color(*BLACK)
    pdf.set_x(10); pdf.cell(190, 7, f"{drug.capitalize()}  vs.  {comparator.capitalize()}  ·  {period}", ln=True)
    pdf.set_x(10); pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(*GREY_MID)
    pdf.cell(190, 5, f"Generated {datetime.now():%B %d, %Y}  ·  Cutoff year: {cutoff_year}  ·  AMS Intelligence Platform", ln=True)
    pdf.set_text_color(*BLACK)
    pdf.ln(6)

    # KPI row
    flag = "alert" if n_sig > 5 else ("warning" if n_sig > 0 else "normal")
    pdf.kpi_row([
        ("FAERS reports (drug)",   f"{drug_total:,}",   "normal"),
        ("FAERS reports (comp.)",  f"{bg_total:,}",     "normal"),
        ("Evans signals",          str(n_sig),           flag),
        ("Strong signals",         str(n_str),           "alert" if n_str > 0 else "normal"),
        ("Top PRR",                top_prr,              "alert" if float(top_prr or 0) >= 5 else "warning"),
    ])

    # ── Section 1: Signal table ───────────────────────────────────────────────
    pdf.section("1", "Disproportionality Signals (Evans Criteria: PRR ≥ 2, N ≥ 3, chi² ≥ 4)")
    sig_rows = [{
        "Reaction PT":  s.reaction_pt[:38],
        "N (Drug)":     str(s.drug_cases),
        "PRR":          f"{s.prr:.2f}",
        "95% CI":       f"{s.prr_ci_lo:.2f}–{s.prr_ci_hi:.2f}",
        "ROR":          f"{s.ror:.2f}",
        "chi²":         f"{s.chi2:.1f}",
        "Strength":     s.signal_strength,
    } for s in signals if s.signal][:20]

    if sig_rows:
        pdf.data_table(sig_rows, [
            ("Reaction PT", 70, "L"), ("N (Drug)", 20, "R"),
            ("PRR", 22, "R"), ("95% CI", 38, "C"),
            ("ROR", 20, "R"), ("chi²", 15, "R"), ("Strength", 15, "C"),
        ])
    else:
        pdf.callout("Result", f"No Evans-positive signals detected for {drug} vs {comparator}.", GREEN)

    # ── Section 2: PRR chart ──────────────────────────────────────────────────
    pdf.section("2", "PRR Chart with 95% Confidence Intervals")
    fig_prr = _prr_bar_chart(signals, drug, comparator)
    _embed_figure(pdf, fig_prr)

    # ── Section 3: Temporal comparison ───────────────────────────────────────
    pdf.section("3", f"Temporal Comparison — Pre vs Post {cutoff_year}")

    pre_label  = f"Pre-{cutoff_year}"
    post_label = f"Post-{cutoff_year}"
    temp_rows  = [{
        "Reaction PT":   r["reaction_pt"][:38],
        pre_label:       f"{r['pre_prr']:.2f}",
        post_label:      f"{r['post_prr']:.2f}",
        "Δ PRR":         f"{r['delta']:+.2f}",
        "Direction":     r["direction"],
    } for r in temporal_compare[:12]]

    if temp_rows:
        pdf.data_table(temp_rows, [
            ("Reaction PT", 72, "L"),
            (pre_label, 28, "R"), (post_label, 28, "R"),
            ("Δ PRR", 26, "R"), ("Direction", 36, "C"),
        ])
    else:
        pdf.callout("Note", "Insufficient data for temporal comparison.", GREEN)

    fig_temp = _temporal_delta_chart(temporal_compare, cutoff_year)
    _embed_figure(pdf, fig_temp)

    # ── Section 4: AMS categories ─────────────────────────────────────────────
    pdf.section("4", "AMS Adverse Event Category Breakdown")
    fig_cat = _ams_category_chart(ams_categories, drug)
    _embed_figure(pdf, fig_cat)

    cat_rows = [{"Category": k, "Case Count": str(v)}
                for k, v in ams_categories.items() if v > 0]
    if cat_rows:
        pdf.data_table(cat_rows, [("Category", 120, "L"), ("Case Count", 70, "R")])

    # ── Section 5: WHONET resistance data ─────────────────────────────────────
    if whonet_summary:
        pdf.section("5", "WHONET Resistance Surveillance Summary")
        ws_rows = [
            {"Metric": "Mean % Resistant",      "Value": f"{whonet_summary.get('mean_pct_resistant', 0):.1f}%"},
            {"Metric": "Min % Resistant",        "Value": f"{whonet_summary.get('min_pct_resistant', 0):.1f}%"},
            {"Metric": "Max % Resistant",        "Value": f"{whonet_summary.get('max_pct_resistant', 0):.1f}%"},
            {"Metric": "Annual Trend",           "Value": f"{whonet_summary.get('annual_trend_pct', 0):+.2f}%/year"},
            {"Metric": "Records Analyzed",       "Value": str(whonet_summary.get('n_records', 0))},
        ]
        pdf.data_table(ws_rows, [("Metric", 120, "L"), ("Value", 70, "R")])

    # ── Section 6: ATLAS MIC data ─────────────────────────────────────────────
    if atlas_records:
        pdf.section("6", "ATLAS MIC Susceptibility Trend")
        atlas_rows = [{
            "Year":          str(r.year),
            "MIC50 (µg/mL)": f"{r.mic_50:.3f}" if r.mic_50 is not None else "—",
            "MIC90 (µg/mL)": f"{r.mic_90:.3f}" if r.mic_90 is not None else "—",
            "% Susceptible": f"{r.pct_susceptible * 100:.1f}%",
            "N Isolates":    str(r.n_isolates),
            "Source":        r.source,
        } for r in atlas_records]
        pdf.data_table(atlas_rows, [
            ("Year", 22, "C"), ("MIC50 (µg/mL)", 36, "R"),
            ("MIC90 (µg/mL)", 36, "R"), ("% Susceptible", 38, "R"),
            ("N Isolates", 30, "R"), ("Source", 28, "C"),
        ])

        # ATLAS trend chart
        years = [r.year for r in atlas_records]
        pct_s = [r.pct_susceptible * 100 for r in atlas_records]
        mic90 = [r.mic_90 for r in atlas_records if r.mic_90 is not None]
        mic_y = [r.year for r in atlas_records if r.mic_90 is not None]

        fig_atl, axes = plt.subplots(1, 2, figsize=(11, 3.5))
        axes[0].plot(years, pct_s, color="#2e7d32", marker="o", linewidth=2)
        axes[0].set_ylim(0, 105)
        axes[0].set_ylabel("% Susceptible", fontsize=9)
        axes[0].set_title(f"Susceptibility — {drug.capitalize()}", fontsize=10)
        axes[0].grid(axis="y", linestyle="--", alpha=0.4)

        if mic90 and mic_y:
            axes[1].plot(mic_y, mic90, color="#e65100", marker="s", linewidth=2)
            axes[1].set_ylabel("MIC90 (µg/mL)", fontsize=9)
            axes[1].set_title("MIC90 Trend (MIC Creep)", fontsize=10)
            axes[1].grid(axis="y", linestyle="--", alpha=0.4)
        else:
            axes[1].axis("off")
        fig_atl.tight_layout()
        _embed_figure(pdf, fig_atl)

    # ── Section 7: Key findings + interpretation ──────────────────────────────
    sec_n = "7" if whonet_summary else ("6" if not atlas_records else "7")
    pdf.section(sec_n, "Key Findings and Clinical Interpretation")

    if key_findings:
        pdf.set_font("Helvetica", "B", 9.5)
        pdf.set_x(10); pdf.cell(190, 6, "Key Findings:", ln=True)
        pdf.set_font("Helvetica", "", 8.5)
        for i, finding in enumerate(key_findings, 1):
            pdf.set_x(12); pdf.cell(5, 5.5, f"{i}.")
            for j, line in enumerate(_wrap_text(pdf, finding, 173, 8.5)):
                pdf.set_x(17); pdf.cell(173, 5.5, line, ln=True)
        pdf.ln(3)

    if interpretation:
        pdf.set_font("Helvetica", "B", 9.5)
        pdf.set_x(10); pdf.cell(190, 6, "Clinical Interpretation:", ln=True)
        pdf.set_font("Helvetica", "", 8.5)
        for line in _wrap_text(pdf, interpretation, 178, 8.5):
            pdf.set_x(12); pdf.cell(178, 5, line, ln=True)

    pdf.disclaimer()
    pdf.output(str(out))
    return out


def generate_utilization_full_report(
    drug_class: str,
    period: str,
    nhsn_records: list,
    benchmark: float,
    anomalies: list,
    faers_signals: list,
    ams_categories: dict,
    correlation_flags: list[str],
    anomaly_score: float,
    overall_flag: str,
    llm_summary: str,
    data_sources: list[str],
) -> Path:
    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    out  = OUTPUT_DIR / f"utilization_{drug_class}_{ts}.pdf"
    n_an = sum(1 for a in anomalies if a.anomaly_type != "normal")
    n_fs = sum(1 for s in faers_signals if s.signal)

    flag_str = {"critical": "CRITICAL", "watch": "WATCH", "routine": "ROUTINE"}.get(overall_flag, overall_flag.upper())
    flag_color = {"critical": "alert", "watch": "warning", "routine": "normal"}.get(overall_flag, "normal")

    pdf = AMSReport(title=f"Utilization Signal Report — {drug_class.replace('_', ' ').title()}")
    pdf.add_page()
    pdf.set_y(28)

    # ── Cover ────────────────────────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(*GREEN)
    pdf.set_x(10); pdf.cell(190, 10, "ANTIBIOTIC UTILIZATION SIGNAL REPORT", ln=True)
    pdf.set_font("Helvetica", "", 12)
    pdf.set_text_color(*BLACK)
    pdf.set_x(10); pdf.cell(190, 7, f"{drug_class.replace('_', ' ').title()}  ·  {period}", ln=True)
    pdf.set_x(10); pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(*GREY_MID)
    pdf.cell(190, 5, f"Generated {datetime.now():%B %d, %Y}  ·  Sources: {', '.join(data_sources)}", ln=True)
    pdf.set_text_color(*BLACK)
    pdf.ln(5)

    pdf.kpi_row([
        ("Periods analyzed",      str(len(nhsn_records)),     "normal"),
        ("Anomalous periods",     str(n_an),                   "warning" if n_an > 0 else "normal"),
        ("FAERS signals",         str(n_fs),                   "alert" if n_fs > 3 else "warning" if n_fs > 0 else "normal"),
        ("Anomaly score",         f"{anomaly_score:.2f}",      flag_color),
        ("Overall flag",          flag_str,                    flag_color),
    ])

    # ── Section 1: Utilization trend chart ───────────────────────────────────
    pdf.section("1", "NHSN Utilization Trend — Days of Therapy per 1,000 Patient-Days")
    fig_nhsn = _nhsn_trend_chart(nhsn_records, anomalies, benchmark, drug_class)
    _embed_figure(pdf, fig_nhsn)

    # ── Section 2: Anomaly table ──────────────────────────────────────────────
    pdf.section("2", "Utilization Anomaly Detail")
    an_rows = [{
        "Year":        str(a.year),
        "Quarter":     f"Q{a.quarter}" if a.quarter else "—",
        "DOT/1000 PD": f"{a.dot_per_1000:.1f}",
        "Benchmark":   f"{a.benchmark:.1f}",
        "Deviation":   f"{a.deviation_pct:+.1f}%",
        "Type":        a.anomaly_type.replace("_", " ").title(),
    } for a in anomalies if a.anomaly_type != "normal"]

    if an_rows:
        pdf.data_table(an_rows, [
            ("Year", 22, "C"), ("Quarter", 22, "C"),
            ("DOT/1000 PD", 36, "R"), ("Benchmark", 36, "R"),
            ("Deviation", 36, "R"), ("Type", 38, "C"),
        ])
    else:
        pdf.callout("Result", "No utilization anomalies detected — within expected range.", GREEN)

    # ── Section 3: FAERS signals ──────────────────────────────────────────────
    pdf.section("3", "Cross-Referenced FAERS Adverse Event Signals")
    fig_faers = _faers_signal_chart(faers_signals, drug_class)
    if fig_faers:
        _embed_figure(pdf, fig_faers)

    fs_rows = [{
        "Reaction PT":  s.reaction_pt[:40],
        "Drug N":       str(s.drug_cases),
        "PRR":          f"{s.prr:.2f}",
        "ROR":          f"{s.ror:.2f}",
        "chi²":         f"{s.chi2:.1f}",
        "Strength":     s.signal_strength,
    } for s in faers_signals if s.signal][:15]

    if fs_rows:
        pdf.data_table(fs_rows, [
            ("Reaction PT", 70, "L"), ("Drug N", 22, "R"),
            ("PRR", 22, "R"), ("ROR", 22, "R"),
            ("chi²", 18, "R"), ("Strength", 36, "C"),
        ])
    else:
        pdf.callout("Result", "No Evans-positive FAERS signals detected for this drug class.", GREEN)

    # ── Section 4: AMS category breakdown ────────────────────────────────────
    pdf.section("4", "AMS Adverse Event Category Breakdown")
    fig_cat = _ams_category_chart(ams_categories, drug_class.replace("_", " ").title())
    _embed_figure(pdf, fig_cat)

    # ── Section 5: Correlation flags ──────────────────────────────────────────
    pdf.section("5", "Utilization–Signal Correlation Flags")
    for flag in correlation_flags:
        pdf.callout("▶", flag, AMBER if "critical" in flag.lower() or "immediate" in flag.lower() else GREEN)

    # ── Section 6: AMS committee summary ─────────────────────────────────────
    pdf.section("6", "AMS Committee Plain-Language Summary")
    if llm_summary:
        pdf.set_font("Helvetica", "", 8.5)
        for line in _wrap_text(pdf, llm_summary, 178, 8.5):
            pdf.set_x(12); pdf.cell(178, 5.5, line, ln=True)
    else:
        pdf.callout("Note", "LLM summary not available.", GREY_MID)

    pdf.disclaimer()
    pdf.output(str(out))
    return out
