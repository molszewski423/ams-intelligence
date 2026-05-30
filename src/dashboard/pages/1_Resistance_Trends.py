"""Module 1 — Resistance Trend Analyzer"""

import sys
from pathlib import Path
import streamlit as st
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from auth import require_auth, auth_sidebar
from config import REASON_MODEL

st.set_page_config(page_title="Resistance Trends", page_icon="📊", layout="wide")
require_auth()
with st.sidebar:
    auth_sidebar()

st.title("📊 Resistance Trend Analyzer")
st.caption(
    f"FAERS PRR/ROR · Temporal pre/post analysis · WHONET/ATLAS integration · `{REASON_MODEL}`"
)
st.error(
    "**DRAFT OUTPUT ONLY** — All signals require validation against patient-level data. "
    "Senior pharmacist sign-off required before any formulary or policy action."
)

# ── Input panel ───────────────────────────────────────────────────────────────

with st.expander("⚙️ Analysis Parameters", expanded=True):
    c1, c2, c3 = st.columns(3)
    with c1:
        drug       = st.text_input("Primary drug", value="cefazolin")
        comparator = st.text_input("Comparator", value="cefpodoxime")
    with c2:
        start_year  = st.number_input("Start year", 2004, 2025, value=2015, step=1)
        cutoff_year = st.number_input("Formulary change cutoff year", 2005, 2025, value=2020, step=1)
    with c3:
        organism  = st.text_input("Organism (WHONET/ATLAS)", value="Staphylococcus aureus")
        run_llm   = st.checkbox("Run LLM interpretation", value=True)

    run_col, _ = st.columns([1, 3])
    with run_col:
        run = st.button("▶ Run Analysis", type="primary", use_container_width=True)

# ── Run ───────────────────────────────────────────────────────────────────────

