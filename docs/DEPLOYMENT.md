# Deployment Guide

This document describes a recommended process for deploying the microstructural analysis server on an Ubuntu Linux intranet environment.  The same steps can be adapted for both a testing server and the final production server.

## 1. Prepare the Server
1. **Install Python 3.10+**
   ```bash
   sudo apt-get update
   sudo apt-get install python3 python3-venv python3-pip -y
   ```
2. **Clone the repository** (replace `<path>` with your location):
   ```bash
   git clone https://github.com/kvmani/ml_server.git
   cd ml_server
   ```
3. **Create a virtual environment** for isolation:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

## 2. Install Dependencies
Install all Python dependencies from `requirements.txt` and testing utilities if needed:
```bash
pip install -r requirements.txt
# Optional: install test utilities
pip install -r requirements-test.txt
```

The hydride segmentation feature will require additional ML packages. When that code is integrated, extend `requirements.txt` with the necessary packages and rerun the installation step.

## 3. Configuration
Configuration values are stored in `config/config.intranet.json`.  You can override any value
via environment variables using the `APP_` prefix and `__` for nested keys
(e.g. `APP_PORT=8080`).  Review the host and port settings and modify them if
required.  For production, set `"debug": false`.

## 4. Starting the Services
The application consists of the Flask web UI and one or more ML model servers.  Start them within the virtual environment.

### a. Start model services
```bash
# Super‑resolution (mock)
python scripts/start_ml_model_service.py &
# EBSD cleanup (mock)
python scripts/start_ebsd_model_service.py &
# Future: Hydride segmentation server will have its own script
```

### b. Start the main Flask app
```bash
python app.py
```
The server listens on the port defined in `config/config.intranet.json` (default `5000`).

### c. Run as systemd services
Create unit files in `/etc/systemd/system/` to manage the app in production. Example units:

```
[Unit]
Description=ML Server
After=network.target

[Service]
WorkingDirectory=/opt/ml_server/src
Environment=PYTHONPATH=/opt/ml_server/src
ExecStart=/opt/ml_server/env/bin/gunicorn -b 0.0.0.0:5000 -w 2 -t 300 ml_server.app.server:create_app()
Restart=always

[Install]
WantedBy=multi-user.target
```

Similarly create `ml_server-celery.service` and `ml_server-celery-beat.service` using `celery -A ml_server.celery_app worker` and `celery -A ml_server.celery_app beat` as the `ExecStart` commands.

Reload systemd and enable the services:

```bash
sudo systemctl daemon-reload
sudo systemctl enable ml_server ml_server-celery ml_server-celery-beat
sudo systemctl start ml_server ml_server-celery ml_server-celery-beat
```

## 5. Service Updates With Minimal Downtime
To deploy new versions without interrupting running users:
1. Start a second instance of the app on a different port (e.g., `5001`).
2. Once healthy, update the local reverse proxy (or simply switch the firewall port) to point users to the new instance.
3. Stop the old instance.
This simple blue‑green approach avoids downtime while keeping the setup minimal.

## 6. Logging and Monitoring
Log files are written to the `logs/` directory as configured in `config/config.intranet.json`.  Ensure this directory exists and that the user running the service has write permission.  Monitor the log files for errors.

## 7. Rollback Plan
If the new deployment fails:
1. Stop the new instance.
2. Restart the previous working version (from its virtual environment or previous Git checkout).
3. Inspect logs to identify issues before attempting another deployment.

## 8. Periodic Code Updates
To fetch updates from the repository and redeploy:
```bash
cd ml_server
git pull
source venv/bin/activate
pip install -r requirements.txt  # update packages if needed
```
Restart the services using the blue‑green method described above.

## 9. Security Notes
This service runs on an isolated intranet with minimal concurrent users.  For simplicity, standard security hardening is not emphasized, but you should:
- Keep the system patched.
- Restrict network access to trusted clients.
- Consider using a firewall to limit access to the server port.


## Example Fresh Installation

On a clean Ubuntu system run:
```bash
sudo apt-get update
sudo apt-get install git python3 python3-venv python3-pip redis-server -y

# optional: install build tools
sudo apt-get install build-essential -y
```
Clone the code and set up:
```bash
git clone <repository-url>
cd ml_server
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
Start Redis and the services:
```bash
redis-server --daemonize yes
celery -A ml_server.celery_app worker &
python app.py
```
Visit `http://localhost:5000` to use the application.
