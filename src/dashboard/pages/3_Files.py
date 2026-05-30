"""Generated Files — AMS Intelligence"""

import sys
from pathlib import Path
from datetime import datetime
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from auth import require_auth, auth_sidebar
from config import OUTPUT_DIR

st.set_page_config(page_title="Files — AMS Intelligence", page_icon="📁", layout="wide")
require_auth()
with st.sidebar:
    auth_sidebar()

st.title("📁 Generated Files")
st.caption("All reports, charts, and data files produced by AMS Intelligence analyses.")

INCLUDE_SUFFIXES = {
    ".pdf":  ("PDF Report",     "📄"),
    ".csv":  ("CSV Data",       "📋"),
    ".png":  ("Chart / Image",  "🖼️"),
    ".json": ("JSON Data",      "📊"),
    ".html": ("HTML Report",    "🌐"),
}

MIME_MAP = {
    ".pdf":  "application/pdf",
    ".csv":  "text/csv",
    ".png":  "image/png",
    ".json": "application/json",
    ".html": "text/html",
}

SEARCH_DIRS = [
    (OUTPUT_DIR,                         "AMS Output"),
    (Path.home() / "ams-intelligence" / "output", "AMS Output (alt)"),
]


@st.cache_data(ttl=10)
def _scan_files() -> list[dict]:
    results, seen = [], set()
    for base, label in SEARCH_DIRS:
        if not base.exists():
            continue
        for f in sorted(base.glob("**/*"), key=lambda p: p.stat().st_mtime, reverse=True):
            if not f.is_file() or f.suffix.lower() not in INCLUDE_SUFFIXES:
                continue
            resolved = f.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            stat = f.stat()
            results.append({
                "path":     f,
                "name":     f.name,
                "label":    label,
                "suffix":   f.suffix.lower(),
                "size_kb":  stat.st_size / 1024,
                "modified": datetime.fromtimestamp(stat.st_mtime),
            })
    return results


files = _scan_files()

# ── Controls ──────────────────────────────────────────────────────────────────
c1, c2, c3 = st.columns([2, 2, 3])
with c1:
    type_opts = ["All"] + sorted({INCLUDE_SUFFIXES[f["suffix"]][0] for f in files})
    type_filt = st.selectbox("File type", type_opts)
with c2:
    search = st.text_input("Search", placeholder="e.g. cefazolin, utilization")
with c3:
    st.markdown("<br>", unsafe_allow_html=True)
    col_r, col_del = st.columns(2)
    with col_r:
        if st.button("↻ Refresh", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    with col_del:
        if st.button("🗑️ Clear All", use_container_width=True, type="secondary",
                     help="Delete all files in output/"):
            for f in files:
                try:
                    f["path"].unlink()
                except Exception:
                    pass
            st.cache_data.clear()
            st.rerun()

filtered = files
if type_filt != "All":
    filtered = [f for f in filtered if INCLUDE_SUFFIXES[f["suffix"]][0] == type_filt]
if search.strip():
    q = search.strip().lower()
    filtered = [f for f in filtered if q in f["name"].lower()]

if not files:
    st.info("No files yet. Run a Resistance Trends or Utilization Signals analysis to generate reports.")
    st.stop()

st.caption(f"Showing {len(filtered)} of {len(files)} files")
st.markdown("---")

if not filtered:
    st.info("No files match the current filters.")
    st.stop()

# ── File listing ──────────────────────────────────────────────────────────────
for entry in filtered:
    suffix = entry["suffix"]
    type_label, icon = INCLUDE_SUFFIXES.get(suffix, ("File", "📄"))
    size_str = (
        f"{entry['size_kb'] / 1024:.1f} MB" if entry["size_kb"] > 1024
        else f"{entry['size_kb']:.0f} KB"
    )
    modified_str = entry["modified"].strftime("%Y-%m-%d %H:%M")

    col_ic, col_nm, col_meta, col_dl = st.columns([0.5, 4, 2, 1.5])
    with col_ic:
        st.markdown(f"### {icon}")
    with col_nm:
        st.markdown(f"**{entry['name']}**")
        st.caption(str(entry["path"].parent))
    with col_meta:
        st.caption(f"{type_label} · {size_str}")
        st.caption(f"Modified: {modified_str}")
    with col_dl:
        try:
            file_bytes = entry["path"].read_bytes()
            st.download_button(
                label="Download",
                data=file_bytes,
                file_name=entry["name"],
                mime=MIME_MAP.get(suffix, "application/octet-stream"),
                key=str(entry["path"]),
                use_container_width=True,
            )
        except Exception as e:
            st.caption(f"Error: {e}")

    # Previews
    if suffix == ".png":
        with st.expander("Preview image", expanded=False):
            st.image(str(entry["path"]))
    elif suffix == ".csv":
        with st.expander("Preview data", expanded=False):
            try:
                import pandas as pd
                df = pd.read_csv(entry["path"])
                st.dataframe(df.head(50), use_container_width=True)
            except Exception as e:
                st.caption(f"Preview error: {e}")

    st.divider()
