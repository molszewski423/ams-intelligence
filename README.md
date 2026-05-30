# AMS Intelligence

**Antimicrobial Stewardship Research Pipeline**
Michael Olszewski, PharmD, BCPS, BCCCP

---

## Purpose

AMS Intelligence is a standalone, locally-executed research pipeline for antimicrobial stewardship pharmacovigilance. It combines FDA adverse event signal detection with real-world antibiotic utilization data to support formulary decision-making, resistance surveillance, and AMS program development.

All computation is local — no patient data, query inputs, or LLM prompts are sent to external servers.

---

## Modules

### Module 1 — Resistance Trend Analyzer

**What it does:**
Fetches FDA FAERS adverse event data for a primary antibiotic (default: cefazolin) and a comparator (default: cefpodoxime), computes disproportionality statistics (PRR and ROR), performs temporal pre/post analysis around a formulary-change year, integrates WHONET resistance surveillance rates and ATLAS MIC data, generates a local-LLM interpretation, and exports a one-page PDF findings summary.

**Key outputs:**
- PRR / ROR signal table with 95% confidence intervals (Evans criteria: PRR ≥ 2, N ≥ 3, chi² ≥ 4)
- Pre/post formulary-change PRR delta chart
- AMS-category adverse event breakdown (treatment failure, C. difficile, allergy, nephrotoxicity, resistance)
- WHONET %R trend (annual slope)
- ATLAS MIC50/MIC90 susceptibility timeline
- LLM-generated key findings and clinical interpretation paragraph
- One-page PDF summary for AMS committee distribution

**Use case example:**
Compare cefazolin (MSSA/surgical prophylaxis) vs cefpodoxime (oral step-down) to evaluate whether a formulary switch is associated with differential adverse event signals. Run pre/post 2020 split to assess COVID-era impact on antibiotic safety profiles.

---

### Module 2 — Antibiotic Utilization Signal Detector

**What it does:**
Loads NHSN Days of Therapy (DOT/1000 patient-days) data for a selected drug class, detects utilization anomalies relative to national benchmarks (spikes, sustained elevation), cross-references with FAERS adverse event signals for the same drug class, identifies correlations between utilization patterns and outcome signals (C. difficile, resistance, treatment failure), and generates a plain-language AMS committee summary.

**Key outputs:**
- DOT/1000 patient-days trend chart with benchmark overlay and anomaly shading
- Anomaly classification (spike, sustained high, low, normal) per quarter
- FAERS signal table for the drug class (Evans criteria)
- Correlation flags (e.g., "Utilization spike in 2021 coincides with C. difficile signal emergence")
- Anomaly score (0–1, composite of frequency and severity)
- LLM plain-language summary for AMS rounds or P&T committee

**Supported drug classes:**
Fluoroquinolones, carbapenems, vancomycin, 1st-gen cephalosporins, 3rd-gen cephalosporins, piperacillin/tazobactam, azithromycin, metronidazole, trimethoprim/sulfa

---

## Data Sources

| Source | Type | Access | AMS Use |
|---|---|---|---|
| **FAERS** | FDA adverse event reports | Live API (api.fda.gov) | Signal detection, PRR/ROR, temporal trends |
| **NHSN** | CDC antimicrobial use surveillance | CSV download (facility enrollment) | DOT/1000 patient-days benchmarking |
| **WHONET** | WHO global AMR surveillance | CSV download (public datasets) | %R trend by organism/antibiotic |
| **ATLAS** | Pfizer global MIC surveillance | CSV download (public dataset) | MIC50/MIC90, susceptibility %S over time |

NHSN, WHONET, and ATLAS fall back to realistic demo data when files are not present. Place downloaded files in:
- `data/nhsn/AU_FacilityWideInpatient_YYYY.csv`
- `data/whonet/WHONET_EXPORT_*.csv`
- `data/atlas/atlas_antibiotics.csv`

---

## Architecture