if run:
    from modules.resistance_analyzer import run_resistance_analysis

    with st.spinner(f"Fetching FAERS data for {drug} vs {comparator} ({start_year}–present)…"):
        try:
            result = run_resistance_analysis(
                drug=drug,
                comparator=comparator,
                cutoff_year=int(cutoff_year),
                start_year=int(start_year),
                organism=organism,
                run_llm=run_llm,
            )
        except Exception as e:
            st.error(f"Analysis failed: {e}")
            st.stop()

    # ── KPIs ─────────────────────────────────────────────────────────────────
    n_sig   = sum(1 for s in result.signals if s.signal)
    n_strong = sum(1 for s in result.signals if s.signal_strength == "strong")
    top_prr = result.signals[0].prr if result.signals else 0.0

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Drug reports (FAERS)", f"{result.drug_total:,}")
    k2.metric("Comparator reports",   f"{result.bg_total:,}")
    k3.metric("Evans signals",        str(n_sig),  delta=f"{n_strong} strong")
    k4.metric("Top PRR",              f"{top_prr:.2f}")

    st.markdown("---")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 Signal Table", "📊 PRR Chart", "🕐 Temporal", "🧫 Resistance Data", "🧠 Interpretation"
    ])

    # ── Tab 1: Signal Table ───────────────────────────────────────────────────
    with tab1:
        sig_data = [s for s in result.signals if s.signal]
        if not sig_data:
            st.success(f"No Evans-positive signals for {drug} vs {comparator}.")
        else:
            df = pd.DataFrame([{
                "Reaction PT":        s.reaction_pt,
                "Drug N":             s.drug_cases,
                "PRR":                s.prr,
                "PRR 95% CI":         f"{s.prr_ci_lo:.2f} – {s.prr_ci_hi:.2f}",
                "ROR":                s.ror,
                "chi²":               s.chi2,
                "Strength":           s.signal_strength,
                "Corrected":          "✓" if s.continuity_corrected else "",
            } for s in sig_data])

            def _color_strength(val):
                return {
                    "strong":    "background-color: #ffcccc",
                    "moderate":  "background-color: #ffe4b5",
                    "threshold": "background-color: #e8f4fd",
                }.get(val, "")

            st.dataframe(
                df.style.map(_color_strength, subset=["Strength"]),
                use_container_width=True,
                height=min(600, 50 + len(df) * 38),
            )
            csv = df.to_csv(index=False)
            st.download_button(
                "Download signals CSV", csv,
                file_name=f"{drug}_vs_{comparator}_signals.csv", mime="text/csv",
            )

    # ── Tab 2: PRR chart ──────────────────────────────────────────────────────
    with tab2:
        top_20 = [s for s in result.signals if s.signal][:20]
        if not top_20:
            st.info("No signals to chart.")
        else:
            labels = [pt[:40] + "…" if len(pt) > 40 else pt for pt in [s.reaction_pt for s in top_20]]
            prrs   = [s.prr for s in top_20]
            lo     = [s.prr - s.prr_ci_lo for s in top_20]
            hi     = [s.prr_ci_hi - s.prr for s in top_20]
            ns     = [s.drug_cases for s in top_20]
            colors = ["#c62828" if p >= 5 else "#e65100" if p >= 3 else "#2e7d32" for p in prrs]

            fig, ax = plt.subplots(figsize=(12, max(5, len(labels) * 0.45)))
            ax.barh(range(len(labels)), prrs, xerr=[lo, hi], color=colors,
                    alpha=0.85, edgecolor="white", capsize=3)
            ax.axvline(x=2.0, color="black", linestyle="--", linewidth=1.2, label="Evans PRR ≥ 2.0")
            ax.set_yticks(range(len(labels)))
            ax.set_yticklabels(labels, fontsize=8.5)
            ax.set_xlabel("PRR (with 95% CI)", fontsize=10)
            ax.set_title(
                f"{drug.capitalize()} vs {comparator.capitalize()} — FAERS Disproportionality\n"
                f"Period: {start_year}–present · Evans criteria · n={sum(ns):,} drug reports",
                fontsize=11, fontweight="bold",
            )
            ax.invert_yaxis()
            for i, (p, n) in enumerate(zip(prrs, ns)):
                ax.text(p + 0.1, i, f"N={n}", va="center", fontsize=7.5, color="dimgray")
            patches = [
                mpatches.Patch(color="#c62828", alpha=0.85, label="PRR ≥ 5 (strong)"),
                mpatches.Patch(color="#e65100", alpha=0.85, label="PRR 3–5 (moderate)"),
                mpatches.Patch(color="#2e7d32", alpha=0.85, label="PRR 2–3 (threshold)"),
            ]
            ax.legend(handles=patches + [plt.Line2D([0], [0], color="black", linestyle="--",
                                                     label="Evans threshold")], fontsize=8, loc="lower right")
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()

    # ── Tab 3: Temporal comparison ────────────────────────────────────────────
    with tab3:
        st.subheader(f"Pre-{cutoff_year} vs Post-{cutoff_year} PRR Changes")
        tc = result.temporal_compare[:20]
        if not tc:
            st.info("Insufficient data for temporal comparison.")
        else:
            tc_df = pd.DataFrame(tc)
            tc_df = tc_df.rename(columns={
                "reaction_pt":  "Reaction PT",
                "pre_prr":      f"Pre-{cutoff_year} PRR",
                "post_prr":     f"Post-{cutoff_year} PRR",
                "delta":        "Δ PRR",
                "direction":    "Direction",
                "pre_signal":   f"Signal Pre",
                "post_signal":  f"Signal Post",
            })

            def _dir_color(val):
                if "↑" in str(val):    return "color: #c62828"
                if "↓" in str(val):    return "color: #2e7d32"
                return ""

            st.dataframe(
                tc_df.style.map(_dir_color, subset=["Direction"]),
                use_container_width=True, height=min(500, 50 + len(tc_df) * 36),
            )

            # Delta bar chart
            top_delta = sorted(tc, key=lambda r: abs(r["delta"]), reverse=True)[:12]
            if top_delta:
                fig2, ax2 = plt.subplots(figsize=(10, max(4, len(top_delta) * 0.5)))
                pts    = [r["reaction_pt"][:35] for r in top_delta]
                deltas = [r["delta"] for r in top_delta]
                bar_cols = ["#c62828" if d > 0 else "#2e7d32" for d in deltas]
                ax2.barh(pts, deltas, color=bar_cols, alpha=0.8, edgecolor="white")
                ax2.axvline(0, color="black", linewidth=0.8)
                ax2.set_xlabel("ΔPRR (Post − Pre)", fontsize=10)
                ax2.set_title(f"PRR Change Pre/Post {cutoff_year} — {drug.capitalize()}", fontweight="bold")
                ax2.invert_yaxis()
                plt.tight_layout()
                st.pyplot(fig2)
                plt.close()

    # ── Tab 4: Resistance data ────────────────────────────────────────────────
    with tab4:
        c_w, c_a = st.columns(2)

        with c_w:
            st.subheader("WHONET Resistance Trends")
            ws = result.whonet_summary
            if ws:
                st.metric("Mean % Resistant",  f"{ws.get('mean_pct_resistant', 0):.1f}%")
                st.metric("Annual trend",       f"{ws.get('annual_trend_pct', 0):+.2f}%/year")
                st.metric("N records",          str(ws.get("n_records", 0)))
                src = result.whonet_summary.get("source", "demo")
            else:
                st.info("No WHONET data available.")

            st.caption("Source: WHONET (demo data — place CSV files in data/whonet/ for real data)")

        with c_a:
            st.subheader("ATLAS MIC Trend")
            if result.atlas_records:
                atlas_df = pd.DataFrame([{
                    "Year":       r.year,
                    "MIC50":      r.mic_50,
                    "MIC90":      r.mic_90,
                    "% Susceptible": round(r.pct_susceptible * 100, 1),
                    "N Isolates": r.n_isolates,
                    "Source":     r.source,
                } for r in result.atlas_records])
                st.dataframe(atlas_df, use_container_width=True, height=250)

                fig3, ax3 = plt.subplots(figsize=(8, 3.5))
                ax3.plot(atlas_df["Year"], atlas_df["% Susceptible"],
                         color="#2e7d32", marker="o", linewidth=2)
                ax3.set_ylabel("% Susceptible", fontsize=9)
                ax3.set_title(f"ATLAS Susceptibility — {drug.capitalize()} / {organism}", fontsize=10)
                ax3.set_ylim(0, 105)
                ax3.grid(axis="y", linestyle="--", alpha=0.4)
                plt.tight_layout()
                st.pyplot(fig3)
                plt.close()
            else:
                st.info("No ATLAS data available.")

        # AMS category breakdown
        st.subheader("FAERS AMS Category Breakdown")
        cat_data = {k: v for k, v in result.ams_categories.items() if v > 0}
        if cat_data:
            cat_df = pd.DataFrame(list(cat_data.items()), columns=["Category", "Cases"])
            fig4, ax4 = plt.subplots(figsize=(8, 3))
            ax4.barh(cat_df["Category"], cat_df["Cases"], color="#2e7d32", alpha=0.8)
            ax4.set_xlabel("FAERS Case Count")
            ax4.set_title(f"AMS-Relevant Adverse Event Categories — {drug.capitalize()}")
            plt.tight_layout()
            st.pyplot(fig4)
            plt.close()

    # ── Tab 5: Interpretation ─────────────────────────────────────────────────
    with tab5:
        if result.key_findings:
            st.subheader("Key Findings")
            for i, f in enumerate(result.key_findings, 1):
                st.markdown(f"**{i}.** {f}")
            st.markdown("---")

        st.subheader("Clinical Interpretation")
        st.markdown(result.interpretation)

        if result.pdf_path:
            st.markdown("---")
            st.success(f"PDF report generated: `{Path(result.pdf_path).name}`")
            try:
                pdf_bytes = Path(result.pdf_path).read_bytes()
                st.download_button(
                    "📄 Download One-Page Summary PDF",
                    pdf_bytes,
                    file_name=Path(result.pdf_path).name,
                    mime="application/pdf",
                    use_container_width=True,
                )
            except Exception:
                pass

# ── Static reference ─────────────────────────────────────────────────────────
st.divider()
with st.expander("Cefazolin vs Cefpodoxime — Clinical Context"):
    st.markdown("""
**Cefazolin** (IV, 1st-gen cephalosporin) is the preferred agent for MSSA infections and
surgical prophylaxis per most AMS guidelines. Its formulary position is well-established.

**Cefpodoxime** (oral, 3rd-gen cephalosporin) is sometimes used as an oral step-down or
outpatient comparator. Broader spectrum activity may carry greater C. difficile risk and
resistance selection pressure vs. cefazolin.

**Signal interpretation guidance:**
- PRR ≥ 5 for treatment failure: may indicate true clinical failure or confounding by indication
- C. difficile PRR elevation: mechanistically plausible — should drive restriction policy review
- Allergy signals: differentiate anaphylaxis (true allergy) vs. maculopapular rash (often tolerated)
- Resistance signals in FAERS are underreported — pair with WHONET/ATLAS microbiological data
    """)
