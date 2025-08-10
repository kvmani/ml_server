"""Example of registering an embedded plugin."""

from flask import Blueprint

from ml_server.app.server import create_app
from ml_server.plugins import PluginRegistry


def create_blueprint(config):
    bp = Blueprint("dummy", __name__)

    @bp.get("/health")
    def health():
        return {"status": "ok"}

    @bp.get("/info")
    def info():
        return {
            "name": "dummy",
            "version": "0.1",
            "description": "demo",
            "homepage": "",
            "authors": [],
            "capabilities": [],
            "api_version": "v1",
        }

    @bp.get("/metrics")
    def metrics():
        return {
            "tool": "dummy",
            "version": "0.1",
            "uptime_s": 1,
            "counters": {},
            "gauges": {},
            "timers": {},
        }

    return bp


app = create_app(startup=False)
registry = PluginRegistry(app)
registry.register_embedded("dummy", create_blueprint, "/dummy")
app.extensions["plugin_registry"] = registry

if __name__ == "__main__":
    app.run(port=5000)
