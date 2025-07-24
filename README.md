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

The hydride segmentation tool is available at `/hydride_segmentation`.
Upload an image and choose either the ML or conventional algorithm. Results
include the segmentation mask, overlay and orientation analysis.

## PDF Tools

Navigate to `/pdf_tools` for secure PDF utilities. The page offers merging of
multiple PDFs and extraction of specific page ranges. All operations run within
the intranet and no files are stored on disk, ensuring privacy.

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
using the `APP_` prefix.

## Development

Install development and testing requirements:

```bash
pip install -r requirements.txt -r requirements-test.txt
```

Run the unit tests with:

```bash
python -m pytest
```

See `docs/DEPLOYMENT.md` for deployment instructions and
`docs/WORKFLOW_OVERVIEW.md` for an overview of how the modules interact.

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
APP_DEBUG=true
APP_SECRET_KEY=change-me
APP_LOGGING__LOG_DIR=logs
APP_LOGGING__LOG_FILE=app.log
APP_LOGGING__FORMAT="%(asctime)s [%(levelname)s] %(message)s"
APP_CELERY__BROKER_URL=redis://redis:6379/0
APP_CELERY__RESULT_BACKEND=redis://redis:6379/0
APP_SUPER_RESOLUTION__ML_MODEL__URL=http://localhost:5002/infer
APP_SUPER_RESOLUTION__ML_MODEL__HEALTH_URL=http://localhost:5002
APP_SUPER_RESOLUTION__ML_MODEL__PORT=5002
APP_SUPER_RESOLUTION__ML_MODEL__TIMEOUT=30
APP_SUPER_RESOLUTION__IMAGE_SETTINGS__MAX_SIZE=10485760
APP_SUPER_RESOLUTION__IMAGE_SETTINGS__MIN_DIMENSIONS="[100,100]"
APP_SUPER_RESOLUTION__IMAGE_SETTINGS__MAX_DIMENSIONS="[4096,4096]"
APP_EBSD_CLEANUP__ML_MODEL__URL=http://localhost:5003/infer
APP_EBSD_CLEANUP__ML_MODEL__HEALTH_URL=http://localhost:5003
APP_EBSD_CLEANUP__ML_MODEL__PORT=5003
APP_EBSD_CLEANUP__ML_MODEL__TIMEOUT=30
APP_EBSD_CLEANUP__FILE_SETTINGS__MAX_SIZE=52428800
APP_HYDRIDE_SEGMENTATION__ML_MODEL__URL=http://localhost:5004/infer
APP_HYDRIDE_SEGMENTATION__ML_MODEL__HEALTH_URL=http://localhost:5004
APP_HYDRIDE_SEGMENTATION__ML_MODEL__PORT=5004
APP_HYDRIDE_SEGMENTATION__ML_MODEL__TIMEOUT=30
APP_FEEDBACK__FILE_PATH=src/ml_server/feedback.json
APP_DOWNLOAD__PROCESSED_DATA_PATH=tmp/enhanced_ebsd_map.png
APP_SECURITY__ADMIN_TOKEN=__SET_ADMIN_TOKEN__
APP_SECURITY__ALLOWED_ORIGINS="[http://localhost:5000]"
APP_SECURITY__CSRF_ENABLED=true
APP_SECURITY__SSL_ENABLED=false
```

**Important:** The `APP_SECRET_KEY` and `APP_SECURITY__ADMIN_TOKEN` values must be
set to secure, unique strings before running the application in production.
