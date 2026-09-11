# Coordinating ledger: Online Annotator integration (2026-09-11)

Cross-repository goal ledger required by `docs/PLATFORM_VISION_AND_GOVERNANCE.md` §3.1.
The detailed ledger of the tool itself is
`OnlineAnnotator/docs/development/active_task_progress.md`.

## Objective

Make Online Annotator (create, review and export segmentation ground truth) a first-class,
independently deployable member tool of the platform, linked from the portal like PyTex and
HydrideSegmentation.

## Repositories

| Repository | Change | State |
| --- | --- | --- |
| `OnlineAnnotator` (`kvmani/OnlineAnnotator`, public) | re-architected tool, health `/api/health`, `/help`, docs, CI | `main` pushed; tags `v1.0.0` (99e485e), `v1.0.1` (fe20215); GitHub Actions green |
| `ml_server` (this repo) | catalog card, scientific help + diagram, icon, privacy copy, local launchers | `main` 2e7b6e3 + 8f05d8b; tag `v1.3.0` |
| `ml_server_deploy` | component `annotator` (port 5070, `/api/health`, data in `shared/data/online_annotator`), rehearsal coverage, RUNBOOK | `main` 22e9f3f, 8d1f334, 6de553e; tag `v1.7.0` (suite release) |

## Contract

- Tool id `online-annotator`; catalog `href` from `ONLINE_ANNOTATOR_URL` (default `http://127.0.0.1:5070`).
- Health: `GET /api/health` → `{"status": "ok", "tool_id": "online-annotator", "version": "1.0.1"}`.
- Manual: `<href>/help` (redirects to the in-app Help centre).
- Persistence (governance §6): the tool deliberately stores uploads, label maps, versions,
  exports and an audit trail in its data directory; accounts hold office e-mail and name only.
- Limits: 200 MB per upload, 80 megapixels per image (configurable); lease 300 s.

## Verification

- `ml_server`: full suite 82 passed (+1 test for the card and help page); flake8/black clean on
  changed files; card and help page checked in a browser (diagram, 10 MathJax expressions, 0
  errors, manual link resolves). CI fails at pre-commit on pre-existing files (tracked separately).
- `OnlineAnnotator`: pytest 51, Node engine 8, Playwright journeys 6 — locally and in GitHub CI.
- `ml_server_deploy`: manifest validation, 62 unit tests, text hygiene; full deployment rehearsal
  28/28 scenarios under real systemd (WSL) with the annotator unit healthy; GitHub CI green.

## Outcome

**Complete (2026-09-12).** Suite release v1.7.0 built and published by GitHub Actions with every
gate green (manifest, hygiene, dependency gate with pip check and imports, reproducible assembly,
systemd rehearsal): https://github.com/kvmani/ml_server_deploy/releases/tag/v1.7.0
(`ml-server-suite-v1.7.0.tar.gz`, 64.8 MB, with `.sha256`). Office rollout:
download the v1.7.0 archive and run `./update.sh` (see ml_server_deploy RUNBOOK, section
"Online Annotator (new in suite 1.7.0)"). Rollback: the previous suite release.
