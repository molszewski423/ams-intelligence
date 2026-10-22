# Handoff: independence and public-file cleanup

Agent: Claude Code. Date: 2026-10-22. Branch: `claude/ams-independence-cleanup`.

## Done

- README and slide-deck generator reworded: research prototype; public and synthetic data only; developed
  independently; not affiliated with or endorsed by any institution; not used in patient care. The IDSA Antimicrobial
  Stewardship Center of Excellence designation removed everywhere. The antibiogram slide is marked Planned, with
  invented example data (no antibiogram upload is implemented in `src/` or `gateway/`).
- README infrastructure in role names and placeholders: node1 (k3s agent, GPU, Ollama host service), node2 (k3s
  server); `<infra-repo>`, `<ams-host>`; no LAN IP, host names, internal domains or login hint. The old
  "mikepc control plane" statement corrected; the cluster diagram is now a Mermaid block; status stated as scaled
  to zero.
- `gateway/src/app.py`: organization logos replaced by text names, with a no-endorsement caption.
- No em dashes left in `README.md` or `scripts/generate_ams_slideshow.py`.

## Verified, and how

- `ruff check src/ gateway/src/ scripts/` (ruff 0.17.1, repository `ruff.toml`): passed. `py_compile` on both edited
  Python files.
- The deck generated to a scratch path (11 slides); its text has no CoE mention and no em dash.
- Cluster facts read with kubectl, read-only: deployment `ams-intelligence` 0/0, `ollama` Service backed by an
  `ollama-proxy` pod.

## Open (owner)

- `docs/cluster-architecture.png` still shows the old host names and a three-node cluster. It is no longer
  referenced by the README; delete it or leave it (history keeps it either way).
- `gateway/assets/logos/` is now unused; delete or keep.
- `scripts/generate_linkedin_pdf.py` still says demo data is used "when real institutional data files are absent"
  (line 349) and that modules "reflect real-world AMS workflows" (lines 486 to 489); not changed here.
- `.gitlab-ci.yml` runs only on branch `main`; this repository uses `master`, so the README's "every push to
  master triggers GitLab CI" is not true as configured.
- No deck or LinkedIn PDF exports are committed (`output/` is ignored); any copies shared elsewhere carry the
  old wording.

## Merge

Merged into `master` on 2026-10-22 by Claude Code, with a signed merge commit (no fast-forward), on the
owner's explicit, one-time authorization for this branch only; the owner-merges rule is otherwise unchanged.
`master` had not moved since the branch point (6fc0d2a). The branch was then deleted on Gitea.

## Next step

Owner decides the open items above.
