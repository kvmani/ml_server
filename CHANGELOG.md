# Changelog

## [1.3.1] - 2026-09-12

Fixes the administrator sign-in failure seen on the office server from suite
v1.4.0 through v1.6.0, and makes the shared configuration something a release
can be upgraded over safely.

### Fixed

- **Admin sign-in failed with "This form expired" on the plain-HTTP intranet.**
  Flask-Talisman defaults `session_cookie_secure` to `True` and re-applies it
  from a `before_request` hook on *every* request, which silently overrode the
  `SESSION_COOKIE_SECURE` the application factory set from
  `security.ssl_enabled`. Browsers never return a `Secure` cookie over HTTP, so
  the login form's CSRF token had nowhere to live and the POST was refused every
  time. `create_app()` now passes `force_https`, `strict_transport_security` and
  `session_cookie_secure` explicitly, all three derived from `ssl_enabled`. CSRF
  protection is unchanged and still enforced.
- **The signing key was regenerated per process.** `app.secret_key` fell back to
  `os.urandom(24)` whenever `secret_key` was unset or still the shipped
  `__SET_SECRET_KEY__` placeholder. Under `gunicorn --workers 2` the worker
  handling the login POST could not read the session the other worker had
  signed. The key is now read from the configuration, or generated once and kept
  in `<config directory>/.session_secret_key` (mode 0600), which every worker
  shares and which survives restarts, upgrades and rollbacks.
- A request short-circuited by an earlier `before_request` -- Talisman's HTTPS
  redirect -- raised `AttributeError: analytics_session_id` in the after-request
  hook, turning a redirect into a 500 on every plain-HTTP request to an HTTPS
  deployment.

### Added

- `ml_server.config_schema`: the canonical shape of `config.intranet.json`, with
  a `config_version`, defaults, type validation, and migration that renames
  legacy key spellings (`adminToken`, `admin-token`, `sslEnabled`, ...) onto the
  one name the portal reads. A file that sets two spellings of a setting to two
  different values is refused rather than guessed at. The module imports only
  the standard library, so the deployment scripts can run it against a shared
  config before activating a release.
- `python -m ml_server.config_cli check|plan|migrate|summary <path>`, with
  distinct exit codes for "invalid", "ambiguous" and "unreadable", and a
  `--json` summary that contains no secret value of any kind.
- `security.trusted_proxy_count` (default `0`). `ProxyFix` is installed only
  when a proxy is actually in front of the portal, so a client on the intranet
  cannot forge `X-Forwarded-For` past the admin login lockout.
- Diagnostics for a rejected login: the portal logs the request path, which of
  the four possible reasons applied, the scheme, and the secure-cookie mode --
  and never the token, the session, the password or the signing key. A `Secure`
  cookie on an HTTP request is called out by name with the setting to change.
- Regression tests covering the whole browser lifecycle: `tests/
  test_admin_session_csrf.py` (HTTP and HTTPS cookie flags, GET->POST CSRF,
  cross-worker sessions, login, logout, token change, diagnostics) and
  `tests/test_config_schema.py` (migration, aliases, validation, backups).

### Changed

- `security.admin_token` is the one canonical spelling of the console password.
  Other spellings are migrated to it; none is read directly.
- `config/config.intranet.json` and `default_config.json` carry
  `config_version`, `security.admin_password_hash` and
  `security.trusted_proxy_count`.
- `.session_secret_key` is git-ignored and docker-ignored.

## [1.3.0] - 2026-09-11

### Added

- **Online Annotator** joins the catalog (`online-annotator`, Microstructure): a multi-user
  workbench for creating, reviewing and exporting pixel-exact segmentation ground truth,
  owned by the standalone `kvmani/OnlineAnnotator` repository and linked by
  `ONLINE_ANNOTATOR_URL` (default `http://127.0.0.1:5070`). Its scientific help page covers
  the class area fraction, Otsu's criterion used by the box-threshold tool and the
  magic-wand membership rule, with a workflow diagram and a link to the tool's own `/help`.
- New catalog mark `annotator-mark.svg` and diagram `help/online-annotator-workflow.svg`.
- `scripts/setup_local.ps1` and `start_platform.ps1` install and start the annotator on
  port 5070 alongside the other local services.

### Changed

- Privacy copy on the home page and the FAQ now states the one deliberate exception to
  "nothing is stored": Online Annotator keeps a team's images and annotations on its
  intranet server and stores only an office e-mail and name per account.

## [1.2.0] - 2026-09-07

### Added

