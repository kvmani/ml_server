"""Prometheus metrics helpers and collectors."""

from __future__ import annotations

import time

from prometheus_client import Counter, Gauge, Histogram, generate_latest

# Counter for Celery task retries
retry_counter = Counter("retry_count", "Number of Celery task retries", ["task"])

# Gauge for disk usage percentage
# Updated each time /disk-usage is called

disk_usage_percent = Gauge("disk_usage_percent", "Disk usage percentage")

# Request/response metrics
request_latency = Histogram(
    "request_latency_seconds",
    "Request latency in seconds",
    ["endpoint"],
)
request_count = Counter(
    "request_count_total",
    "Total HTTP requests",
    ["endpoint", "status"],
)
error_count = Counter(
    "error_count_total",
    "Total error responses",
    ["endpoint", "type"],
)
visit_counter = Counter(
    "visit_total",
    "Total endpoint visits",
    ["endpoint"],
)
active_users_gauge = Gauge("active_users", "Number of active users")
uptime_gauge = Gauge("uptime_seconds", "Application uptime in seconds")


def metrics_response():
    """Return Prometheus metrics text."""
    return (
        generate_latest(),
        200,
        {"Content-Type": "text/plain; version=0.0.4"},
    )


def update_uptime(start_time: float) -> None:
    """Update the uptime gauge based on ``start_time``."""
    uptime_gauge.set(time.time() - start_time)


def visit_summary() -> dict[str, int]:
    """Return visit counts per endpoint."""
    summary: dict[str, int] = {}
    for sample in list(visit_counter.collect())[0].samples:
        if sample.name.endswith("_total"):
            summary[sample.labels["endpoint"]] = int(sample.value)
    return summary


def active_user_count() -> int:
    """Return the current number of active users."""
    samples = list(active_users_gauge.collect())[0].samples
    return int(samples[0].value) if samples else 0
