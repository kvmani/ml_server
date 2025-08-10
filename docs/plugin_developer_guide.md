# Plugin Developer Guide

This guide explains how to integrate independent tools with **ml_server**.

## Architecture & Responsibilities

- **ml_server** provides the user interface and admin dashboard. It does not
  implement any business logic for tools.
- **Plugins/Tools** live in their own repositories and own all processing logic.
  A tool exposes HTTP endpoints or a Flask blueprint that ml_server can mount.

### Integration Modes

1. **Remote Service Mode (HTTP)** – ml_server sends HTTP requests to a running
   service. The tool hosts its own Flask app.
2. **Embedded Blueprint Mode (Python Package)** – the tool ships a
   `flask.Blueprint` factory. ml_server imports the package and mounts the
   blueprint directly into its application.

## Required Endpoints (HTTP contract)

Every tool must expose the following endpoints:

- `GET /health` → `{status:"ok", version, uptime_s}`
- `GET /info` → `{name, version, description, homepage, authors, capabilities:[...], api_version:"v1"}`
- `GET /metrics` → metrics JSON schema v1 (below)
- `GET /openapi.json` → OpenAPI 3.1 specification for all task endpoints
- Tool specific task endpoints under `/tasks/*`
- Errors should return JSON in the form
  `{error:{code, message, details?, trace_id}}`

### Metrics JSON schema v1

```json
{
  "tool": "pdf_tools",
  "version": "1.2.3",
  "uptime_s": 12345,
  "counters": {"tasks_total": 42, "merge_requests": 17, "errors_total": 1},
  "gauges": {"queue_depth": 0},
  "timers": {"merge_ms_p50": 120, "merge_ms_p95": 350}
}
```

## Packaging Requirements for Embedded Mode

- The tool must be pip‑installable (provide a `pyproject.toml`).
- Expose a `create_blueprint(config)` factory returning a `flask.Blueprint`.
- Optionally expose `get_admin_provider()` for extra admin views.

## Testing & Local Development

- Each plugin should include a minimal Flask app for isolated testing.
- Use `python -m flask run` or similar to develop endpoints.

## Versioning, Auth and Security

- Increment the tool's version whenever the API or behaviour changes.
- Support authentication if required; the registry currently supports
  unauthenticated HTTP.
- Validate all request data and avoid executing arbitrary code.

## Documentation Expectations for Plugin Repositories

Each plugin repository should provide:

- `README.md` – overview and usage
- `DEVELOPER_GUIDE.md` – build and contribution instructions
- `API.md` – description of exposed endpoints
- `ADMIN.md` – operational notes for administrators

## Example Configuration

Tools are configured via YAML. Example:

```yaml
api_version: 1
tools:
  - name: pdf_tools
    mode: remote
    base_url: http://localhost:8000/pdf_tools
    auth: {type: none}
  - name: hydride_segmentation
    mode: embedded
    import: hydride_segmentation_service.plugin:create_blueprint
    mount: /hydride
```

Refer to `config/tools.example.yaml` for a full example.
