"""Module 2 — Antibiotic Utilization Signal Detector"""

import sys
from pathlib import Path
import streamlit as st
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from auth import require_auth, auth_sidebar
from config import REASON_MODEL

st.set_page_config(page_title="Utilization Signals", page_icon="📈", layout="wide")
require_auth()
with st.sidebar:
    auth_sidebar()

st.title("📈 Antibiotic Utilization Signal Detector")
st.caption(
    f"NHSN DOT trends · FAERS cross-reference · Anomaly detection · `{REASON_MODEL}`"
)

DRUG_CLASSES = {
    "Fluoroquinolones":       "fluoroquinolones",
    "Carbapenems":            "carbapenems",
    "Vancomycin":             "vancomycin",
    "Cephalosporins (1st gen)": "cephalosporins_1g",
    "Cephalosporins (3rd gen)": "cephalosporins_3g",
    "Piperacillin/Tazobactam": "piperacillin_tazo",
    "Azithromycin":           "azithromycin",
    "Metronidazole":          "metronidazole",
    "Trimethoprim/Sulfa":     "trimethoprim_sulfa",
}

# ── Input panel ───────────────────────────────────────────────────────────────

with st.expander("⚙️ Analysis Parameters", expanded=True):
    c1, c2, c3 = st.columns(3)
    with c1:
        selected_label = st.selectbox("Drug class", list(DRUG_CLASSES.keys()))
        drug_class     = DRUG_CLASSES[selected_label]
    with c2:
        start_year = st.number_input("Start year", 2015, 2024, value=2018, step=1)
    with c3:
        run_llm = st.checkbox("Run LLM summary", value=True)

    run_col, _ = st.columns([1, 3])
    with run_col:
        run = st.button("▶ Run Detection", type="primary", use_container_width=True)

# ── Run ───────────────────────────────────────────────────────────────────────

