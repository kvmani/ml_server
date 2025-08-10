# Admin Dashboard

The admin interface polls configured plugins for health, metrics and tool
information. Plugins are discovered via a YAML configuration file and accessed
through the `PluginRegistry`.

## Metrics Schema

Plugins must expose `/metrics` returning the JSON object:

```json
{
  "tool": "name",
  "version": "1.2.3",
  "uptime_s": 123,
  "counters": {"tasks_total": 1},
  "gauges": {"queue_depth": 0},
  "timers": {"task_ms_p50": 10}
}
```

The dashboard aggregates this data and displays status for each tool at
`/admin/plugins`.
