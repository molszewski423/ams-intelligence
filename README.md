# AMS Intelligence

Clinical AI platform for antimicrobial stewardship programs. Aggregates surveillance data from five public health databases, detects resistance trends and adverse drug event signals, and generates PDF reports for clinical teams.

Built by a pharmacist who led an organization to IDSA Antimicrobial Stewardship Center of Excellence designation — for pharmacists, ID physicians, and infection control teams who need signal detection across heterogeneous data sources without building a data pipeline from scratch.

---

## Features

**Resistance Trends Dashboard**
- Tracks antimicrobial resistance patterns over time across organisms and drug classes
- Pulls from NHSN (HAI surveillance), WHONET (global AMR), and ATLAS (Pfizer global surveillance)
- Visualizes resistance rates with matplotlib/seaborn

**Utilization Signals Dashboard**
- Detects anomalous antibiotic utilization patterns using disproportionality analysis
- Implements PRR (Proportional Reporting Ratio) and ROR (Reporting Odds Ratio) — standard pharmacovigilance signal detection methods applied to stewardship data
- Sources: FAERS (FDA adverse event reporting), NHSN utilization data

**RAG Knowledge Base**
- Ingest clinical guidelines, formulary docs, and institutional policies via Obsidian-compatible vault
- ChromaDB vector store with LangChain orchestration
- Ollama LLM integration for natural language querying of ingested documents

**PDF Report Generation**
- Export resistance trend reports and utilization signal summaries as formatted PDFs
- LinkedIn-ready slide generation for sharing findings

**Authentication**
- bcrypt credential store
- Role-based access (clinicians vs. admin)
- Streamlit-authenticator with cookie-based sessions

---

## Architecture

```
src/
├── dashboard/
│   ├── app.py                        # Entry point, auth gate
│   └── pages/
│       ├── 1_Resistance_Trends.py    # AMR trend visualization
│       ├── 2_Utilization_Signals.py  # Disproportionality analysis
│       └── 3_Files.py                # Vault document browser
├── data_sources/
│   ├── nhsn_client.py                # CDC NHSN API
│   ├── faers_client.py               # FDA FAERS API
│   ├── whonet_client.py              # WHONET data ingestion
│   ├── pubmed_client.py              # PubMed literature search
│   └── atlas_client.py               # Pfizer ATLAS surveillance
├── modules/
│   ├── resistance_analyzer.py        # Trend detection logic
│   └── utilization_detector.py       # PRR/ROR signal detection
└── shared/
    ├── disproportionality.py         # Signal detection algorithms
    ├── pdf_exporter.py               # Report generation (fpdf2)
    └── vault_ingestor.py             # Markdown → ChromaDB pipeline
```

---

## Data Sources

| Source | Type | What it provides |
|---|---|---|
| **NHSN** | CDC surveillance | Healthcare-associated infections, device utilization, antibiotic use rates |
| **FAERS** | FDA reporting | Adverse drug events — used for PRR/ROR signal detection |
| **WHONET** | Global AMR | Organism-level resistance data from labs worldwide |
| **PubMed** | Literature | Signal validation against published clinical evidence |
| **ATLAS** | Pfizer global | Commercial antimicrobial surveillance across 70+ countries |

---

## Stack

| Layer | Technology |
|---|---|
| Dashboard | Python 3.11 + Streamlit |
| Signal detection | NumPy + SciPy + pandas |
| Visualization | Matplotlib + Seaborn |
| RAG / LLM | LangChain + ChromaDB + Ollama |
| PDF reports | fpdf2 |
| Auth | streamlit-authenticator + bcrypt |
| Container | Podman / Docker (Containerfile) |
| CI/CD | GitLab CI — lint (ruff) + container build |

---

## Setup

### Local

```bash
git clone https://gitlab.com/molszewski423/ams-intelligence.git
cd ams-intelligence

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edit secrets.toml — add credentials and cookie key

bash scripts/start.sh
# Dashboard available at http://localhost:8502
```

### Container (Podman/Docker)

```bash
podman build -f Containerfile -t ams-intelligence:latest .
podman run -d \
  -p 8502:8502 \
  -v ./vault:/app/vault:Z \
  -v ./.streamlit/secrets.toml:/app/.streamlit/secrets.toml:Z \
  ams-intelligence:latest
```

---

## Vault Ingestion (RAG Knowledge Base)

Ingest clinical guidelines, policies, or formulary documents:

```bash
# Place markdown files in vault/
# Run ingestion pipeline
python scripts/ingest_vault.py

# Query via the dashboard Files page
# or directly via LangChain + Ollama
```

Compatible with Obsidian vaults — frontmatter is parsed and stored as ChromaDB metadata.

---

## Report Generation

```bash
# Generate PDF resistance trend report
python scripts/generate_ams_slideshow.py

# Generate LinkedIn-format summary
python scripts/generate_linkedin_pdf.py
```

---

## CI/CD

GitLab CI pipeline on every push to `main`:
- **lint** — ruff static analysis
- **build** — container image built and pushed to GitLab Container Registry

---

## Related

- [ams-gateway](https://gitlab.com/molszewski423/ams-gateway) — authenticated entry portal for this platform
