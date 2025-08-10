# Plugin Developer Guide

## Architecture & Responsibilities

`ml_server` acts as a lightweight front end providing UI and an admin dashboard.
Business logic lives in **plugins** which are developed and deployed
independently. Each plugin exposes a small HTTP API and can either run as a
remote service or ship as a Python package that provides a Flask blueprint.

### Integration Modes

1. **Remote Service Mode** – plugin runs as its own service and `ml_server`
   calls it via HTTP.
2. **Embedded Blueprint Mode** – plugin is a Python package providing a
   `flask.Blueprint` factory.

## Required Endpoints

Plugins must implement these endpoints:

- `GET /health` → `{"status": "ok", "version": "1.0.0", "uptime_s": 123}`
- `GET /info` → `{"name": "pdf_tools", "version": "1.0.0", "description": "…",
  "homepage": "…", "authors": ["…"], "capabilities": ["merge"], "api_version": "v1"}`
- `GET /metrics` → see schema below
- `GET /openapi.json` → OpenAPI 3.1 spec for plugin routes
- Tool specific task endpoints under `/tasks/*`

### Common Error JSON

All errors should return:
`{"error": {"code": "string", "message": "string", "details": {}, "trace_id": ""}}`

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

## Packaging for Embedded Mode

- Publish a pip-installable package with `pyproject.toml`.
- Provide `create_blueprint(config)` returning a `flask.Blueprint`.
- Optionally provide `get_admin_provider()` for extra admin views.

Each plugin repository should include a minimal Flask app for isolated testing.

## Testing & Local Development

- Write unit tests and provide a simple app to run the plugin standalone.
- Tools should version their API and publish docs:
  - `README.md`
  - `DEVELOPER_GUIDE.md`
  - `API.md`
  - `ADMIN.md`

## Versioning, Auth and Security

- Expose an `api_version` field in `/info`.
- Handle authentication if required; the example config supports basic
  unauthenticated plugins.
- Validate all inputs and time out outbound requests.

## Example Configuration

`ml_server` discovers plugins via a YAML file:

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

## Adding a Plugin Programmatically

```python
from ml_server.plugins import PluginRegistry
registry = PluginRegistry(app)
registry.register_remote("pdf_tools", "http://localhost:8000/pdf_tools")
```

With the registry configured, the admin dashboard polls `/health`, `/info` and
`/metrics` for each tool.
