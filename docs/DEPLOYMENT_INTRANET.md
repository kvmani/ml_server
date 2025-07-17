# Intranet Deployment Guide

This guide describes how to run the application without internet access.

1. Install Docker and Docker Compose.
2. Copy the repository to the target machine.
3. Run `docker-compose up --build` to start Redis, Celery, model stubs and the Flask server.
4. Place the following Nginx configuration in `/etc/nginx/conf.d/ml_server.conf` to enable HTTPS with a self-signed certificate:

```nginx
server {
    listen 443 ssl;
    server_name ml.local;
    ssl_certificate     /etc/nginx/certs/server.crt;
    ssl_certificate_key /etc/nginx/certs/server.key;

    location / {
        proxy_pass http://web:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Generate a certificate with:

```bash
openssl req -x509 -newkey rsa:4096 -nodes -keyout server.key -out server.crt -days 365
```

Restart Nginx and access `https://ml.local`.
