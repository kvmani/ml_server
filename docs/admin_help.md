# Admin Tasks

- **Dashboard**: `http://<host>:5000/admin?token=<ADMIN_TOKEN>` provides a
  unified view of health checks, feedback, logs and Prometheus metrics.
- **View Feedback**: `http://<host>:5000/admin/feedback?token=<ADMIN_TOKEN>`
- **Check Disk Usage**: `curl http://<host>:5000/disk-usage`
- **Restart Services**:
  ```bash
  systemctl restart ml_server
  systemctl restart celery
  ```
- **Backup Redis**: see [REDIS_BACKUP.md](REDIS_BACKUP.md)