```
ams-intelligence/
├── src/
│   ├── config.py                    # Paths, model names, API URLs
│   ├── auth.py                      # Streamlit authentication (bcrypt + cookie)
│   ├── data_sources/
│   │   ├── faers_client.py          # OpenFDA API (live)
│   │   ├── nhsn_client.py           # NHSN CSV parser + demo data
│   │   ├── whonet_client.py         # WHONET CSV parser + demo data
│   │   └── atlas_client.py          # ATLAS CSV parser + demo data
│   ├── shared/
│   │   ├── disproportionality.py    # PRR, ROR, chi², Evans criteria
│   │   └── pdf_exporter.py          # fpdf2 one-page summary generator
│   ├── modules/
│   │   ├── resistance_analyzer.py   # Module 1 orchestration + LangChain LLM
│   │   └── utilization_detector.py  # Module 2 orchestration + LangChain LLM
│   └── dashboard/
│       ├── app.py                   # Streamlit home page
│       └── pages/
│           ├── 1_Resistance_Trends.py
│           └── 2_Utilization_Signals.py
├── vault/                           # AMS guidelines (ChromaDB ingestion target)
├── chroma_db/                       # Persistent vector store (auto-created)
├── output/                          # Generated PDF reports
├── data/                            # Placed downloaded data files here
│   ├── nhsn/
│   ├── whonet/
│   └── atlas/
├── scripts/
│   ├── start.sh
│   └── stop.sh
└── requirements.txt
```

---

## Technical Specifications

### Language Model Stack

| Model | Role | Context |
|---|---|---|
| `gemma4:26b` | Reasoning, signal interpretation, AMS summaries | 256K tokens, Thinking Mode |
| `qwen3:30b` | Coding tasks, structured data parsing | 32K tokens |
| `nomic-embed-text` | Vector embeddings for guideline RAG | Ollama |

LLM orchestration uses **LangChain Expression Language (LCEL)** with `ChatOllama` from `langchain-ollama`. All inference is local via Ollama at `http://127.0.0.1:11434`.

### Vector Storage

ChromaDB persistent store at `chroma_db/` (collection: `ams_vault`). Populated by ingesting AMS guidelines from `vault/Guidelines/`. Same ingestion pattern as PV Workbench — nomic-embed-text embeddings, header-aware chunking.

### Disproportionality Statistics

Both PRR and ROR are computed with 95% log-normal confidence intervals:

```
PRR = (a / (a+c)) / (b / (b+d))
ROR = (a × d) / (b × c)

SE(ln PRR) = √(1/a − 1/(a+c) + 1/b − 1/(b+d))
SE(ln ROR) = √(1/a + 1/b + 1/c + 1/d)
```

Evans criteria: PRR ≥ 2.0 AND N ≥ 3 AND chi² ≥ 4.0 (Yates-corrected, all three required).
Continuity correction (b = 0.5) applied when background count is zero.

### Authentication

`streamlit-authenticator 0.4.2` with bcrypt-hashed passwords. Cookie-based session persistence (30-day expiry). Same credentials as PV AI Workbench. OAuth providers configurable via `[auth]` section in secrets.toml.

### PDF Export

`fpdf2` with AMS green (#2E7D32) color scheme. One-page summary includes: KPI boxes, signal table (PRR/ROR/chi²), pre/post temporal comparison, key findings (LLM-generated), clinical interpretation, and regulatory disclaimer.

---

## Setup

```bash
# Create Python 3.11 virtual environment
python3.11 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Pull Ollama models (if not already available)
ollama pull gemma4:26b
ollama pull qwen3:30b
ollama pull nomic-embed-text

# Launch dashboard (port 8502)
PYTHONPATH=src streamlit run src/dashboard/app.py

# Or use the start script
bash scripts/start.sh
```

Default credentials: username `mike`, password `Sorento81!`

---

## Clinical Oversight

All outputs are research summaries and AI-generated drafts. They require:
- Senior pharmacist (PharmD) review before any formulary action
- Validation against patient-level data (FAERS is population-level, not individual cases)
- Cross-reference with institutional antibiogram and clinical guidelines
- P&T committee discussion for any policy recommendations

FAERS signals are hypotheses, not conclusions.

---

## Relationship to PV AI Workbench

AMS Intelligence is a standalone project sharing architectural patterns with PV AI Workbench (`~/pv-workbench`):
- Same auth module pattern (streamlit-authenticator 0.4.2)
- Same Ollama/LangChain LLM backend
- Same PRR/ROR disproportionality methodology (adapted from `fda_api_client.py`)
- Same fpdf2 PDF export approach

The two projects are independent repositories with separate ChromaDB stores, separate Streamlit ports (8501 vs 8502), and separate analytical focus (drug safety PV vs antimicrobial stewardship).
