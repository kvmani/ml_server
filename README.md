# ML Server

A Flask and Celery based application for microstructural analysis.  The code is
packaged under `src/ml_server` so it can be imported as `ml_server` by other
Python applications.

## Quick start

```bash
python -m venv env
source env/bin/activate
pip install -r requirements.txt -r requirements-test.txt
```

Run the web server with Gunicorn:

```bash
gunicorn -c gunicorn.conf.py ml_server.app.microstructure_server:create_app()
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
overridden with environment variables using the `APP_` prefix. Common options:

```ini
APP_HOST=127.0.0.1
APP_PORT=5000
APP_DEBUG=true
APP_SECRET_KEY=change-me
APP_LOGGING__LOG_DIR=logs
APP_CELERY__BROKER_URL=redis://redis:6379/0
APP_CELERY__RESULT_BACKEND=redis://redis:6379/0
APP_SUPER_RESOLUTION__ML_MODEL__URL=http://localhost:5002/infer
APP_EBSD_CLEANUP__ML_MODEL__URL=http://localhost:5003/infer
APP_HYDRIDE_SEGMENTATION__ML_MODEL__URL=http://localhost:5004/infer
APP_FEEDBACK__FILE_PATH=src/ml_server/feedback.json
APP_SECURITY__ADMIN_TOKEN=changeme
APP_DOWNLOAD__PROCESSED_DATA_PATH=tmp/enhanced_ebsd_map.png
```