- **A password-protected admin operations console at `/admin/`**, reachable from an
  **Administrator sign in** link in the footer of every page. Seven panels: Overview,
  Live activity, Services & timing, Visitors, Logs, Diagnostics and Feedback. The page
  is a shell; every figure is fetched from a JSON API under `/admin/api/`, so the live
  panel can refresh every five seconds without redrawing the analytics, and an operator
  can `curl` exactly what the charts are drawn from.
- **Password authentication** (`app/admin/auth.py`) with a signed session (12-hour
  maximum, 60-minute idle timeout), a CSRF-protected login form, and a 15-minute
  lockout after five failed attempts from one address. A PBKDF2 hash is preferred to a
  password; `ml-server --hash-admin-password` generates one without echoing the
  password or leaving it in shell history. A server with no credential configured
  refuses every login instead of falling open, and placeholders such as `changeme` do
  not count as configured. Pre-1.2 `?token=` links keep working.
- **A live-activity registry** (`app/services/live_activity.py`) answering "which IP
  address is using which service right now": current and past services per client,
  request and error counts, average response time, last status and path, browser, idle
  time and session length, plus the same aggregated per service.
- **An analytics engine** (`app/services/analytics.py`) computing, for a selectable
  window from one hour to all time: request and error totals, error rate, sessions,
  unique visitors, average and p50/p90/p95/p99 response times overall and per service,
  the busiest and slowest paths, status-code breakdown, an hourly or daily traffic
  series, the busiest UTC hours, and browser and session-length distributions.
- **Unique-visitor counts over a settable number of months** (1–120), month by month
  and across every window from 24 hours to all time — the headline capacity figure of
  how many different machines used the platform.
- **Host and application diagnostics** (`app/services/diagnostics.py`): platform, CPU
  count and load, memory, thread and process figures, portal and host uptime, the
  config file actually loaded, bind address, blueprints and route table, disk usage per
  relevant volume, analytics database size and row counts, and Redis and Celery
  reachability. `psutil` enriches the report and every function degrades gracefully
  without it.
- **A filterable log viewer** (`app/services/logs.py`). Records are filtered at or above
  a chosen level, searched by free text, and counted per level; multi-line tracebacks
  stay attached to the record that raised them; only the newest 2 MB of the file is
  read, so the panel is instant on a log that has grown for months.
- **A JSON export** of the current analytics report, and an on-demand retention prune
  (`analytics.retention_months`, default 24) that bounds the one file on the server
  that grows purely because people used the portal.
- Vendored Chart.js 4.4.1 under `static/vendor/chartjs/`, so the console renders fully
  on an air-gapped office server.
- `docs/ADMIN_DASHBOARD.md`: how to set and rotate the admin password without the
  secret ever reaching git, CI or the release archive; what each panel shows; the JSON
  API; the privacy contract; retention; and a troubleshooting table.
- Thirty-two tests covering authentication, lockout, the unconfigured and
  placeholder-secret cases, open-redirect refusal, live activity and its expiry and
  cap, analytics windows and percentile ordering, log level and text filtering,
  diagnostics, and the absence of any CDN reference in the console.

### Changed

- The admin dashboard is now a first-party Flask blueprint; **Flask-Admin has been
  removed** as a dependency. `psutil` is added.
- Requests are attributed to a service by resolving the path against the catalog
  (`catalog.resolve_service`) rather than a hard-coded list of two prefixes, so a newly
  added internal tool is attributed correctly without a second place to update.
- Console traffic is excluded from the durable analytics; dashboard polling can no
  longer inflate the usage figures the dashboard reports.
- The footer shows the real release version instead of a hard-coded `1.0.0`, and admin
  static assets are cache-busted on that version.
- The portal now warns at startup when no `secret_key` is configured, because a
  generated one silently signs every administrator out on each restart.
- The visitor-facing privacy text on the home page and in the help/FAQ now states
  precisely what happens to a network address: never stored, kept durably only as a
  one-way digest for counting, and visible live to a signed-in administrator for a few
  minutes in server memory.

### Fixed

- The admin dashboard's charts never rendered on the office server: it loaded Chart.js
  from `cdn.jsdelivr.net`, which the Content-Security-Policy blocks and an air-gapped
  network cannot reach. The library is now vendored and served from this origin.
- Analytics indexes over migrated columns are created after the migration adds them, so
  upgrading a database created by an earlier release no longer fails on startup.

## [1.1.0] - 2026-08-28

### Added

