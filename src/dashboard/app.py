"""
AMS Intelligence — Streamlit Dashboard

Run from project root:
    PYTHONPATH=src streamlit run src/dashboard/app.py
"""

import json
import subprocess
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))

from auth import require_auth, auth_sidebar
from config import (
    OLLAMA_BASE_URL, REASON_MODEL, CODE_MODEL, EMBED_MODEL,
    CHROMA_PATH, COLLECTION_NAME, OUTPUT_DIR,
)

st.set_page_config(
    page_title="AMS Intelligence",
    page_icon="🦠",
    layout="wide",
    initial_sidebar_state="expanded",
)

require_auth()


# ── Cached system status helpers ─────────────────────────────────────────────

@st.cache_data(ttl=20)
def _ollama_tags() -> dict:
    try:
        req = urllib.request.Request(
            f"{OLLAMA_BASE_URL}/api/tags", headers={"User-Agent": "ams-intelligence"}
        )
        with urllib.request.urlopen(req, timeout=3) as r:
            data = json.loads(r.read())
        return {
            m["name"]: {"size_mb": m["size"] // 1024 // 1024, "modified": m.get("modified_at", "")[:10]}
            for m in data.get("models", [])
        }
    except Exception:
        return {}


@st.cache_data(ttl=10)
def _ollama_running() -> list[str]:
    try:
        req = urllib.request.Request(
            f"{OLLAMA_BASE_URL}/api/ps", headers={"User-Agent": "ams-intelligence"}
        )
        with urllib.request.urlopen(req, timeout=3) as r:
            data = json.loads(r.read())
        return [m["name"] for m in data.get("models", [])]
    except Exception:
        return []


@st.cache_data(ttl=60)
def _vault_chunks() -> int:
    try:
        import chromadb
        client = chromadb.PersistentClient(path=str(CHROMA_PATH))
        col    = client.get_collection(COLLECTION_NAME)
        return col.count()
    except Exception:
        return -1


@st.cache_data(ttl=5)
def _gpu_info() -> str | None:
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=memory.used,memory.total,utilization.gpu",
             "--format=csv,noheader,nounits"], text=True, timeout=5,
        ).strip()
        used, total, util = [x.strip() for x in out.split(",")]
        return f"{int(used)/1024:.1f} / {int(total)/1024:.1f} GB  ·  {util}% GPU util"
    except Exception:
        return None


@st.cache_data(ttl=30)
def _output_files() -> list[dict]:
    files = []
    for f in sorted(OUTPUT_DIR.glob("*.pdf"), key=lambda p: p.stat().st_mtime, reverse=True)[:10]:
        stat = f.stat()
        files.append({
            "name": f.name,
            "path": str(f),
            "size_kb": round(stat.st_size / 1024, 1),
            "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
        })
    return files


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🦠 AMS Intelligence")
    st.caption("Antimicrobial Stewardship Research Pipeline")
    st.markdown("---")
    st.markdown("**Navigation**")
    st.page_link("app.py",                           label="Home",                icon="🏠")
    st.page_link("pages/1_Resistance_Trends.py",     label="Resistance Trends",   icon="📊")
    st.page_link("pages/2_Utilization_Signals.py",   label="Utilization Signals", icon="📈")
    st.page_link("pages/3_Files.py",                 label="Files",               icon="📁")
    auth_sidebar()
    st.markdown("---")
    st.caption("All outputs are research summaries for AMS review only.")


# ── Header ────────────────────────────────────────────────────────────────────

col_title, col_readme = st.columns([5, 1])
with col_title:
    st.title("🦠 AMS Intelligence")
    st.caption("Antimicrobial Stewardship Research Pipeline · Local-First · Privacy-Preserving")
    st.markdown("**Michael Olszewski, PharmD, BCPS, BCCCP** · Creator & Senior Clinical Reviewer")
with col_readme:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("📖 README", use_container_width=True, help="Full documentation and technical specs"):
        st.session_state["show_readme"] = not st.session_state.get("show_readme", False)

if st.session_state.get("show_readme", False):
    readme_path = Path(__file__).parent.parent.parent / "README.md"
    try:
        readme_text = readme_path.read_text()
        with st.expander("📖 AMS Intelligence — Documentation & Technical Specifications", expanded=True):
            st.markdown(readme_text)
    except Exception:
        st.warning("README.md not found.")


# ── System Status ─────────────────────────────────────────────────────────────

