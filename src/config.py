"""AMS Intelligence — Central configuration."""

import os
from pathlib import Path

ROOT        = Path(__file__).parent.parent
SRC         = Path(__file__).parent
DATA_DIR    = ROOT / "data"
OUTPUT_DIR  = ROOT / "output"
VAULT_DIR   = ROOT / "vault"
CHROMA_PATH = ROOT / "chroma_db"

for _d in (OUTPUT_DIR, DATA_DIR / "nhsn", DATA_DIR / "whonet", DATA_DIR / "atlas"):
    _d.mkdir(parents=True, exist_ok=True)

# ── Ollama ────────────────────────────────────────────────────────────────────
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
REASON_MODEL    = "gemma4:26b"    # Signal analysis, interpretation, regulatory Q&A
CODE_MODEL      = "qwen3:30b"     # Pipeline tasks, structured output, data parsing
EMBED_MODEL     = "nomic-embed-text"

# ── ChromaDB ──────────────────────────────────────────────────────────────────
COLLECTION_NAME = "ams_vault"

# ── FAERS API ─────────────────────────────────────────────────────────────────
FAERS_API_URL   = "https://api.fda.gov/drug/event.json"
FAERS_API_KEY   = ""   # Optional — paste key here to lift rate limits
FAERS_START_YEAR = 2004

# ── NCBI / PubMed ─────────────────────────────────────────────────────────────
NCBI_API_KEY    = ""   # Optional — paste key here for 10 req/s (vs 3 req/s)
