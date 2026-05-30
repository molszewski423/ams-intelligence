# AMS Intelligence

**Local-LLM antimicrobial stewardship platform · Program-agnostic · Clinician-built**

A production-grade clinical AI platform that pairs 20 years of critical care and infectious disease expertise with signal detection algorithms and RAG-powered guideline retrieval. Built by the pharmacist who led an organization to IDSA Antimicrobial Stewardship Center of Excellence designation — every AI output is reviewed by the clinician before any patient care or reporting use.

---

```mermaid
graph TB
    subgraph Sources[Surveillance Sources]
        NHSN[CDC NHSN]
        FAERS[FDA FAERS]
        WHONET[WHONET Global AMR]
        PUBMED[PubMed Literature]
        ATLAS[Pfizer ATLAS]
    end

    subgraph Vault[Knowledge Base]
        VAULTMD[Obsidian Vault Guidelines]
        Chunker[Markdown Chunker]
        Embed[nomic-embed-text Embeddings]
        ChromaDB[ChromaDB Vector Store]
    end

    subgraph Analysis[Analysis Modules]
        RES[Resistance Analyzer]
        UTIL[Utilization Detector PRR ROR]
    end

    subgraph LLM[LLM Layer via Ollama]
        OLLAMA[LangChain ChatOllama]
    end

    subgraph Output[Outputs]
        DASH[Streamlit Dashboard]
        PDF[PDF Reports]
        GW[Gateway Portal]
    end

    NHSN --> RES
    WHONET --> RES
    ATLAS --> RES
    FAERS --> UTIL
    NHSN --> UTIL
    PUBMED --> ChromaDB
    VAULTMD --> Chunker --> Embed --> ChromaDB
    ChromaDB --> OLLAMA
    RES --> DASH
    UTIL --> DASH
    OLLAMA --> DASH
    DASH --> PDF
    GW --> DASH

    subgraph HW[Hardware]
        GPU[RTX 5060 Ti 16GB]
    end
    LLM -.-> GPU
```

**Design principle:** Confounding by indication is explicitly modeled — last-resort antibiotics treat critically ill patients. Statistical signals are always interpreted in clinical context, not in isolation.

---

## The Problem This Solves

Antimicrobial stewardship programs face a daily data problem: resistance surveillance feeds from NHSN and WHONET, adverse event signals from FAERS, utilization trends, literature updates, and institutional formulary decisions — often managed manually across spreadsheets and disparate portals. Commercial platforms are expensive, cloud-dependent, and rarely designed by stewardship clinicians.

This platform brings the full AMS analytical workflow local, private, and clinician-controlled:
- Aggregate five surveillance databases into a unified signal detection pipeline
- Apply the same disproportionality methods used in pharmacovigilance (PRR/ROR) to antibiotic utilization data
- RAG over institutional guidelines, formulary docs, and stewardship policies via an Obsidian-compatible vault
- Generate PDF trend reports and LinkedIn-ready stewardship highlights
- All inference runs locally — no patient data leaves the machine

---

## System Architecture

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
gateway/
├── src/
│   ├── app.py                        # Authenticated portal entry point
│   └── auth.py                       # bcrypt + session management
└── assets/logos/                     # Regulatory agency logos
```

---

## Tech Stack

| Layer | Choice | Why |
|---|---|---|
| **LLM** | Ollama via LangChain `ChatOllama` | Local inference — no patient data in the cloud; GPU scheduling via Ollama |
| **Embeddings** | `nomic-embed-text` via Ollama | Local, no API key, strong retrieval on clinical text |
| **Vector Store** | ChromaDB (persistent, per-program collections) | Program isolation without separate servers |
| **Signal Detection** | NumPy + SciPy (PRR · ROR · Chi²) | Production-grade disproportionality matching pharmacovigilance standards |
| **Visualization** | Matplotlib + Seaborn | Resistance trend charts, utilization heat maps |
| **Dashboard** | Streamlit | Rapid iteration; runs locally, no frontend build step |
| **Surveillance APIs** | OpenFDA FAERS · CDC NHSN · PubMed Entrez | Standard APIs; FAERS uses quarterly partitioning to bypass 5000-result cap |
| **PDF Generation** | fpdf2 | Formatted resistance trend reports and stewardship summaries |
| **Auth** | streamlit-authenticator + bcrypt | Role-based access for clinical teams |
| **Container** | Podman / Docker (Containerfile) | Rootless Podman on homelab; Docker-compatible |
| **CI/CD** | GitLab CI | lint (ruff) + container build on every push to main |
| **Hardware** | RTX 5060 Ti · 16GB VRAM · 32GB RAM | All LLM inference local; no cloud dependency for core function |

---

## Spotlight: Utilization Signal Detection Pipeline

The utilization signal detection module applies pharmacovigilance-grade disproportionality analysis to antibiotic use data — the same statistical methods used in FDA FAERS signal detection, adapted for stewardship.

### What It Does

1. **Fetch** — Retrieves adverse event reports from OpenFDA using quarterly date-range partitioning. The FAERS API caps results at 5000 per search; partitioning into calendar quarters yields the complete dataset.

2. **Compute PRR** — Calculates Proportional Reporting Ratio against a configurable comparator antibiotic using the Evans criteria: **PRR ≥ 2.0 AND N ≥ 3 AND χ² ≥ 4.0**.

3. **Statistical rigor** — Three production-grade adjustments:
   - **Artifact exclusion**: Administrative FAERS PTs (`off label use`, `no adverse event`, `drug ineffective`) filtered before analysis
   - **Continuity correction**: b=0 reactions use b=0.5 instead of silent discard — preserves drug-specific signals
   - **Yates' χ² correction**: Applied when any expected cell count < 5, reducing false positives in sparse data

4. **Clinical interpretation** — LangChain + Ollama interprets all positive signals with confounding analysis, stewardship-specific context, and reviewer recommendations.

### PRR Formula

```
PRR = (a / (a+c)) / (b / (b+d))

           Drug    Comparator
