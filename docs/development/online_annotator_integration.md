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
| `OnlineAnnotator` (`kvmani/OnlineAnnotator`) | re-architected tool, v1.0.0, health `/api/health`, `/help`, docs | committed locally; GitHub repository creation awaiting owner approval |
| `ml_server` (this repo) | catalog card, scientific help + diagram, icon, privacy copy, local launchers, v1.3.0 | this commit |
| `ml_server_deploy` | component `annotator` (port 5070, health `/api/health`, data in `shared/data/online_annotator`) | pending — needs the `v1.0.0` tag of OnlineAnnotator on GitHub |

## Contract

- Tool id `online-annotator`; catalog `href` from `ONLINE_ANNOTATOR_URL` (default `http://127.0.0.1:5070`).
- Health: `GET /api/health` → `{"status": "ok", "tool_id": "online-annotator", "version": "1.0.0"}`.
- Manual: `<href>/help` (redirects to the in-app Help centre).
- Persistence (governance §6): the tool deliberately stores uploads, label maps, versions,
  exports and an audit trail in its data directory; accounts hold office e-mail and name only.
- Limits: 200 MB per upload, 80 megapixels per image (configurable); lease 300 s.

## Verification

- `ml_server`: full suite 82 passed (+1 new test for the card and help page); flake8 clean on
  changed files; card and help page checked in a browser (diagram loads, 10 MathJax
  expressions, 0 errors, manual link resolves to the running tool).
- `OnlineAnnotator`: pytest 51 passed, Node engine tests 8 passed, Playwright journeys 6 passed.

## Next actions

1. Owner creates or approves creation of `github.com/kvmani/OnlineAnnotator`; push `main` and tag `v1.0.0`.
2. Add the `annotator` component to `ml_server_deploy/manifest.yml`, bump the suite version,
   set `ml_server` ref to `v1.3.0`, and cut a suite release per its README.
