# Intranet Deployment Guide — Ubuntu, Local Mirrors, CPU-Only

This guide deploys the **Scientific Tools Portal** and its companion services onto a typical
office Ubuntu host that sits on the intranet with **no direct internet access**. Packages come
from the local PyPI and npm mirrors, every machine-learning dependency is **CPU-only**, and no
component is permitted to contact a public CDN at runtime.

If you want the generic, internet-connected instructions instead, see
[`DEPLOYMENT.md`](DEPLOYMENT.md). For the coordinated multi-repository release order and the
rollback checklist, `docs/PRODUCTION_RELEASE_2026_08.md` remains the authoritative runbook.

---

## 1. What you are deploying

| Service | Owner repository | Default bind | Reached through |
| --- | --- | --- | --- |
| Scientific Tools Portal | `ml_server` | `127.0.0.1:5000` | nginx `/` |
| PDF Tools | `pdf_tools` | mounted in-process | portal `/pdf_tools/` |
| Tabular ML Workbench | `tabular_ml` | mounted in-process | portal `/tabular_ml/` |
| Hydride Segmentation | `HydrideSegmentation` | `127.0.0.1:5005` | its own service URL |
| PyTex Workbench | `pytex` | `127.0.0.1:8765` | its own service URL |
| Scientific Calculator | `scientific_calculator` | `127.0.0.1:5055` | its own service URL |
| Unit Converter | `unit_converter` | `127.0.0.1:5065` | its own service URL |

PDF Tools and Tabular ML are installed **into the portal's environment** and served by the portal
process. The other four are independent services; the portal only links to them. Every one of them
can also be deployed standalone — the portal is an optional gateway, not a prerequisite.

### Offline guarantees this deployment relies on

- **MathJax is vendored.** `src/ml_server/static/vendor/mathjax/` ships the
  `tex-chtml-full.js` bundle, the complete `woff-v2` font set, and the Apache-2.0 licence. The
  in-app scientific help typesets equations with no network access of any kind. Do not replace it
  with a CDN `<script>` tag — the Content-Security-Policy in `app/server.py` restricts
  `script-src` and `font-src` to `'self'` and will block it.
- **Bootstrap, Bootstrap Icons, and Font Awesome are vendored** under the same `static/vendor/`
  tree for the same reason.
- **No telemetry leaves the host.** Usage analytics are written to a local SQLite file and are
  anonymous by design (see §9).

---

## 2. Host prerequisites

Target: **Ubuntu 22.04 LTS or 24.04 LTS**, x86-64, no GPU required.

| Resource | Minimum | Recommended |
| --- | --- | --- |
| vCPU | 4 | 8 |
| RAM | 8 GB | 16 GB |
| Disk | 20 GB | 50 GB |

Install the system packages. `poppler-utils` provides the `pdftoppm` binary that `pdf2image`
shells out to for PDF page previews; without it the PDF preview thumbnails fail at runtime.

```bash
sudo apt-get update
sudo apt-get install -y python3.12 python3.12-venv python3-pip \
    poppler-utils redis-server nginx git ca-certificates
```

Verify the interpreter — the portal requires **Python 3.12 or newer**:

```bash
python3.12 --version
```

---

## 3. Point the host at the local mirrors

Nothing below will work until package resolution is redirected away from the public indexes.
Replace the hostnames with your site's actual mirrors.

### 3.1 Python (PyPI mirror)

Write a system-wide pip configuration:

```bash
sudo tee /etc/pip.conf >/dev/null <<'EOF'
[global]
index-url = http://pypi.intranet.local/simple
trusted-host = pypi.intranet.local
timeout = 60
retries = 3
EOF
```

Confirm the mirror answers before going further:

```bash
pip download --no-deps --dest /tmp/pipcheck Flask==3.0.2 && rm -rf /tmp/pipcheck
```

> If your mirror is served over plain HTTP, `trusted-host` is required. If it is served over HTTPS
> with an internal CA, drop `trusted-host` and install the CA certificate instead
> (`sudo cp intranet-ca.crt /usr/local/share/ca-certificates/ && sudo update-ca-certificates`).
> Prefer the CA route where your site supports it.

