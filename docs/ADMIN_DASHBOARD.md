# Admin Operations Console

The portal ships a password-protected operations console at `/admin/`. It shows
live service activity, usage analytics, filterable logs and host diagnostics.
Every visitor page carries an **Administrator sign in** link in the footer.

---

## 1. Setting the admin password

**The password is never stored in this repository.** It is read from the service
environment at runtime, which is why a clean checkout, a CI run and a release
build all work without it, and why the release archive contains no credential.

### Recommended: store a hash, not the password

On the office server, generate a hash once:

```bash
cd /home/kvmani/ml_platform/current
../.venv/bin/ml-server --hash-admin-password
```

It prompts twice (the password is never echoed, never lands in your shell
history, and never appears in `ps`), then prints one line:

```text
ML_SERVER_ADMIN_PASSWORD_HASH=pbkdf2:sha256:600000$....
```

Put that line in a root-owned environment file that systemd reads:

```bash
sudo install -o kvmani -g kvmani -m 600 /dev/null /home/kvmani/ml_platform/shared/config/portal.env
# paste the ML_SERVER_ADMIN_PASSWORD_HASH=... line into it, then:
chmod 600 /home/kvmani/ml_platform/shared/config/portal.env
```

Point the unit at it (`~/.config/systemd/user/ml-platform-portal.service`):

```ini
[Service]
EnvironmentFile=/home/kvmani/ml_platform/shared/config/portal.env
```

Then reload and restart:

```bash
systemctl --user daemon-reload
systemctl --user restart ml-platform-portal
```

### Why this keeps deployments and builds working

| Concern | Why it is unaffected |
| --- | --- |
| GitHub Actions / CI | No admin secret is needed to install, lint, test or package. Tests set their own password in-process. |
| The release archive | Contains only code and config templates. `admin_password_hash` ships empty. |
| `update.sh` / `rollback.sh` | The secret lives in `shared/config/`, **outside** the replaceable release directory, so switching the `current` symlink never touches it. |
| Rotating the password | Edit the env file and restart the portal. No redeploy, no rebuild, no new tag. |
| Git | `.env` is git-ignored and `shared/config/portal.env` is not in the repository at all. |

### Resolution order

The first configured value wins:

1. `ML_SERVER_ADMIN_PASSWORD_HASH` (environment) — **recommended**
2. `security.admin_password_hash` (config JSON)
3. `ML_SERVER_ADMIN_PASSWORD` (environment, plaintext)
4. `security.admin_password` (config JSON, plaintext)
5. `security.admin_token` (config JSON) — the pre-1.2 token, accepted as a
   password so an upgrade does not lock an operator out

Placeholder values (`changeme`, `__SET_ADMIN_TOKEN__`, `admin`, `password`, an
empty string) are treated as **not configured**. A server with no credential
refuses every login and says so on the sign-in page; it never falls open.

### Local development

Put a throwaway password in a git-ignored `.env` at the checkout root:

```text
APP_SECRET_KEY=local-dev-secret-key-not-for-production
ML_SERVER_ADMIN_PASSWORD=local-dev-admin-password
```

### The signing key, and why it must be stable

Admin sessions -- and the login form's CSRF token, which lives inside the
session -- are signed with the Flask secret key. Two properties are required,
and the second is the one that broke a production deployment:

* it must **survive a restart**, or every administrator is silently signed out;
* it must be **the same in every worker process**. Production runs
  `gunicorn --workers 2`. With a per-process key, the worker that handles the
  login POST cannot read the session the worker that rendered the form wrote,
  so the CSRF token appears to have vanished and the login reports that the
  form expired -- on roughly every other attempt, which is exactly as confusing
  as it sounds.

The key is resolved in this order:

1. `secret_key` in the config JSON (or `APP_SECRET_KEY` in the environment);
2. failing that, a key generated **once** and kept in
   `<config directory>/.session_secret_key` -- in the office deployment that is
   `~/ml_platform/shared/config/.session_secret_key`, which sits outside every
   release directory, is read by both workers, and survives restarts, upgrades
   and rollbacks. It is created with mode 0600 and is a secret: it must never
   reach git, CI or a release archive.

`deploy/update.sh` fills in a strong `secret_key` for you when the shared config
has none, so a migrated deployment has nothing to do here. Set
`ML_SERVER_STATE_DIR` if the generated key should live somewhere other than
beside the configuration.

---

## 1b. HTTP and HTTPS, and the session cookie

One setting decides this, and it drives three behaviours together:

```json
"security": { "ssl_enabled": false }
```