st.markdown("### System Status")

tags    = _ollama_tags()
running = _ollama_running()
chunks  = _vault_chunks()
gpu     = _gpu_info()

CORE_MODELS = [
    (REASON_MODEL, "Reasoning",   "Signal analysis · LLM interpretation · AMS summaries"),
    (CODE_MODEL,   "Code/Pipeline","Structured output · Data parsing · Pipeline tasks"),
    (EMBED_MODEL,  "Embeddings",   "Vault RAG · Guideline retrieval"),
]

status_cols = st.columns(len(CORE_MODELS) + 1)

for col, (mname, role, desc) in zip(status_cols, CORE_MODELS):
    base  = mname.split(":")[0]
    info  = tags.get(mname) or next((v for k, v in tags.items() if k.startswith(base)), {})
    in_vram   = any(base in r for r in running)
    available = bool(info)

    badge, bcolor = (
        ("● In VRAM",  "green") if in_vram else
        ("● Available","blue")  if available else
        ("● Not found","red")
    )
    size_str = f"{info['size_mb']:,} MB" if info else "—"

    with col:
        with st.container(border=True):
            st.markdown(f"**{role}**")
            st.caption(f"`{mname}`")
            st.caption(size_str)
            if bcolor == "green":
                st.success(badge)
            elif bcolor == "blue":
                st.info(badge)
            else:
                st.error(badge)

# Vault card
with status_cols[-1]:
    with st.container(border=True):
        st.markdown("**Knowledge Vault**")
        st.caption("ChromaDB · AMS Guidelines")
        if chunks > 0:
            st.caption(f"{chunks} chunks")
            st.success("● Indexed")
        else:
            st.caption("No documents indexed")
            st.warning("● Empty")

if gpu:
    st.caption(f"🖥️  RTX 5060 Ti · {gpu}")

_, col_refresh = st.columns([6, 1])
with col_refresh:
    if st.button("↻ Refresh", key="refresh_status"):
        st.cache_data.clear()
        st.rerun()


# ── Command Center ────────────────────────────────────────────────────────────

st.markdown("---")
st.markdown("### Command Center")
st.caption(
    "**Commands:** `status` · `run resistance <drug> vs <comparator>` · "
    "`run utilization <class>` · `files` · `ask <question>` · `help`"
)

if "cmd_history" not in st.session_state:
    st.session_state.cmd_history = []

col_cmd, col_run = st.columns([6, 1])
with col_cmd:
    cmd_input = st.text_input(
        "command", label_visibility="collapsed",
        placeholder="run resistance <drug> vs <comparator>  |  run utilization <drug class>  |  ask <clinical question>  |  status  |  help",
        key="cmd_text",
    )
with col_run:
    run_pressed = st.button("Run", type="primary", use_container_width=True)

DRUG_CLASS_KEYS = {
    "fluoroquinolones", "carbapenems", "vancomycin",
    "cephalosporins_1g", "cephalosporins_3g", "piperacillin_tazo",
    "azithromycin", "metronidazole", "trimethoprim_sulfa",
}
DRUG_CLASS_ALIASES = {
    "fluoroquinolone":      "fluoroquinolones",
    "carbapenem":           "carbapenems",
    "cephalosporins 1g":    "cephalosporins_1g",
    "cephalosporins 3g":    "cephalosporins_3g",
    "piperacillin":         "piperacillin_tazo",
    "pip/tazo":             "piperacillin_tazo",
    "azithro":              "azithromycin",
    "metro":                "metronidazole",
    "tmp/smx":              "trimethoprim_sulfa",
    "bactrim":              "trimethoprim_sulfa",
}


def _resolve_drug_class(raw: str) -> str:
    key = raw.lower().strip().replace(" ", "_")
    if key in DRUG_CLASS_KEYS:
        return key
    return DRUG_CLASS_ALIASES.get(raw.lower().strip(), key)


