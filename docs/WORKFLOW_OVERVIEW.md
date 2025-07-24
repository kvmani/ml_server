# Workflow Overview

The Flask application lives in `ml_server.app.server` and exposes
several routes for file processing. Heavy operations are delegated to Celery
workers communicating through Redis queues.

## Request lifecycle

1. A browser sends a request to an endpoint such as `/super_resolution`.
2. `create_app()` registers blueprints found under `ml_server.app.routes`.
3. For long running tasks (e.g. EBSD clean up) a Celery task defined in
   `ml_server.celery_app` is queued.
4. Celery workers process the job and store results back in Redis.
5. The Flask route polls for the result and returns it to the user.

## Modules

- **ml_server.app.server** – application factory used by Gunicorn
- **celery_app** – defines the Celery instance and tasks
- **routes/** – HTTP endpoints for the web UI and API
- **services/** – helpers and utilities used by the routes
- **pdf_tools/** – merge and extract page utilities integrated from the companion repository

The `health` endpoint aggregates the status of Redis, Celery and model services.
