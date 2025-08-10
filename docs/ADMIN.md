# Admin Guide

The admin dashboard aggregates information from registered plugins.

## Health and Metrics Polling

When the server starts it loads plugin definitions from `config/tools.yaml`
(or `tools.example.yaml`). The `PluginRegistry` keeps track of remote services
and embedded blueprints. The admin view at `/admin/plugins` polls each plugin's
`/health`, `/info` and `/metrics` endpoints.

## Metrics Schema

Each plugin must expose metrics using the following JSON structure:

```json
{
  "tool":"pdf_tools",
  "version":"1.2.3",
  "uptime_s":12345,
  "counters":{"tasks_total":42,"merge_requests":17,"errors_total":1},
  "gauges":{"queue_depth":0},
  "timers":{"merge_ms_p50":120,"merge_ms_p95":350}
}
```

The raw JSON is rendered for inspection in the dashboard and may be
exported to external monitoring systems.
