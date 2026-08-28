# Changelog

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
