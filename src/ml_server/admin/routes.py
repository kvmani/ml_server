"""Admin endpoints to display plugin status."""
from __future__ import annotations

from typing import Any, Dict, List

from flask import Blueprint, current_app, render_template, request

bp = Blueprint("admin_plugins", __name__, url_prefix="/admin/plugins")


@bp.get("/")
def plugin_status() -> Any:
    """Render a simple table of registered plugins and their status."""
    token = request.args.get("token")
    admin_token = current_app.config.get("ADMIN_TOKEN")
    if not admin_token or token != admin_token:
        return "Unauthorized", 401

    registry = current_app.config.get("PLUGIN_REGISTRY")
    plugins: List[Dict[str, Any]] = []
    if registry:
        for name in registry.list_tools():
            plugins.append(
                {
                    "name": name,
                    "health": registry.health(name),
                    "info": registry.info(name),
                    "metrics": registry.metrics(name),
                }
            )
    return render_template("admin_plugins.html", plugins=plugins)
