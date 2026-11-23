# AGENTS.md — ML Server portal

`ml_server` is the Office Scientific Tools **portal and control surface**: the catalog-driven home
page, tool cards and scientific help, launch analytics, central feedback and its authenticated
administration console, portal health, release identity and metrics. Tools (PyTex,
HydrideSegmentation, OnlineAnnotator, PDF Tools, Tabular ML, calculator, converter) are owned by
their own repositories and are linked or mounted through stable boundaries. This file is the
operating contract for every coding agent (Codex, Claude, Gemini, …) and human contributor; it is
the only agent-instruction file in the repository.

**Order of authority:** the owner's instruction for the task → this file →
[docs/PLATFORM_VISION_AND_GOVERNANCE.md](docs/PLATFORM_VISION_AND_GOVERNANCE.md) (canonical
platform governance, policy 1.1) → [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) →
[CONTRIBUTING.md](CONTRIBUTING.md) → other docs.

## Cardinal rules (owner-mandated, every repository)

1. **Fetch before you change anything.** Start every task with
   `git fetch origin && git pull --rebase --autostash origin main`. Several people and agents push
   to this repository; never build on a stale checkout.
2. **Work on `main` only.** Commit and push directly to `main` unless the owner names another
   branch for the task. No feature branches or pull requests by default. Fetch again before
   pushing; if the push is rejected, `git pull --rebase origin main`, rerun the affected tests,
   then push. Never force-push or rewrite published history.
3. **Keep the progress ledger current:** [`docs/development/active_task_progress.md`](docs/development/active_task_progress.md). Before coding, add (or claim)
   the task entry: goal, plan, who is working on it, date. After each meaningful step record what
   was done, the commit, test evidence, decisions, blockers and the next step. Commit the ledger
   with the work it describes. A new session must be able to resume from the ledger and git
   history alone, without the chat that started the work.
