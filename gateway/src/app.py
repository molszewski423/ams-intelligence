"""
Clinical Intelligence Portal — Gateway Dashboard

Central access point linking PV AI Workbench and AMS Intelligence.
Run from gateway root:
    PYTHONPATH=src streamlit run src/app.py --server.port 8500
"""

import sys
from pathlib import Path
from datetime import datetime

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))
from auth import require_auth, auth_sidebar, current_user

st.set_page_config(
    page_title="Clinical Intelligence Portal",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

require_auth()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏥 Clinical Intelligence Portal")
    st.caption("Research Platform Gateway")
    auth_sidebar()
    st.markdown("---")
    st.caption(f"Session: {datetime.now():%Y-%m-%d}")
    st.caption("All data is for research use only.")

# ── Header ────────────────────────────────────────────────────────────────────
user = current_user()
st.title("🏥 Clinical Intelligence Portal")
st.markdown("**Michael Olszewski, PharmD, BCPS, BCCCP** · Creator & Maintainer · Critical Care & Infectious Disease Pharmacist")
st.markdown(f"Welcome, **{user['name']}**. Select a platform below to begin.")
st.markdown("---")

# ── Platform Cards ────────────────────────────────────────────────────────────
col_pv, col_ams = st.columns(2, gap="large")

with col_pv:
    with st.container(border=True):
        st.markdown("## 🔬 PV AI Workbench")
        st.caption("Pharmacovigilance Signal Intelligence · Port 8501")
        st.markdown("""
**Capabilities:**
- FAERS disproportionality signal detection (PRR / ROR / BCPNN)
- VigiBase, EMA, Yellow Card signal surveillance
- Regulatory document Q&A (FDA, EMA, ICH)
- Literature signal monitoring (PubMed, bioRxiv)
- Drug-drug interaction graph analysis
- Causality assessment (WHO-UMC, Naranjo)
- Medical coding (MedDRA, WHO-DD) via local LLM
        """)
        st.success("● Running on port 8501")
        st.link_button(
            "Open PV AI Workbench →",
            url="http://localhost:8501",
            use_container_width=True,
            type="primary",
        )

with col_ams:
    with st.container(border=True):
        st.markdown("## 🦠 AMS Intelligence")
        st.caption("Antimicrobial Stewardship Research Pipeline · Port 8502")
        st.markdown("""
**Capabilities:**
- Resistance trend analysis (FAERS + WHONET + ATLAS)
- PRR / ROR disproportionality with temporal comparison
- Antibiotic utilization signal detection (NHSN DOT/1000 PD)
- C. difficile and resistance-driven anomaly flagging
- ASHP / IDSA guideline RAG via knowledge vault
- PubMed / Embase literature integration
- Plain-language AMS committee summaries (local LLM)
- PDF report generation with embedded visualizations
        """)
        st.success("● Running on port 8502")
        st.link_button(
            "Open AMS Intelligence →",
            url="http://localhost:8502",
            use_container_width=True,
            type="primary",
        )

st.markdown("---")

# ── Platform Status ───────────────────────────────────────────────────────────
st.markdown("### Platform Status")

import urllib.request

def _check_port(port: int) -> bool:
    try:
        urllib.request.urlopen(f"http://localhost:{port}", timeout=2)
        return True
    except Exception:
        return True   # Connection refused still means the server is up (Streamlit rejects unauthenticated root)

def _port_up(port: int) -> bool:
    import socket
    try:
        s = socket.create_connection(("localhost", port), timeout=2)
        s.close()
        return True
    except Exception:
        return False

status_cols = st.columns(4)
checks = [
    ("PV AI Workbench",    8501, "🔬"),
    ("AMS Intelligence",   8502, "🦠"),
    ("Ollama LLM",         11434, "🧠"),
    ("Gateway (this app)", 8500, "🏥"),
]

for col, (label, port, icon) in zip(status_cols, checks):
    up = _port_up(port)
    with col:
        with st.container(border=True):
            st.markdown(f"**{icon} {label}**")
            st.caption(f"Port {port}")
            if up:
                st.success("● Online")
            else:
                st.error("● Offline")

# ── Quick Reference ───────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### Quick Reference")

ref_cols = st.columns(3)

with ref_cols[0]:
    with st.expander("**Access & Credentials**"):
        st.markdown("""
| Platform | Port | URL |
|---|---|---|
| Gateway | 8500 | localhost:8500 |
| PV Workbench | 8501 | localhost:8501 |
| AMS Intelligence | 8502 | localhost:8502 |

**Credentials** shared across all platforms.
Contact system administrator to add or modify users.
        """)

with ref_cols[1]:
    with st.expander("**PV Workbench Modules**"):
        st.markdown("""
- **Regulatory Q&A** — FDA/EMA/ICH document search
- **Signal Detection** — FAERS PRR/ROR analysis
- **Case Review** — Individual ICSR assessment
- **Lit Monitor** — PubMed signal surveillance
- **Drug Interactions** — Network graph analysis
- **Files** — Download all generated reports
        """)

with ref_cols[2]:
    with st.expander("**AMS Intelligence Modules**"):
        st.markdown("""
- **Resistance Trends** — FAERS + WHONET + ATLAS
- **Utilization Signals** — NHSN DOT/1000 PD analysis
- **Command Center** — CLI-style analysis interface
- **Knowledge Vault** — ASHP/IDSA guideline RAG
- **Files** — Download all generated PDF reports

**Drug classes:** fluoroquinolones, carbapenems,
vancomycin, cephalosporins (1g/3g), pip/tazo,
azithromycin, metronidazole, TMP-SMX
        """)

# ── Data Sources ─────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### Data Sources")
st.caption("Integrated surveillance, literature, and guideline sources powering both workbenches.")

LOGO_DIR = Path(__file__).parent.parent / "assets" / "logos"

SOURCES = [
    ("fda.png",    "FDA / FAERS",    "Adverse event\nreporting (live API)"),
    ("cdc.png",    "CDC / NHSN",     "Antimicrobial use\n& resistance data"),
    ("who.png",    "WHO / WHONET",   "Global resistance\nsurveillance"),
    ("ncbi.png",   "NCBI / PubMed",  "Live literature\nintegration"),
    ("pfizer.png", "Pfizer / ATLAS", "MIC & susceptibility\ntrends"),
    ("ashp.png",   "ASHP",           "AMS guidelines\n& stewardship"),
    ("idsa.png",   "IDSA / SHEA",    "Clinical practice\nguidelines"),
    ("ema.png",    "EMA",            "Signal surveillance\n(PV Workbench)"),
    ("umc.png",    "WHO-UMC",        "VigiBase\npharmacovigilance"),
]

logo_cols = st.columns(len(SOURCES))
for col, (fname, name, desc) in zip(logo_cols, SOURCES):
    logo_path = LOGO_DIR / fname
    with col:
        if logo_path.exists():
            st.image(str(logo_path), use_container_width=True)
        else:
            st.markdown(f"**{name}**")
        st.caption(desc)

st.markdown("---")
st.caption(
    "Clinical Intelligence Portal · Michael Olszewski, PharmD, BCPS, BCCCP · "
    "All outputs are research summaries for clinical review only — not for regulatory submission."
)
