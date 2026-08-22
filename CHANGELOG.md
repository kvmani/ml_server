# Changelog

## [Unreleased]
- Integrated the independently deployable CPU-only Tabular ML Workbench at
  `/tabular_ml/`, including catalog discovery, same-origin assets, host smoke
  tests, local setup, and compatible Plotly CSP directives.
- Governance 1.1: every tool must remain independently deployable while supporting optional portal integration.
- Switch Docker services to run with Gunicorn directly via command line options.
- Added `gunicorn` and `Flask-Compress` dependencies for production deployment.
- New development and architecture documents in `docs/`.
- Introduced this changelog.
