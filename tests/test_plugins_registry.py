from __future__ import annotations

from flask import Flask, Blueprint, jsonify
import responses

from ml_server.plugins import PluginRegistry


def create_dummy_blueprint(config):
    bp = Blueprint("dummy", __name__)

    @bp.get("/health")
    def health():
        return jsonify(status="ok", version="1.0", uptime_s=1)

    @bp.get("/info")
    def info():
        return jsonify(
            name="dummy",
            version="1.0",
            description="test",
            homepage="",
            authors=[],
            capabilities=[],
            api_version="v1",
        )

    @bp.get("/metrics")
    def metrics():
        return jsonify(tool="dummy", version="1.0", uptime_s=1, counters={}, gauges={}, timers={})

    return bp


def test_remote_plugin_polling():
    registry = PluginRegistry()
    registry.register_remote("pdf", "http://example.com/pdf")
    with responses.RequestsMock() as rsps:
        rsps.get(
            "http://example.com/pdf/health",
            json={"status": "ok", "version": "1.0", "uptime_s": 1},
        )
        rsps.get(
            "http://example.com/pdf/info",
            json={
                "name": "pdf",
                "version": "1.0",
                "description": "test",
                "homepage": "",
                "authors": [],
                "capabilities": [],
                "api_version": "v1",
            },
        )
        rsps.get(
            "http://example.com/pdf/metrics",
            json={
                "tool": "pdf",
                "version": "1.0",
                "uptime_s": 1,
                "counters": {},
                "gauges": {},
                "timers": {},
            },
        )
        assert registry.health("pdf").status == "ok"
        assert registry.info("pdf").name == "pdf"
        assert registry.metrics("pdf").tool == "pdf"


def test_embedded_plugin_polling():
    app = Flask(__name__)
    registry = PluginRegistry(app)
    registry.register_embedded("dummy", create_dummy_blueprint, "/dummy")
    assert registry.health("dummy").status == "ok"
    assert registry.info("dummy").name == "dummy"
    assert registry.metrics("dummy").tool == "dummy"