- The Scientific Calculator's periodic table now carries **characteristic X-ray data** for every
  element up to californium: all twenty-six Siegbahn emission lines (Kα1, Kα2, Kβ1, Lα1, Lβ1,
  Mα …) and all twenty-four absorption edges (K, L1–L3, M1–M5, N1–N7, O1–O5, P1–P3), each with
  its energy in eV and keV, its wavelength in ångströms, the transition it comes from, and — for
  edges — the fluorescence yield and jump ratio. An **X-ray line finder** identifies an
  unlabelled XRF or EDS peak from its energy. Sixty further properties per element join the
  table, including successive ionization energies, covalent, van der Waals and metallic radii,
  thermal and calorimetric properties, lattice structure and natural isotopes. Requires
  Scientific Calculator 0.6.0; the portal catalog entry, tags and scientific help page describe
  it (`/tools/scientific-calculator/help`).
- Three equations on the calculator's scientific help page: the characteristic-line energy as the
  difference of two binding energies, Moseley's law, and the energy–wavelength relation with the
  12398.42 eV·Å constant.
- Vendored MathJax 3.2.2 (`tex-chtml-full` plus the complete CHTML web-font set) under
  `static/vendor/mathjax/`, so the in-app scientific help typesets professional mathematics with
  no CDN and no internet access.
- Symbol glossaries beneath every help equation, and an accessible spoken form for each formula.
- A privacy panel on the PDF Tools guide and a dedicated "Privacy and data security" section in
  the help/FAQ.
- `docs/DEPLOYMENT_UBUNTU_INTRANET.md`: an office-intranet Ubuntu runbook covering local
  PyPI/npm mirrors, CPU-only wheel enforcement, offline MathJax verification, and the privacy
  guarantees.
- Anonymous browser-family reporting on the admin dashboard.
- Anonymous browser major-version buckets (e.g. "Chrome 120"), session-length distribution, and
  Chart.js visualizations for tool usage, per-tool timing, browser mix, and session length on the
  admin dashboard.
- A `.gitattributes` guarding the vendored bundle against line-ending rewrites, and a test
  asserting the vendored assets are tracked by git rather than merely present on disk.

### Changed

- Rewrote every help equation from ASCII approximations (`2 d_hkl sin(theta_B) = lambda`) into
  real LaTeX, and added equations for aspect ratio, hexagonal interplanar spacing, output page
  count, sample count, and the cross-validated estimate.
- Rebuilt the landing page and help page styling on a single set of design tokens, replacing the
  competing `!important` "compact landing surface" layer. The tool grid is now a readable
  three-column desktop layout with a hero status panel and a four-item trust strip.
- PDF Tools is described as a general-purpose tool for **any** PDF rather than a scientific-PDF
  tool, and states plainly that documents are never stored and never leave the office network.

### Fixed

- `src/ml_server/static/css/style.css` was syntactically invalid: a stray `}` and `/` terminated
  the file and a malformed `..research-header` selector was never applied.
- `python -m ml_server.cli` exited silently because the module had no `__main__` guard.
- The repository-wide `output/` ignore rule silently excluded MathJax's entire font directory
  from version control; it is now anchored to the repository root.

### Security

- Privacy by design: client IP addresses and full `User-Agent` strings are no longer stored
  anywhere. Analytics keep only a coarse browser family, feedback keeps only what the visitor
  typed, the developer notification e-mail no longer carries the sender's IP, and
  `initialize_database()` erases identifiers left behind by earlier deployments.

## [1.0.0] - 2026-08-23

### Added

- Scientific help pages for every catalog tool, with equations, workflow steps, critical inputs,
  interpretation limits, and accessible SVG diagrams.
- Descriptive card details on hover and keyboard focus, plus distinct launch and help actions.
- A dependency-independent `/health/live` probe carrying the portal version.
- A coordinated production deployment, verification, and rollback runbook for all seven release
  components.

### Changed

- Promoted the portal to production release 1.0.0, disabled debug in shipped intranet configs,
  and made the `ml-server` command use Waitress unless `--debug` is explicitly requested.
- Installed the portal package in the production container and made the source-layout import path
  explicit in both container stages.
- Treats shipped `__SET_*__` placeholders as unset, preventing a placeholder from becoming a
  shared session secret or a usable administrator credential.
- Migrated PDF support from deprecated PyPDF2 to pypdf and pinned the 0.2.0 companion releases.

### Security

- In-app scientific guides inherit the portal content-security policy and open external manuals
  with opener isolation.

- Integrated the independently deployable CPU-only Tabular ML Workbench at
  `/tabular_ml/`, including catalog discovery, same-origin assets, host smoke
  tests, local setup, and compatible Plotly CSP directives.
- Governance 1.1: every tool must remain independently deployable while supporting optional portal integration.
- Switch Docker services to run with Gunicorn directly via command line options.
- Added `gunicorn` and `Flask-Compress` dependencies for production deployment.
- New development and architecture documents in `docs/`.
- Introduced this changelog.