Reaction     a          b
No Reaction  c          d

Signal if: PRR ≥ 2.0 AND a ≥ 3 AND χ² ≥ 4.0
```

### Clinically-Aware Design

Confounding by indication is the central challenge in AMS signal detection. Last-resort antibiotics (cefiderocol, colistin, ceftazidime-avibactam) are reserved for the sickest patients — high mortality signals in FAERS reflect the underlying infection, not the drug. The LLM interpretation layer is explicitly instructed to identify and weight this bias in every signal output.

---

## Three Dashboard Modules

| # | Module | What it does | Output |
|---|---|---|---|
| 1 | **Resistance Trends** | Tracks AMR patterns over time across organisms and drug classes from NHSN, WHONET, ATLAS | Trend charts, resistance rate tables |
| 2 | **Utilization Signals** | PRR/ROR disproportionality analysis on FAERS + NHSN utilization data | Signal table + LLM clinical interpretation |
| 3 | **Vault Browser** | Natural language querying of ingested clinical guidelines and formulary docs via RAG | Cited answers from institutional knowledge base |

---

## Program-Agnostic Design

Every module is parameterized by stewardship program, not hardcoded. Each program gets its own ChromaDB collection and vault folder:

```python
@dataclass
class ProgramConfig:
    program_name: str          # e.g. "community_hospital", "academic_medical_center"
    comparator: str            # FAERS background comparator antibiotic
    collection_name: str       # auto: ams_{program} — isolated ChromaDB collection
    vault_folder: str          # auto: Programs/{ProgramName} — per-program vault
    focus_organisms: list[str] # e.g. ["E. coli", "K. pneumoniae", "A. baumannii"]
    formulary_antibiotics: list[str]
```

Switching programs swaps all module contexts — resistance trend charts, signal detection comparators, vault retrieval — without code changes. The same platform serves a community hospital, academic medical center, or long-term care facility.

---

## Stewardship Knowledge Base

The RAG pipeline indexes structured markdown notes (Obsidian vault) covering AMS-specific content:

**Clinical Guidelines**
- IDSA Stewardship Guidelines — core stewardship program requirements
- ASHP Stewardship Resources — implementation tools, metrics
- CDC Core Elements — the seven core elements of hospital stewardship

**Antimicrobial Reference**
- Formulary antibiotic monographs
- Spectrum of activity tables
- PK/PD dosing principles for critical care

**Resistance**
- Resistance mechanism summaries by organism
- Local antibiogram interpretation notes
- Empiric therapy guidance by infection type

Notes use frontmatter `tags` and `source` fields. The ingester strips `[[wikilinks]]`, chunks by header hierarchy, and upserts idempotently using SHA-256 chunk IDs.

---

## Clinical Oversight Model

```
AI Output ──► is_draft=True ──► reviewer_flag=True ──► Stewardship Pharmacist Sign-off
                                                              │
                                                    PharmD · BCPS · BCCCP
                                                    20 years critical care / ID / AMS
                                                    IDSA AMS Center of Excellence
```

The platform never makes final clinical or formulary determinations. `is_draft` cannot be set to `False` by any module function — it is a design invariant, not a configuration option. Signal outputs inform stewardship decision-making; they do not replace it.

---

## Quick Start

### Local

```bash
git clone https://gitlab.com/molszewski423/ams-intelligence.git
cd ams-intelligence

python3 -m venv .venv && source .venv/bin/activate
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

### Vault Ingestion

```bash
# Place markdown files in vault/
python scripts/ingest_vault.py

# Query via the dashboard Files page
# or directly: PYTHONPATH=src python -c "from shared.vault_ingestor import query_vault; print(query_vault('carbapenem resistance'))"
```

### Report Generation

