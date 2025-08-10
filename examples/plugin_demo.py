"""Example application loading tools from the example config."""
from __future__ import annotations

import os

from flask import Flask

from ml_server.admin.routes import bp as admin_plugins_bp
from ml_server.plugins.registry import PluginRegistry


def create_demo_app() -> Flask:
    app = Flask(__name__)
    config_path = os.path.join(os.path.dirname(__file__), "../config/tools.example.yaml")
    registry = PluginRegistry.from_file(config_path, app)
    app.config["PLUGIN_REGISTRY"] = registry
    app.config["ADMIN_TOKEN"] = "dev"
    app.register_blueprint(admin_plugins_bp)

    @app.get("/")
    def index():
        statuses = {
            name: registry.health(name).model_dump() if registry.health(name) else {}
            for name in registry.list_tools()
        }
        return statuses

    return app


if __name__ == "__main__":
    app = create_demo_app()
    app.run(debug=True)