| `ssl_enabled` | `SESSION_COOKIE_SECURE` | HTTPS redirect | HSTS |
| --- | --- | --- | --- |
| `false` -- plain-HTTP intranet | off | no | no |
| `true` -- HTTPS | on | yes | yes |

They must move together. **A browser never returns a `Secure` cookie over
HTTP.** An HTTP deployment whose session cookie is marked `Secure` therefore
serves every page perfectly and makes signing in impossible: the CSRF token has
nowhere to live, and the POST comes back "This form expired".

That is not hypothetical -- it is what happened between suite v1.4.0 and
v1.6.0. Flask-Talisman defaults `session_cookie_secure` to `True` and re-applies
it from a `before_request` hook on *every* request, so setting
`SESSION_COOKIE_SECURE` in the application factory afterwards had no effect at
all: the value looked correct in a startup dump and was `True` by the time any
response was built. `create_app()` now passes `force_https`,
`strict_transport_security` and `session_cookie_secure` to Talisman explicitly,
all three from `ssl_enabled`, and a regression test asserts on the `Set-Cookie`
header rather than on the config.

`SESSION_COOKIE_HTTPONLY` is always on and `SESSION_COOKIE_SAMESITE` is always
`Lax`, in both modes.

**CSRF protection is enabled in both modes and is not a thing to turn off.** The
config validator refuses `security.csrf_enabled: false` outright.

### Reverse proxies

`security.trusted_proxy_count` is `0` by default, which means `X-Forwarded-For`
and `X-Forwarded-Proto` are **not** believed. In the office deployment gunicorn
is reached directly, so trusting them would let any client on the intranet claim
somebody else's address and walk past the login lockout. Set it to the number of
proxies actually in front of the portal if you put one there.

---

## 2. Signing in

The canonical URL is **`http://<host>:5000/admin/`**, and every portal page links
to it from **Administrator sign in** in the footer. The URL is deliberately not
a secret: authentication is enforced on every console page and every JSON
endpoint behind it, so a visible link costs nothing and a hidden one only costs
the operator who has forgotten where it is.

* Browse to `http://<host>:5000/` and use **Administrator sign in** in the footer,
  or go straight to `/admin/login`.
* A session lasts 12 hours, or 60 minutes of inactivity, whichever comes first.
* Five wrong passwords from one address locks that address out for 15 minutes.
* **Sign out** ends the session immediately.
* Pre-1.2 `?token=<ADMIN_TOKEN>` links still work, for scripts and bookmarks.
  Prefer the login form: a token in a URL ends up in logs and chat history.

---

## 3. What each tab shows

### Overview

Uptime, clients active right now, unique visitors, requests, error rate,
response-time p95, sessions and total server time for the selected window, plus
traffic over time, unique visitors per month, requests per service, the busiest
UTC hours, response-status breakdown, and the busiest and slowest paths.

The **Window** control (1h … all time) scopes every figure on this tab, the
Services tab and the Logs counts. **Months of history** (1–120) sets the depth of
the per-month visitor trend.

### Live activity

Which **IP address** is using which **service**, right now: current service, all
services touched, request and error counts, average response time, last status
code, last path, browser, idle time and how long the client has been active.
A companion table aggregates the same data per service.

This panel refreshes every 5 seconds. See §5 for the privacy contract.

### Services & timing

Per-service statistics for the window: requests, tool opens, sessions, unique
visitors, errors and error rate, average, p50, p90, p95, p99, slowest request,
total server time and last use — plus charts of timing and of total time spent.

p95 is the number to watch: it is what the slowest one visitor in twenty waits.

### Visitors

Unique visitors and sessions across every window (24h, 7d, 30d, 90d, 12 months,
all time), the month-by-month table, browser families and versions, the session
length distribution, and the most recent sessions.

### Logs

The application log parsed into records and filterable by **minimum level**
(choosing `WARNING` shows warnings, errors and criticals together), by free-text
search, and by line count. Counts per level are shown for the whole file.
Multi-line tracebacks stay attached to the record that raised them.

Only the most recent 2 MB of the log is read, so the panel stays instant on a
server that has been running for months.

### Diagnostics

Host (platform, CPU, load, memory, threads, PID), application (version, uptime,
bind address, the config file actually loaded, debug flag, blueprints, route
count), analytics storage (database size, row counts, first and last event),
dependency reachability (Redis, Celery workers), disk usage per relevant volume,
the catalog of services with their addresses, the full route table, and the raw
Prometheus exposition text.

Loading this tab pings Redis and Celery, so it can take a couple of seconds when
either is down.

### Feedback

The latest feedback and feature requests, with a link to the full paginated view.