### 3.2 Node (npm mirror)

The portal itself needs no Node toolchain at runtime. Configure the mirror only on hosts where a
companion repository builds front-end assets:

```bash
npm config set registry http://npm.intranet.local/
npm config set strict-ssl false   # only if the mirror is plain HTTP
```

### 3.3 Git (source archives)

`requirements.txt` pins PDF Tools and Tabular ML to GitHub source archives, which an air-gapped
host cannot reach. Point Git at the internal mirror so those URLs resolve locally:

```bash
git config --global url."http://git.intranet.local/".insteadOf "https://github.com/"
```

Alternatively, replace those two lines in `requirements.txt` with the versions your local PyPI
mirror publishes, or with local paths to the sibling checkouts. See §5.2.

---

## 4. Create the deployment tree

The bundled systemd units expect `/opt/ml_server` with the virtual environment at
`/opt/ml_server/env`. Keep those paths unless you also edit the unit files.

```bash
sudo mkdir -p /opt/ml_server
sudo chown "$USER":"$USER" /opt/ml_server
git clone http://git.intranet.local/kvmani/ml_server.git /opt/ml_server
cd /opt/ml_server
python3.12 -m venv env
source env/bin/activate
python -m pip install --upgrade pip setuptools wheel
```

---

## 5. Install the Python dependencies (CPU-only)

### 5.1 Enforce CPU-only wheels

**Never install the default PyTorch wheels on this host.** The `pypi.org` defaults for
`torch`/`torchvision` bundle the CUDA runtime, adding several gigabytes and pulling GPU libraries
that will never be used on an office CPU machine. If a companion repository needs PyTorch, install
it from the CPU index explicitly, *before* installing that repository:

```bash
pip install --index-url http://pytorch-cpu.intranet.local/whl/cpu \
    --trusted-host pytorch-cpu.intranet.local \
    torch torchvision
```

Then verify no accelerator runtime was pulled in:

```bash
python - <<'PY'
import torch
print("torch", torch.__version__)
assert not torch.cuda.is_available(), "GPU build installed — reinstall from the CPU index"
assert "+cpu" in torch.__version__ or "cu" not in torch.__version__, torch.__version__
print("CPU-only build confirmed")
PY
```

The portal itself, PDF Tools, Tabular ML, Scientific Calculator, and Unit Converter have **no
deep-learning dependency at all**. Tabular ML is scikit-learn based and CPU-only by design.

### 5.2 Install the portal

```bash
cd /opt/ml_server
source env/bin/activate
pip install -r requirements.txt
```

If the two GitHub archive URLs in `requirements.txt` cannot be reached even with the Git
`insteadOf` rule from §3.3, install the companions from local checkouts instead:

```bash
pip install -r <(grep -v '@ https://github.com' requirements.txt)
pip install /srv/src/pdf_tools /srv/src/tabular_ml
```

Confirm both companions imported cleanly, since the portal fails to start without them:

```bash
python -c "import pdf_tools_service, tabular_ml_service; print('companions OK')"
```

Install the portal package itself so the `ml-server` entry point and the packaged
templates/static assets are available:

```bash
pip install .
```

---

## 6. Configure

Copy the example environment file and set the two secrets. **Both must be changed** — the
placeholders are deliberately invalid.

```bash
cd /opt/ml_server
cp .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(48))"   # APP_SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"   # APP_SECURITY__ADMIN_TOKEN
chmod 600 .env
```

Edit `.env` for the intranet host:

```ini
APP_HOST=127.0.0.1
APP_PORT=5000
APP_DEBUG=false
APP_SECRET_KEY=<the 48-byte value generated above>
APP_SECURITY__ADMIN_TOKEN=<the 32-byte value generated above>
APP_SECURITY__ALLOWED_ORIGINS="[http://tools.intranet.local]"
APP_CELERY__BROKER_URL=redis://127.0.0.1:6379/0
APP_CELERY__RESULT_BACKEND=redis://127.0.0.1:6379/0
APP_FEEDBACK__DATABASE_PATH=/opt/ml_server/data/engagement.sqlite3
APP_ANALYTICS__ENABLED=true
ML_SERVER_CONFIG=config/config.intranet.json
```

