# Intranet Deployment Guide

This guide covers deploying the ML Server inside a restricted intranet.
It assumes the code is installed at `/opt/ml_server` with a virtual
environment located in `/opt/ml_server/env`.

## Configuration

All settings are stored in `config/config.intranet.json`.  Environment
variables using the `APP_` prefix can override values.  The most common
options are the host/port and URLs for the ML model services.

Be sure to edit `APP_SECRET_KEY` and `APP_SECURITY__ADMIN_TOKEN` in `.env`
or as environment variables before exposing the service.

## Gunicorn Service

Create `/etc/systemd/system/ml_server.service` with:

```ini
[Unit]
Description=ML Server
After=network.target

[Service]
WorkingDirectory=/opt/ml_server/src
Environment=PYTHONPATH=/opt/ml_server/src
EnvironmentFile=/opt/ml_server/.env
ExecStart=/opt/ml_server/env/bin/gunicorn -b 0.0.0.0:5000 -w 2 -t 300 ml_server.app.server:create_app()
Restart=always

[Install]
WantedBy=multi-user.target
```

## Celery Services

Create similar units for the worker and beat scheduler:

`/etc/systemd/system/ml_server-celery.service`
```ini
[Unit]
Description=Celery Worker
After=network.target

[Service]
WorkingDirectory=/opt/ml_server/src
Environment=PYTHONPATH=/opt/ml_server/src
EnvironmentFile=/opt/ml_server/.env
ExecStart=/opt/ml_server/env/bin/celery -A ml_server.celery_app worker
Restart=always

[Install]
WantedBy=multi-user.target
```

`/etc/systemd/system/ml_server-celery-beat.service`
```ini
[Unit]
Description=Celery Beat
After=network.target

[Service]
WorkingDirectory=/opt/ml_server/src
Environment=PYTHONPATH=/opt/ml_server/src
EnvironmentFile=/opt/ml_server/.env
ExecStart=/opt/ml_server/env/bin/celery -A ml_server.celery_app beat
Restart=always

[Install]
WantedBy=multi-user.target
```

Reload systemd after creating the files:

```bash
sudo systemctl daemon-reload
sudo systemctl enable ml_server ml_server-celery ml_server-celery-beat
sudo systemctl start ml_server ml_server-celery ml_server-celery-beat
```

## Troubleshooting

If the service fails with `ModuleNotFoundError: No module named 'ml_server'`,
verify that `PYTHONPATH=/opt/ml_server/src` is set in each unit file and that
the working directory exists.  Also ensure the virtual environment was
created with the required packages installed.

## Test Data

Sample files for smoke testing are provided under `tests/test_data/`.  After
deployment you can verify the API is reachable by running:

```bash
curl http://localhost:5000/health
```

You should receive a JSON response indicating the service status.