4. **Targeted tests for ordinary changes.** Run only the tests that cover what you touched (see
   [Tests](#tests)). Run the full suite only when preparing a release or when the owner asks.
5. **CI runs only on request.** GitHub Actions workflows start by `workflow_dispatch` only;
   tag-triggered release workflows are the single exception. Never add push, pull-request or
   schedule triggers, and never start a workflow unless the owner asks.
6. **Be honest.** Never report a check as passed unless you ran it and saw it pass; record skipped
   checks and the reason. Never weaken, skip or delete a test to make it pass.
7. **Keep git clean.** Commit sources and canonical assets only: no secrets, real personal data,
   virtual environments, caches, logs or build output.

The cardinal rules decide *how work is done* (sync, branch, ledger, test scope, CI). The project
rules in this file decide *what this repository must achieve and protect*; nothing generic here
relaxes them. If a project rule and a cardinal rule genuinely conflict, stop and ask the owner.

## Platform governance (canonical copy lives here)

[docs/PLATFORM_VISION_AND_GOVERNANCE.md](docs/PLATFORM_VISION_AND_GOVERNANCE.md) governs the portal
and every member repository. Changing it is a deliberate platform decision: bump its policy
version, explain the change in `CHANGELOG.md`, and push to `main`. A goal that spans several
repositories keeps a coordinating ledger in `docs/development/` naming every affected repository,
its last pushed commit, its verification state and the next cross-repository action.

## Project rules

- **The portal owns only portal concerns** (governance §5.1). Never add scientific models,
  segmentation, diffraction, EBSD, PDF manipulation or other tool functionality here; change that
  in the owning repository. One capability has one owning repository (§3.3).
- **Tools stay standalone.** Integration (links, mounted blueprints) must never weaken a tool's
  independent operation (§3.5). Depend only on each tool's operational contract (§6): health,
  version, URL, limits — not its internals.
- **The catalog is data-driven** (`src/ml_server/catalog.py`): adding a card must not require
  editing the home-page template. Experimental and placeholder utilities are not catalogued.
- **Configuration, not constants.** Read settings through `ml_server.config.Config`
  (`config/config.intranet.json`, `APP_*` environment overrides, `ML_SERVER_CONFIG` for installed
  deployments). UI sizes such as `mainIconSize` and `toolsIconsSize` come from configuration.
- **Air-gapped and private.** Vendor every browser asset under `static/vendor/` (Bootstrap,
  Chart.js, MathJax, …); no CDN. Feedback copy states that no personal information is collected or
  stored; access logs never contain request bodies, secrets or feedback messages (§11).
- **Outbound calls** with `requests` always set a timeout and handle `RequestException`.
- **Observability:** new routes record metrics with `ml_server.app.services.metrics`; new admin
  pages are registered in `init_admin()`. Health: `/health/live` for liveness, `/health` also
  checks Redis and Celery and may report `degraded`.
- **No binary or model files** (`*.pkl`, `*.h5`, `*.pt`, …) or screenshots in git.
- **Releases:** set `__version__` in `src/ml_server/_version.py`, add a
  `## [X.Y.Z] - YYYY-MM-DD` section to `CHANGELOG.md`, push `main`, then start "Publish release"
  (`release.yml`) with `version = X.Y.Z` (a `vX.Y.Z` tag push also works). Suite procedure:
  `kvmani/ml_server_deploy` → `RELEASING.md`.

## Quality bar

- `black`, `isort` and `flake8` (max line length 100) pass on touched files; `pre-commit install`
  once per clone.
- Type hints and a concise docstring on every new function and public method.
- The smallest change that fully solves the task; no dead or commented-out code; tool-specific
  logic stays out of the portal.
- Every behaviour change ships with tests in the same commit, including denied and failure cases
  for admin, feedback and upload routes.
- User-visible changes update the relevant help (`tool_help.py`, `/help/faq`), README or docs and
  `CHANGELOG.md` (`Unreleased`) in the same commit.

## How to work

1. Sync (cardinal rule 1) and read the ledger; for cross-repository goals also read the
   coordinating ledger in `docs/development/`.
2. Use the [Map](#map) to read only what the task needs, then the code and its tests.
3. Record objective, scope, contracts touched, risks and verification plan in the ledger
   (governance §8.1). Implement in small verified steps; commit, push and update the ledger.

## Tests

```bash
pip install -r requirements.txt -r requirements-test.txt     # Python 3.12+
python -m pytest tests/test_<area>.py -q                      # targeted (ordinary changes)
python -m pytest --cov=src                                    # full suite (release or on request)
```

| You changed | Run |
| --- | --- |
| home page, catalog, tool links | `tests/test_home_route.py` |
| help pages, FAQ, MathJax | `tests/test_help_faq_route.py tests/test_help_mathematics.py` |
| health endpoints | `tests/test_health.py tests/test_health_disk.py` |
| admin console, auth, sessions | `tests/test_admin_dashboard.py tests/test_admin_session_csrf.py` |
| feedback | `tests/test_submit_feedback.py` |
| configuration, schema | `tests/test_config_load.py tests/test_config_schema.py tests/test_upload_config.py` |
| security headers | `tests/test_security_headers.py` |
| mounted PDF Tools / Tabular ML routes | `tests/test_pdf_tools_routes.py tests/test_tabular_ml_routes.py` |
| downloads, vendored assets | `tests/test_download_processed_data.py tests/test_production_assets.py` |

Shared or integration changes (health, version, catalog or feedback contracts; auth; uploads;
routing consumed by another repository) also need the relevant contract tests in the affected
repositories (governance §9.2).

## Definition of done

- [ ] Targeted tests pass and were run; lint clean on touched files.
- [ ] Help, docs and `CHANGELOG.md` updated for user-visible changes.
- [ ] No tool functionality added to the portal; no CDN or network dependency introduced.
- [ ] Ledger updated; committed and pushed to `main`.

## Map

| Need | Read |
| --- | --- |
| Platform vision, ownership, shared contracts, testing and release policy | [docs/PLATFORM_VISION_AND_GOVERNANCE.md](docs/PLATFORM_VISION_AND_GOVERNANCE.md) |
| Architecture and module interaction | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), [docs/WORKFLOW_OVERVIEW.md](docs/WORKFLOW_OVERVIEW.md) |
| Local development and running | [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md), [docs/HOW_TO_RUN.md](docs/HOW_TO_RUN.md) |
| Admin console | [docs/ADMIN_DASHBOARD.md](docs/ADMIN_DASHBOARD.md), [docs/admin_help.md](docs/admin_help.md) |
| Deployment (Ubuntu intranet, Docker, general) | [docs/DEPLOYMENT_UBUNTU_INTRANET.md](docs/DEPLOYMENT_UBUNTU_INTRANET.md), [docs/DEPLOYMENT_DOCKER.md](docs/DEPLOYMENT_DOCKER.md), [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) |
| Release manifest and rollback | [docs/PRODUCTION_RELEASE_2026_08.md](docs/PRODUCTION_RELEASE_2026_08.md) |
| Troubleshooting, Redis backup | [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md), [docs/REDIS_BACKUP.md](docs/REDIS_BACKUP.md) |
| OnlineAnnotator integration | [docs/development/online_annotator_integration.md](docs/development/online_annotator_integration.md) |
| Style, tooling, monitoring conventions | [CONTRIBUTING.md](CONTRIBUTING.md) |
| Current work and history | [docs/development/active_task_progress.md](docs/development/active_task_progress.md) |
