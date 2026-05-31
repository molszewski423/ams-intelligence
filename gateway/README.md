# AMS Gateway

Public-facing portal for the AMS Intelligence platform - authenticated entry point with role-based access.

## Stack

- Python + Streamlit
- bcrypt authentication
- Containerized (Podman/Docker)

## Run

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
streamlit run src/app.py
```
