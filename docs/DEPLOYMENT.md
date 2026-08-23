# Deployment Guide

This document describes a recommended process for deploying the microstructural analysis server on an Ubuntu Linux intranet environment.

> **Deploying onto an office intranet host with local Python/Node mirrors and CPU-only packages?**
> Use [`DEPLOYMENT_UBUNTU_INTRANET.md`](DEPLOYMENT_UBUNTU_INTRANET.md) instead — it is the
> step-by-step runbook for that environment, including mirror configuration, CPU-only wheel
> enforcement, the vendored offline MathJax check, and the privacy guarantees.
  The same steps can be adapted for both a testing server and the final production server.

## 1. Prepare the Server
1. **Install Python 3.12+**
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
Install all Python dependencies from `requirements.txt` and testing utilities if needed. The PDF tools require `pypdf` and `pdf2image`, which are included in the requirements file:
```bash
pip install -r requirements.txt
# Optional: install test utilities
pip install -r requirements-test.txt
```

Hydride segmentation is a separately deployed service owned by `C:\Users\kvman\HydrideSegmentation`. Install and run that repository using its own deployment instructions; the portal only links to its stable service URL.

PDF Tools is likewise installed from the local owner repository with
`scripts/setup_local.ps1`; it is intentionally not fetched as a package from
the public package index.

PDF Tools and Tabular ML are installed from the immutable `v0.2.0` source archives declared in
`requirements.txt`. For local development, `scripts/setup_local.ps1` replaces
those installs with editable sibling checkouts. The
companion is CPU-only: deployment does not require CUDA, ROCm, a GPU driver, or
an accelerator runtime.

Every companion service may also be deployed independently. Follow the owning repository's
standalone web-app instructions when only one tool is required; the portal deployment is an
optional gateway arrangement and is not a prerequisite.

## 3. Configuration
Configuration values are stored in `config/config.intranet.json`.  You can override any value
via environment variables using the `APP_` prefix and `__` for nested keys
(e.g. `APP_PORT=8080`).  Review the host and port settings and modify them if
required.  For production, set `"debug": false`.

For the coordinated release manifest, tagged-artifact order, smoke-test matrix, blue-green
procedure, and rollback checklist, use `docs/PRODUCTION_RELEASE_2026_08.md` as the authoritative
runbook.

## 4. Starting the Services
The application consists of the Flask web UI and one or more ML model servers.  Start them within the virtual environment.

### a. Start the mature companion services
```bash
# Hydride segmentation runs from its own repository and service.
# Tabular ML is mounted by the portal at /tabular_ml/ and may also run alone.
```

### b. Start the main Flask app
```bash
ml-server --host 127.0.0.1 --port 5000
```
`python app.py` is a compatibility wrapper for the same Waitress-backed entry point. The server
otherwise uses the host and port in the file selected by `ML_SERVER_CONFIG`.

### c. Run as systemd services
Create unit files in `/etc/systemd/system/` to manage the app in production. Example units:

```
[Unit]
Description=ML Server
After=network.target

[Service]
WorkingDirectory=/opt/ml_server
Environment=PYTHONPATH=/opt/ml_server/src
ExecStart=/opt/ml_server/env/bin/gunicorn -b 127.0.0.1:5000 -w 2 -t 300 ml_server.app.server:create_app()
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

## 8. Release Updates
Do not update the live checkout or virtual environment in place. Build and hash the approved
release artifacts, install them into a new versioned environment, run the acceptance checks in
`PRODUCTION_RELEASE_2026_08.md`, and switch traffic using the blue-green procedure above. Retain
the previous environment until the observation window closes.

## 9. Security Notes
An intranet is not a trust boundary. The production deployment must:

- bind application services to loopback and expose only a TLS reverse proxy;
- load secrets from the deployment secret store through `ML_SERVER_CONFIG`/environment variables;
- use a non-default admin token and stable secret key, with debug and reloaders disabled;
- run under an unprivileged service account with least-privilege data-directory permissions;
- enforce request-size limits, patch the host regularly, and restrict ingress with a firewall;
- collect access/application logs and alert on readiness degradation and elevated error rates.


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
Validate configuration, then start Redis and the supervised services:
```bash
export ML_SERVER_CONFIG=/etc/ml-server/config.intranet.json
ml-server --host 127.0.0.1 --port 5000
```
Use the systemd units for the portal and Celery worker/beat in production; the foreground command
above is only a pre-cutover smoke. Access the application through the configured TLS proxy.
