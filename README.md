# AMS Intelligence

Clinical AI platform for antimicrobial stewardship — tracks drug resistance trends, utilization signals, and adverse event data across public health databases.

## Data Sources

- **NHSN** — Healthcare-associated infection surveillance
- **FAERS** — FDA adverse event reporting
- **WHONET** — Global antimicrobial resistance data
- **PubMed** — Literature signal detection
- **ATLAS** — Pfizer global surveillance

## Stack

- Python + Streamlit dashboard
- ChromaDB vector store
- Containerized (Podman/Docker)

## Run

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# fill in credentials
bash scripts/start.sh
```
