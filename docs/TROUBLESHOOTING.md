# Troubleshooting

## Services Fail to Start
- Ensure Redis is running: `docker-compose up redis` or `sudo service redis start`.
- Check logs in the `logs/` directory for errors.

## Celery Tasks Stuck
- Verify workers are running: `celery -A microstructure_server.services.tasks worker`.
- Inspect `logs/retries.log` for repeated failures.

## Disk Alerts
- Query `/disk-usage` or check Prometheus `disk_usage_percent` gauge to see if the disk is full.
