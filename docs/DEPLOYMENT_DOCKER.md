# Docker Deployment

This guide describes how to run the ML Server using Docker Compose.

## Build Images

Use the provided `docker-compose.yml` to build the application and model service images:

```bash
docker-compose build
```

## Start the Stack

Bring up Redis, the Flask application, Celery worker and beat services:

```bash
docker-compose up -d
```

The web UI will be available on port 5000 by default.

## Environment Configuration

Copy `.env.example` to `.env` and update `APP_SECRET_KEY` and
`APP_SECURITY__ADMIN_TOKEN` with secure values before the first run. All
other variables can be adjusted as needed.

## Stopping Services

To stop the containers run:

```bash
docker-compose down
```
