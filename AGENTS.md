# ams-intelligence: agent instructions

Read the global agent instructions first: `~/.claude/CLAUDE.md` (Claude Code) or `~/.codex/AGENTS.md` (Codex),
both linked to `context/global/AGENTS.md` in the private claude-memory repo. They cover conventions, approvals and
the session protocol (branches `<agent>/<topic>`, signed commits with an `Agent:` trailer, handoff notes). This file
adds what is specific to this repository; where it is stricter, it wins.

## What this is

AMS Intelligence, a local-LLM antimicrobial stewardship platform (Python, Streamlit, RAG over a guideline vault),
deployed as a k3s workload in the `ai` namespace (manifests in homelab-infra). See `README.md`.

## Rules for this repository

- **Public on Gitea.** No PHI, ever; synthetic or public data only. No real IPs or credential locations in new text.
- Keep it distinct from the LocumView clinical AI module (ADR 0017 in locumview) and from the owner's clinical day
  job; do not name the employer.
- Lint with `ruff` (`ruff.toml`).
