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

## Follow-up: branch `claude/ams-cleanup-2` (owner-approved scope, unmerged)

- Deleted `docs/cluster-architecture.png` (old host names, three-node cluster; unreferenced).
- Deleted `gateway/assets/logos/`, and the now-failing `COPY assets/ ./assets/` line in `gateway/Containerfile`
  (nothing in `gateway/src/` reads `assets/` since the text names replaced the logos); README tree updated.
- `scripts/generate_linkedin_pdf.py` reworded by the README's rules: independent research prototype, public and
  synthetic data only, not affiliated, not used in patient care, no real institutional data (lines 349 and 486 to
  489, plus the overview, the design callout, the "patient data" KPI, the application lists and "zero PHI cloud
  exposure"); "Regulatory submission support" became research-use signal narratives, matching the gateway caption.
  Its em dash sanitizer now uses `\u2014`/`\u2013` escapes (same behavior, no literal em dash in the file).
- CI: `.gitlab-ci.yml` left unchanged. Its `build` job runs Docker-in-Docker, logs in to the GitLab registry and
  pushes `:<sha>` and `:latest` (the tag the k3s deployment pulls), so it is not lint-only. The README's CI section
  now says no pipeline runs on `master` as configured. Switching the rules to `master` is the owner's decision.
- Verified: `ruff check src/ gateway/src/ scripts/` passed; the PDF regenerated to a scratch path (5 pages) has no
  CoE mention, no em dash, no "real-world", "PHI cloud" or "regulatory submission support"; the edited files have no
  em dashes.

## Next step

Owner reviews and merges `claude/ams-cleanup-2`; decides whether GitLab CI should run on `master`.
