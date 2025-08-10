from __future__ import annotations

from typing import Any, Dict

import requests
from flask import Blueprint, Flask

from ml_server.plugins.registry import PluginRegistry
from ml_server.plugins.schemas import HealthV1, InfoV1, MetricsV1


def test_remote_plugin_health(monkeypatch: Any) -> None:
    registry = PluginRegistry()
    registry.register_remote("pdf", "http://example.com")

    class Resp:
        def __init__(self, data: Dict[str, Any]):
            self._data = data

        def raise_for_status(self) -> None:
            return None

        def json(self) -> Dict[str, Any]:
            return self._data

    def fake_get(url: str, timeout: int) -> Resp:
        assert url.endswith("/health")
        return Resp({"status": "ok", "version": "1", "uptime_s": 1})

    monkeypatch.setattr(requests, "get", fake_get)
    health = registry.health("pdf")
    assert isinstance(health, HealthV1)
    assert health.status == "ok"


def _create_dummy_blueprint(config: Dict[str, Any]) -> Blueprint:
    bp = Blueprint("dummy", __name__)

    @bp.get("/health")
    def _h() -> Dict[str, Any]:
        return {"status": "ok", "version": "1", "uptime_s": 1}

    @bp.get("/info")
    def _i() -> Dict[str, Any]:
        return {
            "name": "dummy",
            "version": "1",
            "description": "",
            "homepage": "",
            "authors": [],
            "capabilities": [],
            "api_version": "v1",
        }

    @bp.get("/metrics")
    def _m() -> Dict[str, Any]:
        return {
            "tool": "dummy",
            "version": "1",
            "uptime_s": 1,
            "counters": {},
            "gauges": {},
            "timers": {},
        }

    return bp


def test_embedded_plugin(monkeypatch: Any) -> None:
    app = Flask(__name__)
    registry = PluginRegistry(app)
    registry.register_embedded(
        "dummy", "tests.test_plugins_registry:_create_dummy_blueprint", "/dummy"
    )
    with app.app_context():
        health = registry.health("dummy")
        info = registry.info("dummy")
        metrics = registry.metrics("dummy")
    assert isinstance(health, HealthV1)
    assert isinstance(info, InfoV1)
    assert isinstance(metrics, MetricsV1)
