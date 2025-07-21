# Redis Backup Guide

Create a snapshot of the Redis database for backup:

```bash
redis-cli SAVE
cp /var/lib/redis/dump.rdb /path/to/backup/
```

To restore, copy the backup file back to the Redis directory and restart Redis.
