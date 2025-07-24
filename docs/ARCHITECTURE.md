# Architecture Overview

The application is composed of a Flask web layer and separate model services.

- **Flask App** – Handles routing, templates and API endpoints. It is created via `ml_server.app.server:create_app()`.
- **Model Services** – Stub servers in `scripts/` emulate ML models. Real models can be dropped in with the same interface.
- **Celery Worker** – Processes long running tasks and communicates with Redis.
- **Docker Compose** – Provides Redis, workers and the web server for local development.
- **PDF Tools** – Lightweight utilities for merging and extracting pages from PDFs. They run entirely within the Flask app.

The app loads configuration from `config/config.intranet.json` and environment variables via a lightweight loader in `ml_server.config`.

```
+-----------+      +--------------------+
|  Browser  +----->|    Flask App       |
+-----------+      +--------------------+
                            |
                            v
                    +---------------+
                    |  Celery Worker|
                    +---------------+
                            |
                            v
                    +------------+
                    | ML Models  |
                    +------------+
```

Browser requests hit the Flask app which delegates heavy jobs to Celery workers interacting with the ML model services.
