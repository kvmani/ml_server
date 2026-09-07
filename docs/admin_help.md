# Admin Tasks

- **Operations console**: `http://<host>:5000/admin/` — sign in with the admin
  password (footer link on every page). Live client activity, analytics, logs,
  diagnostics and feedback. Full guide: [ADMIN_DASHBOARD.md](ADMIN_DASHBOARD.md).
- **Set or rotate the admin password**: `ml-server --hash-admin-password`, then
  put `ML_SERVER_ADMIN_PASSWORD_HASH=...` in the service `EnvironmentFile` and
  restart. Never commit it. See [ADMIN_DASHBOARD.md](ADMIN_DASHBOARD.md) §1.
- **View Feedback**: `http://<host>:5000/admin/feedback`
- **Check Disk Usage**: `curl http://<host>:5000/disk-usage`, or the console's
  Diagnostics tab.
- **Restart Services**:
  ```bash
  systemctl restart ml_server
  systemctl restart celery
  ```
- **Backup Redis**: see [REDIS_BACKUP.md](REDIS_BACKUP.md)
