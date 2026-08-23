# ML Server

A Flask and Celery based application for microstructural analysis.  The code is
packaged under `src/ml_server` so it can be imported as `ml_server` by other
Python applications.

## Quick start

```bash
python -m venv env
source env/bin/activate
pip install -r requirements.txt -r requirements-test.txt
pre-commit install
```

Run the web server with Gunicorn:

```bash
gunicorn -w 2 -b 0.0.0.0:5000 ml_server.app.server:create_app()
```

Start a Celery worker:

```bash
celery -A ml_server.celery_app worker
```

## Health check

With the services running you should get a JSON status from:

```bash
curl http://localhost:5000/health
```

Use `/health/live` for process liveness; `/health` also checks Redis and Celery and can report
`degraded` while the web process itself remains healthy.

Hydride Segmentation is provided by the well-tested standalone repository at
`C:\Users\kvman\HydrideSegmentation` and is linked from the portal at its own
service URL. The portal does not contain a duplicate segmentation
implementation.

Every catalog card has a separate **Scientific help** action. The central `/help/faq` index and
`/tools/<tool-id>/help` guides document workflows, mathematical core, critical inputs, result
interpretation, and limitations with accessible SVG diagrams.

## PDF Tools

Navigate to `/pdf_tools/` for secure PDF utilities. The page offers merging of
multiple PDFs and extraction of specific page ranges. All operations run within
the intranet and no files are stored on disk, ensuring privacy.

## Tabular ML Workbench

Navigate to `/tabular_ml/` for the integrated visual machine-learning
workbench. It profiles CSV and Excel tables, makes preprocessing and outlier
choices explicit, compares CPU-only classification and regression algorithms,
renders configurable validation figures, and runs in-session inference. Six
licensed public datasets are included for guided exploration.

The owning repository remains independently runnable at
`C:\Users\kvman\PycharmProjects\tabular_ml`. The portal installs its stable
companion package and mounts the same `/tabular_ml/*` blueprint contract; no
training logic is duplicated here.

## Admin Dashboard and Monitoring

Access the admin interface at `/admin?token=<ADMIN_TOKEN>`. The page now
features a cleaner card layout and a bar chart visualising recent endpoint
visits. Service health badges quickly indicate the status of background
processes while logs and Prometheus metrics remain available in scrollable
sections. These updates make it easier to monitor uptime, active users and
system health at a glance.

Feedback, feature requests, IP/session activity, tool launches, session
duration, and request timings are persisted in `data/engagement.sqlite3` and
shown only in the token-protected admin views. The homepage tells users what is
collected. Set `APP_ANALYTICS__ENABLED=false` to disable new analytics writes.

Feedback email is optional and disabled by default. To use an internal relay,
set `APP_EMAIL__ENABLED=true`, `APP_EMAIL__SMTP_HOST`, and the related values in
`.env`. The relay may be unauthenticated (leave username/password empty) or use
TLS/authentication. SMTP runs after the database commit in a background thread;
a relay failure is recorded in the submission but never loses the message.

Prometheus metrics continue to be exposed at `/metrics` for integration with
external monitoring systems.

## Repository layout

```
ml_server/
  src/ml_server/        - Python package
    app/                - Flask application and routes
    celery_app.py       - Celery tasks and worker entrypoint
    config.py           - Configuration loader
    static/             - Static assets served by Flask
    templates/          - Jinja2 templates
```

Configuration for the intranet environment is stored in
`config/config.intranet.json` and can be overridden with environment variables
using the `APP_` prefix. Installed-wheel deployments should set `ML_SERVER_CONFIG` to the
absolute path of their protected configuration file.

### UI configuration

Two keys control the size of icons displayed on the site:

```
"mainIconSize": [100, 100]   # size of the logo on the homepage
"toolsIconsSize": [75, 75]   # size of icons for individual tools
```

