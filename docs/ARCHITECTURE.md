# Architecture Overview

The application is composed of a Flask web layer and separate model services.

- **Flask App** – Handles routing, templates and API endpoints. It is created via `microstructure_server:create_app`.
- **Model Services** – Stub servers in `scripts/` emulate ML models. Real models can be dropped in with the same interface.
- **Celery Worker** – Processes long running tasks and communicates with Redis.
- **Docker Compose** – Provides Redis, workers and the web server for local development.

The app loads configuration from `config.json` and environment variables using `pydantic-settings`.