def _execute_cmd(raw: str) -> tuple[str, str | None]:
    """Returns (markdown_result, optional_pdf_path)."""
    cmd   = raw.strip()
    lower = cmd.lower()

    # ── status / models ──────────────────────────────────────────────────────
    if lower in ("status", "models", "health", "model status"):
        t   = _ollama_tags()
        r   = _ollama_running()
        v   = _vault_chunks()
        g   = _gpu_info()
        lines = ["**System Status**\n"]
        for mname, role, _ in CORE_MODELS:
            base = mname.split(":")[0]
            info = t.get(mname) or next((v2 for k, v2 in t.items() if k.startswith(base)), {})
            ok   = "✓" if info else "✗"
            vram = " · **in VRAM**" if any(base in rn for rn in r) else ""
            size = f"{info['size_mb']:,} MB" if info else "not found"
            lines.append(f"- {ok} **{role}** `{mname}` — {size}{vram}")
        lines.append(f"\n**Vault**: {v} chunks")
        if g: lines.append(f"**GPU**: {g}")
        return "\n".join(lines), None

    # ── files ────────────────────────────────────────────────────────────────
    if lower in ("files", "list files", "outputs"):
        recent = _output_files()
        if not recent:
            return "No output files yet. Run an analysis to generate reports.", None
        lines = [f"**Recent Output Files** ({len(recent)} found)\n"]
        for f in recent:
            lines.append(f"- `{f['name']}` · {f['size_kb']} KB · {f['modified']}")
        lines.append("\nOpen **Files** page to download.")
        return "\n".join(lines), None

    # ── run resistance ────────────────────────────────────────────────────────
    if lower.startswith("run resistance"):
        parts = cmd.split()
        drug, comparator = "cefazolin", "cefpodoxime"
        try:
            vs_idx = [p.lower() for p in parts].index("vs")
            drug       = parts[vs_idx - 1]
            comparator = parts[vs_idx + 1]
        except (ValueError, IndexError):
            if len(parts) >= 3:
                drug = parts[2]

        with st.spinner(f"Running resistance analysis: {drug} vs {comparator}…"):
            try:
                from modules.resistance_analyzer import run_resistance_analysis
                result = run_resistance_analysis(
                    drug=drug, comparator=comparator, run_llm=True
                )
                n_sig  = sum(1 for s in result.signals if s.signal)
                top_prr = f"{result.signals[0].prr:.2f}" if result.signals else "—"
                pdf_p   = result.pdf_path
                msg = (
                    f"**Resistance Analysis Complete — {drug.capitalize()} vs {comparator.capitalize()}**\n\n"
                    f"- FAERS reports (drug): {result.drug_total:,}\n"
                    f"- Evans signals: {n_sig}  ·  Top PRR: {top_prr}\n"
                    f"- Period: {result.start_year}–{result.end_year}\n"
                )
                if pdf_p:
                    msg += f"\n📄 PDF report generated — see **Files** page to download."
                return msg, pdf_p
            except Exception as e:
                return f"Analysis failed: {e}", None

    # ── run utilization ───────────────────────────────────────────────────────
    if lower.startswith("run utilization"):
        parts = cmd.split(None, 2)
        raw_class  = parts[2] if len(parts) > 2 else "fluoroquinolones"
        drug_class = _resolve_drug_class(raw_class)

        with st.spinner(f"Detecting utilization signals: {drug_class}…"):
            try:
                from modules.utilization_detector import detect_utilization_signals
                report = detect_utilization_signals(drug_class=drug_class, run_llm=True)
                n_an = sum(1 for a in report.anomalies if a.anomaly_type != "normal")
                n_fs = sum(1 for s in report.faers_signals if s.signal)
                msg = (
                    f"**Utilization Analysis Complete — {drug_class.replace('_', ' ').title()}**\n\n"
                    f"- Periods analyzed: {len(report.nhsn_records)}\n"
                    f"- Anomalous periods: {n_an}  ·  FAERS signals: {n_fs}\n"
                    f"- Overall flag: **{report.overall_flag.upper()}**\n"
                )
                if report.pdf_path:
                    msg += f"\n📄 PDF report generated — see **Files** page to download."
                return msg, report.pdf_path
            except Exception as e:
                return f"Analysis failed: {e}", None

    # ── ask ───────────────────────────────────────────────────────────────────
    if lower.startswith("ask "):
        question = cmd[4:].strip()
        if not question:
            return "Usage: `ask <question>`", None
        with st.spinner(f"Querying {REASON_MODEL}…"):
            try:
                import json, urllib.request
                payload = json.dumps({
                    "model": REASON_MODEL,
                    "think": False,
                    "stream": False,
                    "messages": [
                        {"role": "system", "content":
                            "You are a clinical AMS pharmacist. Answer concisely "
                            "(3-5 sentences, evidence-based, pharmacovigilance focus)."},
                        {"role": "user", "content": question},
                    ],
                }).encode()
                req = urllib.request.Request(
                    f"{OLLAMA_BASE_URL}/api/chat",
                    data=payload, headers={"Content-Type": "application/json"},
                )
                with urllib.request.urlopen(req, timeout=90) as resp:
                    data = json.loads(resp.read())
                answer = data.get("message", {}).get("content", "").strip()
                return f"**Q:** {question}\n\n**A:** {answer}", None
            except Exception as e:
                return f"LLM error: {e}", None

    # ── help ──────────────────────────────────────────────────────────────────
    if lower in ("help", "?", "commands"):
        return (
            "**AMS Intelligence Command Reference**\n\n"
            "| Command | Description |\n|---|---|\n"
            "| `status` | Ollama model status, vault, GPU |\n"
            "| `files` | List recent output files |\n"
            "| `run resistance <drug> vs <comp>` | Run resistance trend analysis + PDF |\n"
            "| `run utilization <class>` | Run utilization signal detection + PDF |\n"
            "| `ask <question>` | Direct AMS Q&A via local LLM |\n"
            "| `help` | Show this reference |\n\n"
            "**Drug classes for `run utilization`:** "
            "fluoroquinolones, carbapenems, vancomycin, cephalosporins_1g, "
            "cephalosporins_3g, piperacillin_tazo, azithromycin, metronidazole, trimethoprim_sulfa"
        ), None

    # ── LLM fallback ─────────────────────────────────────────────────────────
    with st.spinner(f"Routing to {REASON_MODEL}…"):
        try:
            payload = json.dumps({
                "model": REASON_MODEL,
                "think": False,
                "stream": False,
                "messages": [
                    {"role": "system", "content":
                        "You are an AMS pharmacist assistant embedded in an antimicrobial stewardship platform. "
                        "Available commands: status, run resistance <drug> vs <comp>, "
                        "run utilization <drug class>, ask <question>. "
                        "If the input looks like a command, explain what it does and suggest correct syntax. "
                        "If it is a clinical question, answer concisely (3-5 sentences, AMS focus)."},
                    {"role": "user", "content": cmd},
                ],
            }).encode()
            req = urllib.request.Request(
                f"{OLLAMA_BASE_URL}/api/chat",
                data=payload, headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=90) as resp:
                data = json.loads(resp.read())
            return data.get("message", {}).get("content", "No response.").strip(), None
        except Exception as e:
            return f"Unrecognized command. Type `help` for available commands.\n\nError: {e}", None


