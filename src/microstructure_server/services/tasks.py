from __future__ import annotations

import io

import requests
from celery import Celery

from config import Config

celery_app = Celery(
    "microstructure_tasks",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0",
)


@celery_app.task(bind=True, max_retries=3)
def ebsd_cleanup_task(self, file_bytes: bytes) -> dict:
    """Send EBSD data to the cleanup model."""
    cfg = Config()
    url = cfg.ebsd_cleanup_settings.get("ml_model", {}).get("url", "")
    timeout = cfg.ebsd_cleanup_settings.get("ml_model", {}).get("timeout", 30)
    try:
        response = requests.post(url, files={"ebsd_file": io.BytesIO(file_bytes)}, timeout=timeout)
        if response.status_code == 200:
            return response.json()
        raise RuntimeError("Model processing failed")
    except Exception as exc:  # noqa: BLE001
        raise self.retry(exc=exc, countdown=5)
