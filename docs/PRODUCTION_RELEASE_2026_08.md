# Scientific Tools Platform Production Release

Release date: 2026-08-23

This document is the coordinated deployment, verification, and rollback runbook for the portal
and all six scientific tools. Each tool remains independently deployable; the portal is the
common discovery surface and mounts PDF Tools and Tabular ML directly.

## Release manifest

| Component | Version | Default URL | Health/readiness | Scientific help |
| --- | ---: | --- | --- | --- |
| ML Server portal | 1.0.0 | `http://127.0.0.1:5000/` | `/health/live`, `/health` | `/help/faq` and `/tools/<id>/help` |
| Hydride Segmentation | 1.0.1 | `http://127.0.0.1:5005/` | `/health` | `/help` |
| PyTex | 0.2.0 | `http://127.0.0.1:8765/` | `/api/health` | Help workspace and documentation site |
| PDF Tools | 0.2.0 | `/pdf_tools/` or port 5045 | `/pdf_tools/health` | `/pdf_tools/help` |
| Tabular ML | 0.2.0 | `/tabular_ml/` or port 5070 | `/tabular_ml/api/v1/health` | `/tabular_ml/help` |
| Scientific Calculator | 0.3.0 | `http://127.0.0.1:5055/` | `/api/health` | `/help` |
| Unit Converter | 0.2.0 | `http://127.0.0.1:5065/` | `/api/health` | `/help` |

The versions above are the release unit. Create signed or annotated `v<version>` tags only after
the gates below pass. The portal dependency file deliberately resolves PDF Tools and Tabular ML
from those immutable tags.

## Host preparation

Use Python 3.12 or newer, Redis 7, a dedicated unprivileged service account, and TLS termination
at an intranet reverse proxy. Install Poppler for PDF raster preview. Create a separate virtual
environment per independently hosted tool so numerical dependencies cannot contaminate one
another. Restrict all service ports to loopback; expose only the reverse proxy.

Before first start:

1. Copy `config/config.intranet.json` outside the release directory and replace every
   `__SET_*__` value with a secret from the deployment secret store.
   Set `ML_SERVER_CONFIG` to that absolute file path; an installed wheel otherwise uses its
   safe, non-debug packaged defaults.
   For Compose deployments, copy `.env.example` to the untracked `.env` file expected by the
   compose definition and set the same values there.
2. Set `APP_DEBUG=false`, a stable `APP_SECRET_KEY`, a non-default `APP_ADMIN_TOKEN`, Redis URLs,
   and the external tool URLs. Never commit the populated file or SMTP password.
3. Give the service account write access only to `data/`, `logs/`, `tmp/`, and the explicitly
   configured upload/output locations. Back up `data/engagement.sqlite3` before portal upgrades.
4. Set reverse-proxy request limits consistently with each application's own limit and preserve
   `/pdf_tools` and `/tabular_ml` path prefixes.

## Build immutable artifacts

From each repository, run its test gates and then `python -m build`. Record the Git commit and
SHA-256 of every wheel in the deployment ticket. Publish/tag in dependency order:

The hashes of the locally verified artifacts are recorded in `RELEASE_SHA256_2026_08.txt`.
Recompute and replace that manifest if any artifact is rebuilt; a changed hash is a different
release artifact even when its version is unchanged.

1. `pdf_tools` 0.2.0 and `tabular_ml` 0.2.0;
2. PyTex 0.2.0, Scientific Calculator 0.3.0, Unit Converter 0.2.0, and Hydride Segmentation 1.0.1;
3. `ml_server` 1.0.0 after its tagged companion URLs resolve.

Install artifacts into new versioned virtual environments; do not upgrade the live environment
in place. The portal can then be installed with `pip install --require-hashes` from an internally
mirrored, locked requirements file derived from this release.

For the container route, keep the populated environment file outside the image context when
possible and select it explicitly:

```bash
export ML_SERVER_ENV_FILE=/etc/ml-server/production.env
docker compose config --quiet
docker compose build --pull
docker compose up -d
```

The checked-in `.dockerignore` excludes local secrets, environments, logs, data, test output, and
build artifacts. Compose binds the portal only to host loopback; the TLS reverse proxy is the
network entry point.

## Start commands

The small Flask services ship Waitress entry points for portable production use. On Linux, the
portal may use Gunicorn as shown below; set working directories to the corresponding release.

```bash
gunicorn --bind 127.0.0.1:5000 --workers 2 --timeout 300 'ml_server.app.server:create_app()'
tabular-ml --host 127.0.0.1 --port 5070
pdf-tools --host 127.0.0.1 --port 5045
scientific-calculator --host 127.0.0.1 --port 5055
unit-converter --host 127.0.0.1 --port 5065
python -m pytex.app serve --host 127.0.0.1 --port 8765
python scripts/run_web_server.py --host 127.0.0.1 --port 5005 --no-preload
```

Run Redis, the portal, and its Celery worker/beat as separately supervised services with restart
on failure and journald or structured log collection. Do not enable Flask debug mode or the
Werkzeug reloader in production.

## Blue-green deployment

1. Install the new wheels into a new release directory and virtual environments.
2. Start every component on temporary loopback ports.
3. Verify liveness, component readiness, the portal catalog, all six scientific-help pages, a
   representative calculation/conversion, a two-page PDF merge, a Tabular ML demo-dataset load,
   a PyTex example, and a Hydride practice image.
4. Confirm SVG diagrams and application assets return 200 without browser console errors.
5. Switch the reverse proxy atomically, observe logs/latency/error rate, then drain the old
   processes. Retain the preceding release until the observation window closes.

`/health/live` proves that the portal process can serve requests. `/health` is dependency-aware
and may return `degraded`; use it for readiness and alerting, not for an automatic restart loop.

## Rollback

Switch the proxy back to the previous port set, then stop the new services. Reinstalling an old
wheel is unnecessary when versioned environments are retained. Restore the engagement database
only if the release performed a data migration (this release does not). PDF Tools, Tabular ML,
Scientific Calculator, and Unit Converter keep no persistent user workload, so rollback has no
application-data migration. Preserve failed-release logs and artifact hashes for diagnosis.

## Release acceptance checklist

- All repository tests, static checks, frontend builds, and wheel builds pass.
- `docker compose config` succeeds on the deployment host before any image is built.
- Wheels install into clean virtual environments and their console entry points start.
- The version reported by metadata/health matches the manifest.
- Default configuration has debug disabled and contains no deployed secret.
- All tool cards expose descriptive hover/focus details and separate launch/help actions.
- Every help page documents workflow, equations/algorithm, critical inputs, interpretation, and
  limitations, with an accessible SVG workflow diagram.
- Reverse-proxy, backup, monitoring, and rollback rehearsals are recorded in the deployment ticket.
