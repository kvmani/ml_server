from prometheus_client import Counter, Gauge, generate_latest

# Counter for Celery task retries
retry_counter = Counter("retry_count", "Number of Celery task retries", ["task"])

# Gauge for disk usage percentage
# Updated each time /disk-usage is called

disk_usage_percent = Gauge("disk_usage_percent", "Disk usage percentage")


def metrics_response():
    """Return Prometheus metrics text."""
    return (
        generate_latest(),
        200,
        {"Content-Type": "text/plain; version=0.0.4"},
    )