if run_pressed and cmd_input:
    result_text, result_pdf = _execute_cmd(cmd_input)
    st.session_state.cmd_history.insert(0, {
        "cmd":      cmd_input,
        "result":   result_text,
        "pdf_path": result_pdf,
        "ts":       datetime.now().strftime("%H:%M:%S"),
    })
    st.cache_data.clear()  # refresh file list after any analysis

if st.session_state.cmd_history:
    for i, entry in enumerate(st.session_state.cmd_history[:8]):
        with st.expander(f"`{entry['cmd']}`  —  {entry['ts']}", expanded=(i == 0)):
            st.markdown(entry["result"])
            if entry.get("pdf_path"):
                try:
                    pdf_bytes = Path(entry["pdf_path"]).read_bytes()
                    st.download_button(
                        "📄 Download PDF Report",
                        pdf_bytes,
                        file_name=Path(entry["pdf_path"]).name,
                        mime="application/pdf",
                        key=f"dl_{entry['ts']}_{i}",
                    )
                except Exception:
                    pass
    col_clr, _ = st.columns([1, 5])
    with col_clr:
        if st.button("Clear history", key="clear_hist"):
            st.session_state.cmd_history = []
            st.rerun()


# ── Data Source Status ────────────────────────────────────────────────────────

st.markdown("---")
st.markdown("### Data Sources")

from config import DATA_DIR
nhsn_files  = list((DATA_DIR / "nhsn").glob("*.csv"))
whonet_files = list((DATA_DIR / "whonet").glob("*.csv"))
atlas_file  = DATA_DIR / "atlas" / "atlas_antibiotics.csv"

