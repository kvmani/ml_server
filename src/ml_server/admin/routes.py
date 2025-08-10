from __future__ import annotations

"""Admin routes for displaying plugin status."""

from flask import Blueprint, current_app, render_template, request

from ..plugins import PluginRegistry

bp = Blueprint("plugin_admin", __name__, url_prefix="/admin/plugins")


@bp.route("/")
def plugins_dashboard():
    registry: PluginRegistry | None = current_app.extensions.get("plugin_registry")
    tools = []
    if registry:
        for tool in registry.list_tools():
            tools.append(
                {
                    "name": tool.name,
                    "health": registry.health(tool.name),
                    "info": registry.info(tool.name),
                    "metrics": registry.metrics(tool.name),
                }
            )
    return render_template("admin_plugins.html", tools=tools)


@bp.before_request
def _check_token():
    token = request.args.get("token")
    admin_token = current_app.config.get("ADMIN_TOKEN")
    if not admin_token or token != admin_token:
        return "Unauthorized", 401


__all__ = ["bp"]
