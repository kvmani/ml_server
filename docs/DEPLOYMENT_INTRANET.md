# Intranet Deployment Guide

This document describes how to run the application on an isolated Ubuntu server
using systemd, Gunicorn and Celery.  All paths assume the project has been
cloned to `/opt/ml_server`.

## Requirements

- Python 3.10 or newer
- Redis server
- A virtual environment located at `/opt/ml_server/env`

Install dependencies:

```bash
sudo apt install python3-venv redis-server
cd /opt/ml_server
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
```

## Configuration

Edit `config/config.intranet.json` to match your environment or override values
with environment variables using the `APP_` prefix.

## Systemd Services

Create the following unit files in `/etc/systemd/system/`.

### ml_server.service

```
[Unit]
Description=ML Server
After=network.target

[Service]
WorkingDirectory=/opt/ml_server/src
Environment=PYTHONPATH=/opt/ml_server/src
ExecStart=/opt/ml_server/env/bin/gunicorn -w 2 -b 0.0.0.0:5000 ml_server.app.microstructure_server:create_app()
Restart=always

[Install]
WantedBy=multi-user.target
```

### ml_server-celery.service

```
[Unit]
Description=Celery Worker
After=network.target

[Service]
WorkingDirectory=/opt/ml_server/src
Environment=PYTHONPATH=/opt/ml_server/src
ExecStart=/opt/ml_server/env/bin/celery -A ml_server.celery_app worker
Restart=always

[Install]
WantedBy=multi-user.target
```

### ml_server-celery-beat.service

```
[Unit]
Description=Celery Beat
After=network.target

[Service]
WorkingDirectory=/opt/ml_server/src
Environment=PYTHONPATH=/opt/ml_server/src
ExecStart=/opt/ml_server/env/bin/celery -A ml_server.celery_app beat
Restart=always

[Install]
WantedBy=multi-user.target
```

Reload systemd and enable the services:

```bash
sudo systemctl daemon-reload
sudo systemctl enable ml_server ml_server-celery ml_server-celery-beat
```

Start the services and verify the health endpoint:

```bash
sudo systemctl start ml_server
sudo systemctl start ml_server-celery
sudo systemctl start ml_server-celery-beat
curl http://localhost:5000/health
```

If you encounter `ModuleNotFoundError` or Gunicorn crashes, ensure that the
`PYTHONPATH` and `WorkingDirectory` paths match the installation directory and
that the virtual environment contains all required packages.