if run:
    from modules.utilization_detector import detect_utilization_signals

    with st.spinner(f"Analyzing {selected_label} utilization + FAERS signals ({start_year}–present)…"):
        try:
            report = detect_utilization_signals(
                drug_class=drug_class,
                start_year=int(start_year),
                run_llm=run_llm,
            )
        except Exception as e:
            st.error(f"Detection failed: {e}")
            st.stop()

    # ── KPIs ─────────────────────────────────────────────────────────────────
    n_anomalies = sum(1 for a in report.anomalies if a.anomaly_type != "normal")
    n_signals   = sum(1 for s in report.faers_signals if s.signal)
    flag_color  = {"critical": "error", "watch": "warning", "routine": "success"}

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Utilization periods", len(report.nhsn_records))
    k2.metric("Anomalous periods",   n_anomalies,
              delta=f"benchmark: {report.benchmark:.0f} DOT/1000")
    k3.metric("FAERS signals",       n_signals)
    k4.metric("Anomaly score",       f"{report.anomaly_score:.2f}")

    flag_msg = {"critical": "⚠️ CRITICAL — Immediate AMS review required",
                "watch":    "🟡 WATCH — Increased monitoring indicated",
                "routine":  "✅ ROUTINE — Continue standard monitoring"}
    getattr(st, flag_color.get(report.overall_flag, "info"))(flag_msg.get(report.overall_flag, ""))

    # Correlation flags
    if report.correlation_flags:
        for flag in report.correlation_flags:
            st.markdown(f"• {flag}")

    st.markdown("---")

    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Utilization Trend", "🚨 FAERS Signals", "📋 Data Table", "🧠 AMS Summary"
    ])

    # ── Tab 1: Utilization trend chart ────────────────────────────────────────
    with tab1:
        if not report.nhsn_records:
            st.info("No NHSN records available.")
        else:
            rec_df = pd.DataFrame([{
                "Year-Q":        f"{r.year} Q{r.quarter}" if r.quarter else str(r.year),
                "DOT/1000 PD":   r.dot_per_1000,
                "Anomaly":       next((a.anomaly_type for a in report.anomalies
                                       if a.year == r.year and a.quarter == r.quarter), "normal"),
            } for r in report.nhsn_records])

            fig, ax = plt.subplots(figsize=(12, 4))
            x = range(len(rec_df))
            ax.plot(x, rec_df["DOT/1000 PD"], color="#2e7d32", linewidth=2, marker="o", markersize=5)
            ax.axhline(report.benchmark, color="#c62828", linestyle="--", linewidth=1.5,
                       label=f"National benchmark ({report.benchmark:.0f})")

            # Shade anomalies
            for i, (_, row) in enumerate(rec_df.iterrows()):
                if row["Anomaly"] == "spike":
                    ax.axvspan(i - 0.5, i + 0.5, alpha=0.25, color="#c62828")
                elif row["Anomaly"] == "sustained_high":
                    ax.axvspan(i - 0.5, i + 0.5, alpha=0.15, color="#e65100")

            tick_step = max(1, len(x) // 12)
            ax.set_xticks(list(x)[::tick_step])
            ax.set_xticklabels(rec_df["Year-Q"].tolist()[::tick_step], rotation=45, ha="right", fontsize=8)
            ax.set_ylabel("Days of Therapy / 1000 Patient-Days", fontsize=9)
            ax.set_title(
                f"{selected_label} — Utilization Trend\n"
                f"Period: {start_year}–present  ·  Data: {', '.join(report.data_sources)}",
                fontsize=11, fontweight="bold",
            )
            ax.legend(fontsize=8)
            patches = [
                mpatches.Patch(color="#c62828", alpha=0.25, label="Spike anomaly"),
                mpatches.Patch(color="#e65100", alpha=0.15, label="Sustained high"),
            ]
            ax.legend(handles=patches + [plt.Line2D([0], [0], color="#c62828", linestyle="--",
                                                     label="National benchmark")], fontsize=8)
            ax.grid(axis="y", linestyle="--", alpha=0.3)
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()

            st.caption(
                f"Source: {', '.join(report.data_sources)}  ·  "
                f"Red shading = spike; orange = sustained high relative to benchmark"
            )

    # ── Tab 2: FAERS signals ──────────────────────────────────────────────────
    with tab2:
        sig_data = [s for s in report.faers_signals if s.signal]
        if not sig_data:
            st.success(f"No Evans-positive FAERS signals for {selected_label}.")
        else:
            df_s = pd.DataFrame([{
                "Reaction PT":  s.reaction_pt,
                "Drug N":       s.drug_cases,
                "PRR":          s.prr,
                "ROR":          s.ror,
                "chi²":         s.chi2,
                "Strength":     s.signal_strength,
            } for s in sig_data])

            def _scolor(val):
                return {
                    "strong":    "background-color: #ffcccc",
                    "moderate":  "background-color: #ffe4b5",
                    "threshold": "background-color: #e8f5e9",
                }.get(val, "")

            st.dataframe(
                df_s.style.map(_scolor, subset=["Strength"]),
                use_container_width=True, height=min(500, 50 + len(df_s) * 36),
            )

            # AMS category pie
            cats = {k: v for k, v in report.ams_category_counts.items() if v > 0}
            if cats:
                fig2, ax2 = plt.subplots(figsize=(6, 4))
                ax2.pie(list(cats.values()), labels=list(cats.keys()), autopct="%1.0f%%",
                        colors=["#2e7d32", "#66bb6a", "#a5d6a7", "#c8e6c9", "#e8f5e9", "#1b5e20"],
                        startangle=90, textprops={"fontsize": 8.5})
                ax2.set_title(f"{selected_label} — FAERS AMS Category Breakdown", fontsize=10)
                plt.tight_layout()
                st.pyplot(fig2)
                plt.close()

    # ── Tab 3: Data table ─────────────────────────────────────────────────────
    with tab3:
        st.subheader("NHSN Utilization Records")
        nhsn_df = pd.DataFrame([{
            "Year":          r.year,
            "Quarter":       r.quarter,
            "DOT/1000 PD":   r.dot_per_1000,
            "Benchmark":     report.benchmark,
            "Deviation %":   round((r.dot_per_1000 - report.benchmark) / report.benchmark * 100, 1),
            "Type":          next((a.anomaly_type for a in report.anomalies
                                   if a.year == r.year and a.quarter == r.quarter), "normal"),
            "Source":        r.source,
        } for r in report.nhsn_records])
        st.dataframe(nhsn_df, use_container_width=True, height=300)
        csv = nhsn_df.to_csv(index=False)
        st.download_button(
            "Download utilization CSV", csv,
            file_name=f"{drug_class}_utilization.csv", mime="text/csv",
        )

    # ── Tab 4: AMS summary ────────────────────────────────────────────────────
    with tab4:
        st.subheader("AMS Committee Summary")
        st.markdown(report.llm_summary)
        st.divider()
        st.caption(
            "Generated by AMS Intelligence using local LLM inference. "
            "This summary is a draft for clinical review — not for direct policy implementation."
        )

    # ── Auto-save PDF ─────────────────────────────────────────────────────────
    try:
        from shared.pdf_exporter import generate_utilization_full_report
        pdf_path = generate_utilization_full_report(
            drug_class=drug_class,
            period=f"{start_year}–present",
            nhsn_records=report.nhsn_records,
            benchmark=report.benchmark,
            anomalies=report.anomalies,
            faers_signals=report.faers_signals,
            ams_categories=report.ams_categories,
            correlation_flags=report.correlation_flags,
            anomaly_score=report.anomaly_score,
            overall_flag=report.overall_flag,
            llm_summary=report.llm_summary,
            data_sources=report.data_sources,
        )
        st.success(f"PDF saved → {pdf_path.name}")
        try:
            st.download_button(
                "📄 Download PDF Report",
                pdf_path.read_bytes(),
                file_name=pdf_path.name,
                mime="application/pdf",
                use_container_width=True,
            )
        except Exception:
            pass
    except Exception as e:
        st.warning(f"PDF save failed: {e}")

# ── Static reference ─────────────────────────────────────────────────────────
st.divider()
with st.expander("GVP / AMS Monitoring Schedule Reference"):
    st.markdown("""
| Drug Class | Recommended Review Frequency | Key Concern |
|---|---|---|
| Carbapenems | Weekly (active AMS target) | Carbapenem-resistant Enterobacterales |
| Fluoroquinolones | Monthly | C. difficile, tendinopathy |
| Vancomycin | Weekly (ICU), Monthly (general) | AUC-guided dosing, nephrotoxicity |
| Pip/Tazo | Monthly | ESBL selection, renal dosing |
| 3rd-gen Cephalosporins | Monthly | ESBL/AmpC induction |
| Azithromycin | Quarterly | QTc prolongation, macrolide resistance |

*Per ASHP/IDSA/SIDP AMS guidelines and GVP Module VI monitoring principles.*
    """)
