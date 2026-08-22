# Architecture Overview

The platform is composed of a Flask gateway and independently deployable companion web services.

- **Flask App** – Handles routing, templates and API endpoints. It is created via `ml_server.app.server:create_app()`.
- **Companion Services** – Tool repositories such as HydrideSegmentation, PyTex, PDF Tools,
  Scientific Calculator, and Unit Converter run as their own web applications and are linked or
  mounted by the portal through stable service boundaries.
- **Celery Worker** – Processes long running tasks and communicates with Redis.
- **Docker Compose** – Provides Redis, workers and the web server for local development.
- **PDF Tools** – A separately owned web service for merging and extracting pages from PDFs. The
  portal may mount its blueprint, but PDF Tools remains runnable on its own.

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

## Standalone and integrated deployment

`ml_server` is the common intranet entry point, not a runtime prerequisite for every tool. Each
companion repository must be installable, testable, and runnable independently. The integrated
stack adds discovery and gateway routing; it must not introduce imports, configuration, ports, or
service dependencies that make a standalone tool unusable.