ds_cols = st.columns(4)
for col, (label, files_present, detail, url) in zip(ds_cols, [
    ("FAERS",  True,                "FDA OpenFDA API — live",        "api.fda.gov/drug/event.json"),
    ("NHSN",   bool(nhsn_files),    f"{len(nhsn_files)} CSV file(s)", "cdc.gov/nhsn"),
    ("WHONET", bool(whonet_files),  f"{len(whonet_files)} CSV file(s)","whonet.org"),
    ("ATLAS",  atlas_file.exists(), "atlas_antibiotics.csv",          "pfizer.com/atlas"),
]):
    with col:
        with st.container(border=True):
            st.markdown(f"**{label}**")
            st.caption(detail)
            if files_present:
                st.success("● Ready")
            else:
                st.warning("● Demo data" if label != "FAERS" else "● Live")
    if not files_present and label != "FAERS":
        pass   # silently degrade to demo data


# ── Module Cards ──────────────────────────────────────────────────────────────

st.markdown("---")
st.markdown("### Modules")

m1, m2 = st.columns(2)

with m1:
    with st.container(border=True):
        st.markdown("### 📊 Resistance Trend Analyzer")
        st.caption(f"`{REASON_MODEL}`  ·  FAERS + WHONET + ATLAS")
        st.markdown("""
- PRR / ROR disproportionality analysis
- Temporal pre/post formulary-change comparison
- MIC creep visualization (ATLAS data)
- Auto-generated one-page findings summary PDF
        """)
        st.success("✓ Active")
        if st.button("Open →", key="open_m1", use_container_width=True):
            st.switch_page("pages/1_Resistance_Trends.py")

with m2:
    with st.container(border=True):
        st.markdown("### 📈 Utilization Signal Detector")
        st.caption(f"`{REASON_MODEL}`  ·  FAERS + NHSN")
        st.markdown("""
- NHSN DOT/1000 patient-days trend analysis
- Cross-reference utilization spikes with FAERS signals
- C. difficile and resistance-driven anomaly flagging
- Plain-language AMS committee summaries
        """)
        st.success("✓ Active")
        if st.button("Open →", key="open_m2", use_container_width=True):
            st.switch_page("pages/2_Utilization_Signals.py")


# ── Recent Outputs ────────────────────────────────────────────────────────────

recent = _output_files()
if recent:
    st.markdown("---")
    st.markdown("### Recent Reports")
    for entry in recent:
        col_n, col_m, col_dl = st.columns([5, 2, 1.5])
        with col_n:
            st.markdown(f"📄 **{entry['name']}**")
        with col_m:
            st.caption(f"{entry['size_kb']} KB · {entry['modified']}")
        with col_dl:
            try:
                file_bytes = Path(entry["path"]).read_bytes()
                st.download_button(
                    "Download", file_bytes, file_name=entry["name"],
                    mime="application/pdf", key=entry["path"],
                    use_container_width=True,
                )
            except Exception:
                st.caption("Read error")


# ── Quick Reference ───────────────────────────────────────────────────────────

st.markdown("---")
col_a, col_b = st.columns(2)

with col_a:
    st.markdown("### AMS Metrics")
    with st.expander("**Evans Signal Criteria**"):
        st.markdown("""
All three must be met simultaneously:
- **PRR ≥ 2.0** — at least 2× overrepresented vs. comparator
- **N ≥ 3** — minimum 3 drug-reaction co-reports
- **chi² ≥ 4.0** — statistical significance threshold
*Yates' correction applied for small expected cells.*
        """)
    with st.expander("**DOT / DDD Benchmarks**"):
        st.markdown("""
| Drug Class | Target DOT/1000 PD |
|---|---|
| Fluoroquinolones | < 75 |
| Carbapenems | < 25 |
| Vancomycin | < 65 |
| Pip/Tazo | < 80 |
*Based on NHSN national benchmarks.*
        """)

with col_b:
    st.markdown("### Data Sources Guide")
    with st.expander("**Loading NHSN Data**"):
        st.markdown("""
1. Enroll facility at [nhsn.cdc.gov](https://nhsn.cdc.gov)
2. Export Antimicrobial Use → Facility-Wide Inpatient
3. Save CSV → `data/nhsn/AU_FacilityWideInpatient_YYYY.csv`
4. Refresh dashboard — demo data replaced automatically
        """)
    with st.expander("**Loading ATLAS Data**"):
        st.markdown("""
1. Download from [Pfizer ATLAS](https://www.pfizer.com/science/clinical-trials/atlas-dataset)
2. Save as `data/atlas/atlas_antibiotics.csv`
3. Restart dashboard — file loaded automatically
        """)