Point the catalog at the companion services (these are read by `src/ml_server/catalog.py`):

```ini
HYDRIDE_SEGMENTATION_URL=http://tools.intranet.local/hydride
PYTEX_URL=http://tools.intranet.local/pytex
SCIENTIFIC_CALCULATOR_URL=http://tools.intranet.local/calculator
UNIT_CONVERTER_URL=http://tools.intranet.local/converter
```

Optional internal SMTP relay for feedback acknowledgement mail. Feedback is still saved if
delivery fails, so leaving this disabled is safe:

```ini
APP_EMAIL__ENABLED=true
APP_EMAIL__SMTP_HOST=smtp.intranet.local
APP_EMAIL__SMTP_PORT=25
APP_EMAIL__FROM_ADDRESS=noreply@intranet.local
APP_EMAIL__DEVELOPER_ADDRESS=<the maintaining team's address>
```

Create the writable runtime directories:

```bash
mkdir -p /opt/ml_server/data /opt/ml_server/logs /opt/ml_server/tmp
```

`APP_DEBUG` must remain `false`. Debug mode exposes the Werkzeug console and is never acceptable
on a shared host, even an internal one.

---

## 7. Run as a service

Install the bundled units. The portal unit runs gunicorn with two workers and a 300-second
timeout, which suits long PDF and tabular jobs.

```bash
sudo cp /opt/ml_server/ml_server.service /etc/systemd/system/
sudo cp /opt/ml_server/ml_server-celery.service /etc/systemd/system/
sudo cp /opt/ml_server/ml_server-celery-beat.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now redis-server
sudo systemctl enable --now ml_server ml_server-celery ml_server-celery-beat
sudo systemctl status ml_server --no-pager
```

Celery and Redis are only needed for background job dispatch. If your deployment uses none of the
queued workflows, you may leave the two Celery units disabled.

### nginx reverse proxy

```nginx
server {
    listen 80;
    server_name tools.intranet.local;

    # PDF and dataset uploads; raise to match your largest expected document.
    client_max_body_size 200M;

    location / {
        proxy_pass         http://127.0.0.1:5000;
        proxy_set_header   Host              $host;
        proxy_set_header   X-Real-IP         $remote_addr;
        proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
    }

    # The vendored MathJax bundle and fonts are immutable per release.
    location /static/vendor/ {
        proxy_pass       http://127.0.0.1:5000;
        proxy_set_header Host $host;
        expires          30d;
        add_header       Cache-Control "public, immutable";
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/ml_server /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

The portal applies `ProxyFix(x_for=1, x_proto=1)`, so exactly **one** trusted proxy is expected in
front of it. If you chain a second proxy, update `x_for` in `src/ml_server/app/server.py` to match,
otherwise the forwarded headers will be misread.

---

## 8. Post-deployment verification

Run every check before announcing the service.

```bash
# 1. The portal answers and the catalog is complete.
curl -fsS http://127.0.0.1:5000/api/catalog | python -m json.tool | head -20

# 2. All six scientific help pages render.
for t in hydride-segmentation pytex pdf-tools tabular-ml \
         scientific-calculator unit-converter; do
  printf '%-24s %s\n' "$t" \
    "$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:5000/tools/$t/help)"
done

# 3. The vendored MathJax bundle and its fonts are served locally.
curl -s -o /dev/null -w 'bundle %{http_code} %{size_download} bytes\n' \
  http://127.0.0.1:5000/static/vendor/mathjax/tex-chtml-full.js
curl -s -o /dev/null -w 'font   %{http_code}\n' \
  http://127.0.0.1:5000/static/vendor/mathjax/output/chtml/fonts/woff-v2/MathJax_Math-Italic.woff