```bash
python scripts/generate_ams_slideshow.py   # PDF resistance trend report
python scripts/generate_linkedin_pdf.py    # LinkedIn stewardship summary
```

---

## Interfaces

### Streamlit Dashboard (Primary)

Runs locally at `localhost:8502`:

- **Program selector** — switch between stewardship programs; all modules update to reflect the active program
- **Resistance Trends** — AMR trend charts, organism resistance rates, drug class comparisons
- **Utilization Signals** — PRR signal table, Chi² values, LLM clinical interpretation with confounding analysis
- **Vault Browser** — natural language queries over ingested guidelines and formulary docs
- **PDF export** — resistance reports and stewardship summaries on demand

### Gateway Portal (Clinical Team Access)

The `gateway/` subdirectory contains an authenticated entry portal for clinical teams — ID physicians, infection control nurses, pharmacy staff. Role-based access controls which modules each user can reach.

```bash
cd gateway
streamlit run src/app.py --server.port 8500
```

---

## Technical Showcase

### Local-First Clinical AI

No patient data leaves the machine. All LLM inference runs on an RTX 5060 Ti 16GB, served by Ollama:

| Model | Role |
|---|---|
| Local LLM via Ollama | Signal interpretation, confounding analysis, guideline Q&A |
| `nomic-embed-text` | Vault embeddings (retrieval only) |

### Signal Detection

Statistical rigor matching pharmacovigilance standards:
- **PRR/ROR** using the 2×2 contingency table
- **Evans criteria**: PRR ≥ 2.0 AND N ≥ 3 AND χ² ≥ 4.0 — all three required simultaneously
- **Continuity correction**: b=0 reactions use b=0.5 — preserves novel drug-specific signals
- **Yates' χ² correction**: applied when any expected cell < 5
- **Artifact exclusion**: administrative FAERS PTs filtered before analysis
- **Quarterly pagination bypass**: `_fetch_quarter()` per calendar quarter overcomes 5000-result OpenFDA API cap

### Vector Database

ChromaDB with `nomic-embed-text` embeddings:
- **Header-aware chunking**: splits on H1/H2/H3 boundaries, not arbitrary character count
- **Idempotent ingestion**: SHA-256 chunk IDs; re-running is safe, changed notes update in place
- **Per-program isolation**: separate ChromaDB collections per stewardship program

### Infrastructure

- **OS**: Debian 13, Linux 6.12
- **GPU**: RTX 5060 Ti 16GB VRAM — inference
- **RAM**: 32GB — Ollama layer offloading for large models
- **Python**: 3.11 (venv) — chromadb wheels not available for 3.13

---

## How It's Built — Multi-AI Development Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                   Human Supervision                         │
│           PharmD · BCPS · BCCCP · 20 years                 │
│  Critical care · Infectious disease · AMS · IDSA CoE        │
└────────────┬──────────────┬──────────────────┬─────────────┘
             │              │                  │
    ┌────────▼─────┐ ┌──────▼──────┐  ┌───────▼────────┐
    │  Claude Code  │ │   Hermes    │  │  Local LLM     │
    │  (Architect)  │ │(Implementor)│  │  (Reasoner)    │
    │               │ │             │  │                │
    │ Architecture  │ │  Module     │  │ Clinical       │
    │ Task specs    │ │  implement- │  │ interpretation │
    │ Complex fixes │ │  ation      │  │ Signal analysis│
    │ Code review   │ │  Tool calls │  │ Guideline Q&A  │
    └───────────────┘ └─────────────┘  └────────────────┘
             │              │                  │
    ┌────────▼──────────────▼──────────────────▼─────────────┐
    │                   Shared Codebase                       │
    │           ~/ams-intelligence/  (this repo)              │
    └─────────────────────────────────────────────────────────┘
```

**Division of AI labor:**
- **Claude Code** (Anthropic): Architecture decisions, signal detection algorithm design, task spec authoring, code review. High-level thinking, broad context.
- **Hermes + Local LLM**: Module implementation from Claude's task specs. Autonomous implementation agent using the skill system.
- **Local LLM via Ollama**: Clinical reasoning at inference time — signal interpretation, confounding analysis, guideline Q&A. Not used in development, used in production.

---

## About

Built by a PharmD, BCPS, BCCCP with 20 years of critical care and infectious disease experience who led an organization to IDSA Antimicrobial Stewardship Center of Excellence designation. The statistical methods aren't bolted on — they're the same disproportionality algorithms used in pharmacovigilance, applied to stewardship data by someone who understands both sides.

**Stack philosophy:** Local-first. No cloud dependencies for core function. Data stays on-machine. The LLM reasoning layer runs on consumer hardware (RTX 5060 Ti 16GB) and is explicitly designed around the clinical realities of stewardship — confounding by indication, last-resort antibiotic populations, and the difference between a statistical signal and a clinical finding.

---

*All AI outputs are drafts. Clinical determinations require qualified stewardship pharmacist review.*
