from __future__ import annotations

import logging
import os
from pathlib import Path

import requests
from celery import Celery
from celery.signals import worker_process_init

from .app.services.graceful import install_signal_handlers
from .app.services.metrics import retry_counter
from .config import Config

cfg = Config()
celery_app = Celery(
    "microstructure_tasks",
    broker=cfg.celery_settings.get("broker_url", "redis://redis:6379/0"),
    backend=cfg.celery_settings.get("result_backend", "redis://redis:6379/0"),
)


@worker_process_init.connect
def _init_worker(**_kwargs) -> None:  # pragma: no cover - side effect only
    install_signal_handlers()


@celery_app.task(bind=True, max_retries=3)
def ebsd_cleanup_task(self, file_path: str) -> dict:
    """Send EBSD data to the cleanup model."""
    cfg = Config()
    url = cfg.ebsd_cleanup_settings.get("ml_model", {}).get("url", "")
    timeout = cfg.ebsd_cleanup_settings.get("ml_model", {}).get("timeout", 30)
    try:
        with open(file_path, "rb") as f:
            response = requests.post(
                url,
                files={"ebsd_file": f},
                timeout=timeout,
            )
        if response.status_code == 200:
            return response.json()
        raise RuntimeError("Model processing failed")
    except Exception as exc:  # noqa: BLE001
        retry_counter.labels(task="ebsd_cleanup").inc()
        _log = logging.getLogger("celery.retry")
        log_file = Path("logs") / "retries.log"
        log_file.parent.mkdir(exist_ok=True)
        handler = logging.FileHandler(log_file)
        _log.addHandler(handler)
        _log.info("Retry ebsd_cleanup_task for %s due to %s", file_path, exc)
        _log.removeHandler(handler)
        raise self.retry(exc=exc, countdown=5)
    finally:
        try:
            os.remove(file_path)
        except OSError:
            pass
