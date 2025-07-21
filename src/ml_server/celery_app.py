"""Celery application setup."""

from __future__ import annotations

from flask import Flask
from celery import Celery
from celery.signals import worker_process_init

from .app.services.graceful import install_signal_handlers
from .config import Config

celery_app = Celery("microstructure_tasks")


@worker_process_init.connect
def _init_worker(**_kwargs) -> None:  # pragma: no cover - side effect only
    install_signal_handlers()


def celery_init_app(app: Flask) -> Celery:
    """Configure Celery using Flask app context."""
    cfg = Config()
    celery_app.conf.update(
        broker_url=cfg.celery_settings.get("broker_url", "redis://redis:6379/0"),
        result_backend=cfg.celery_settings.get(
            "result_backend", "redis://redis:6379/0"
        ),
        task_default_queue="default",
    )
    celery_app.set_default()
    app.extensions["celery"] = celery_app
    return celery_app