# 4. The mounted companions respond.
curl -s -o /dev/null -w 'pdf_tools  %{http_code}\n'  http://127.0.0.1:5000/pdf_tools/
curl -s -o /dev/null -w 'tabular_ml %{http_code}\n'  http://127.0.0.1:5000/tabular_ml/

# 5. No page references a public CDN.
curl -s http://127.0.0.1:5000/tools/pytex/help | grep -c 'cdn\.\|jsdelivr\|googleapis'
```

Expected: step 2 prints `200` six times, step 3 reports `200` with roughly 1.3 MB for the bundle,
step 4 prints `200` twice, and **step 5 prints `0`**. A non-zero count in step 5 means something
reintroduced a CDN reference and equations will not render on a disconnected host.

Finally, open `http://tools.intranet.local/tools/pytex/help` in a desktop browser and confirm the
equations are typeset as real mathematics — fractions with horizontal bars, proper Greek letters,
and a bold upright `g` for the orientation matrix. Raw text such as `\frac{...}` on screen means
the bundle failed to load; check the browser console for a Content-Security-Policy violation.

---

## 9. Privacy and data handling

The portal tells every visitor that no personal information is collected or stored. The
implementation enforces that claim, and any change to this area must preserve it:

- **Uploads are never persisted.** Documents and datasets are processed in memory for the lifetime
  of the request and discarded when the response is streamed.
- **No IP addresses are stored.** `analytics_sessions` and `feedback_submissions` retain the legacy
  `ip_address`/`user_agent` columns for schema compatibility, but they are always `NULL`.
  `initialize_database()` erases any values a pre-upgrade deployment left behind, so simply
  deploying this release clears historical identifiers.
- **User agents are reduced to a browser family** (Chrome, Firefox, Edge, Safari, Opera, Other)
  before storage, which cannot be used to fingerprint a visitor.
- **Feedback holds only what the visitor typed** — name, email, and message — and is used solely
  to reply to them.
- **Nothing is transmitted off-host.** The only outbound connection the portal can make is to the
  internal SMTP relay, and only when `APP_EMAIL__ENABLED=true`.

Back up `data/engagement.sqlite3` with the same care as any other operational database, and apply
your site's retention policy to it.

---

## 10. Upgrades and rollback

```bash
cd /opt/ml_server
sudo systemctl stop ml_server ml_server-celery ml_server-celery-beat
cp data/engagement.sqlite3 "data/engagement.sqlite3.$(date +%F)"
git fetch --tags && git checkout <new-tag>
source env/bin/activate
pip install -r requirements.txt && pip install .
sudo systemctl start ml_server ml_server-celery ml_server-celery-beat
```

Re-run every check in §8 afterwards. To roll back, check out the previous tag, reinstall, and
restore the dated database copy.

---

## 11. Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| Equations show as raw `\frac{...}` text | MathJax bundle not served, or blocked by CSP | Run §8 step 3; check the browser console for a CSP violation; confirm nothing replaced the vendored script with a CDN URL |
| Equations render but glyphs look wrong | Web fonts 404 | Confirm `static/vendor/mathjax/output/chtml/fonts/woff-v2/` was deployed; check `font-src 'self'` in the CSP |
| Service fails to start, `ModuleNotFoundError: pdf_tools_service` | Companion archives unreachable from the mirror | Install from local checkouts (§5.2) |
| PDF page previews are blank | `pdftoppm` missing | `sudo apt-get install -y poppler-utils` |
| `pip` cannot resolve any package | Mirror not configured or unreachable | Re-check `/etc/pip.conf` and the §3.1 verification command |
| Multi-gigabyte install, GPU libraries pulled in | Default PyTorch wheels used | Reinstall from the CPU index (§5.1) |
| Uploads rejected as too large | nginx `client_max_body_size` | Raise it in the server block and reload nginx |
| `/admin/` returns `Unauthorized` | Missing or wrong token | Append `?token=<APP_SECURITY__ADMIN_TOKEN>`; note the trailing slash on `/admin/` |