These values also control the logo in the navigation bar. Override them with the
environment variables `APP_MAINICONSIZE` and `APP_TOOLSICONSSIZE` using JSON
arrays like `[120,120]`.

## Development

Install development and testing requirements:

```bash
pip install -r requirements.txt -r requirements-test.txt
```

For the complete local platform, use the setup helper so the companion PDF
Tools and Tabular ML repositories are installed from their local owner
repositories:

```powershell
.\scripts\setup_local.ps1
.\start_platform.ps1
```

## Standalone and integrated operation

The portal is an optional common intranet gateway. Every linked tool remains an independently
deployable web application with its own environment, startup command, health check, tests, and
deployment documentation. A user may run only one tool without deploying the full platform; the
portal adds discovery and integration but is not a prerequisite for the companion repositories.

Run the unit tests with:

```bash
python -m pytest
```

Portal development now requires Python 3.12 or newer because the Tabular ML
companion uses the current scientific Python stack. Tabular ML is CPU-only and
does not install a GPU runtime.

See `docs/DEPLOYMENT_UBUNTU_INTRANET.md` for the office-intranet Ubuntu runbook (local Python/npm
mirrors, CPU-only packages, offline MathJax verification, privacy guarantees),
`docs/DEPLOYMENT.md` for the general deployment instructions, and
`docs/PRODUCTION_RELEASE_2026_08.md` for the coordinated version manifest, verification matrix,
blue-green procedure, and rollback plan. `docs/WORKFLOW_OVERVIEW.md` explains how the modules
interact.

## Contributing

Pull requests are welcome! Please follow these guidelines:

1. Run `pre-commit install` after cloning to enable linting hooks.
2. Ensure `flake8`, `black` and `isort` pass before committing.
3. Add unit tests for new functionality and run `pytest`.
4. Include docstrings for all public functions and keep lines under 100 characters.

## Environment Variables

Configuration values are loaded from `config/config.intranet.json` and can be
overridden with environment variables using the `APP_` prefix. Key options are
listed below. Nested keys use `__` to separate levels.

```ini
APP_HOST=127.0.0.1
APP_PORT=5000
APP_DEBUG=false
APP_SECRET_KEY=change-me
APP_LOGGING__LOG_DIR=logs
APP_LOGGING__LOG_FILE=app.log
APP_LOGGING__FORMAT="%(asctime)s [%(levelname)s] %(message)s"
APP_CELERY__BROKER_URL=redis://redis:6379/0
APP_CELERY__RESULT_BACKEND=redis://redis:6379/0
APP_FEEDBACK__DATABASE_PATH=data/engagement.sqlite3
APP_ANALYTICS__ENABLED=true
APP_EMAIL__ENABLED=false
APP_EMAIL__SMTP_HOST=
APP_EMAIL__SMTP_PORT=25
APP_EMAIL__USE_TLS=false
APP_EMAIL__FROM_ADDRESS=noreply@intranet.local
APP_EMAIL__DEVELOPER_ADDRESS=kvmani@barc.gov.in
APP_DOWNLOAD__PROCESSED_DATA_PATH=tmp/processed_data.bin
APP_SECURITY__ADMIN_TOKEN=__SET_ADMIN_TOKEN__
APP_SECURITY__ALLOWED_ORIGINS="[http://localhost:5000]"
APP_SECURITY__CSRF_ENABLED=true
APP_SECURITY__SSL_ENABLED=false
APP_MAINICONSIZE="[100,100]"
APP_TOOLSICONSSIZE="[75,75]"
```

**Important:** The `APP_SECRET_KEY` and `APP_SECURITY__ADMIN_TOKEN` values must be
set to secure, unique strings before running the application in production.

### Prometheus Setup

Metrics are available at `http://<host>:5000/metrics`. Configure Prometheus to
scrape this endpoint:

```yaml
scrape_configs:
  - job_name: ml_server
    static_configs:
      - targets: ['localhost:5000']
```