---

## 4. JSON API

Every panel is backed by an endpoint an operator or script can call directly.
All of them require a session (or `?token=`) and return `401` otherwise.

| Endpoint | Purpose |
| --- | --- |
| `GET /admin/api/overview?window=&months=` | The complete analytics report |
| `GET /admin/api/live` | Current client addresses and services |
| `GET /admin/api/logs?level=&search=&limit=` | Filtered log records and level counts |
| `GET /admin/api/diagnostics` | Host, application, disk and dependency state |
| `GET /admin/api/metrics` | Prometheus exposition text |
| `GET /admin/api/feedback?limit=` | Recent feedback |
| `GET /admin/api/export?window=&months=` | The report as a JSON download |
| `POST /admin/api/prune` | Apply the retention policy now |

Example:

```bash
curl -s "http://127.0.0.1:5000/admin/api/overview?window=30d&months=12&token=$ADMIN_TOKEN" \
  | python -m json.tool
```

---

## 5. Privacy contract

The portal tells every visitor that it does not store personal information. That
statement stays true, and the design is what makes it true:

* **Nothing durable holds an address.** `analytics_sessions` and
  `analytics_events` store `client_hash`, an HMAC-SHA256 digest of the address
  keyed with the server secret. It can be counted (`COUNT(DISTINCT ...)`) but
  cannot be read back into an address by anyone holding only the database file.
  Rotating the secret starts a new counting epoch.
* **Live addresses exist only in memory.** The Live activity panel reads an
  in-process registry that keeps the last five minutes of activity, caps itself
  at 5000 clients, and is lost on restart. Nothing there is written to disk, to
  the analytics database, or to the log.
* **The browser string is reduced before storage** to a family and a major
  version (e.g. "Chrome 120"), never the full User-Agent.
* **Upgrading enforces it.** Startup migration erases any IP address or
  user-agent left in a database created by an older release.
* **The console itself is not counted.** Admin traffic is excluded from the
  durable analytics so dashboard polling cannot inflate usage figures.

The visitor-facing help/FAQ describes all of this in plain language under
"Privacy and data security".

---

## 6. Retention

Analytics are kept for `analytics.retention_months` (default 24). Use
`POST /admin/api/prune` — or the environment override
`APP_ANALYTICS__RETENTION_MONTHS` — to change or apply it:

```bash
curl -s -X POST "http://127.0.0.1:5000/admin/api/prune?token=$ADMIN_TOKEN" \
  -H 'Content-Type: application/json' -d '{"retention_months": 24}'
```

Twenty-four months keeps year-on-year comparisons available while bounding the
one file on the server that grows purely because people used the portal.

---

## 7. Offline operation

The console loads **no CDN assets**. Chart.js 4.4.1 is vendored at
`static/vendor/chartjs/chart.umd.min.js` and the Content-Security-Policy allows
scripts only from this origin, so the dashboard renders fully on an air-gapped
office server.

---

## 8. Troubleshooting

| Symptom | Cause and fix |
| --- | --- |
| "Admin access is not configured" | No credential set, or a placeholder value. See §1. |
| Signed out on every restart | No stable signing key. See the signing-key section in §1; on a deployed server `shared/config/.session_secret_key` should exist. |
| **"This form expired" / "Page expired" on every sign-in attempt** | The CSRF token could not be matched to the session that issued it. The portal logs the reason (`grep -i csrf` in the log). Most often: the session cookie is marked `Secure` on a plain-HTTP site -- set `security.ssl_enabled: false` and restart. See §1b. |
| Sign-in works about half the time | The signing key differs between gunicorn workers. Set `secret_key` in the shared config, or confirm `shared/config/.session_secret_key` is readable by the service user, then restart. |
| `KeyError: 'adminToken'` when reading the config | The canonical key is `security.admin_token`. `adminToken` and `admin-token` are accepted and rewritten by the updater's migration; nothing reads the camelCase spelling directly. |
| "Too many failed attempts" | Five failures from your address. Wait 15 minutes, or restart the service to clear the in-memory counter. |
| Charts are blank | Check that `static/vendor/chartjs/chart.umd.min.js` is present in the release; the browser console will show a blocked or 404 script. |
| Unique visitors read 0 for older months | Expected. The per-client digest only exists for traffic recorded from 1.2.0 onward; earlier rows keep their session counts. |
| Diagnostics take seconds to load | Redis or Celery is unreachable and the check is waiting on its timeout. The panel reports which. |
| Log panel says no file | The log directory in the loaded config does not match where the service writes. The panel prints the path it tried. |
