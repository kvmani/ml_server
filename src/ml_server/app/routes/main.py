from flask import Blueprint, abort, jsonify, redirect, render_template

from ...catalog import tool_catalog
from ...tool_help import tool_help
from ..services.metrics import active_user_count

"""Public site routes such as the home page and help page."""

bp = Blueprint("main", __name__)


@bp.route("/")
def home():
    """Render the landing page."""
    return render_template(
        "home.html",
        tools=tool_catalog(),
        active_users=max(1, active_user_count()),
    )


@bp.route("/api/catalog")
def catalog():
    """Expose the reviewed catalog for integrations and smoke checks."""
    return jsonify({"status": "ok", "tools": tool_catalog()})


@bp.route("/api/active-users")
def active_users():
    """Expose an anonymized, approximate active visitor count for the landing page."""
    return jsonify({"status": "ok", "active_users": max(1, active_user_count())})


@bp.route("/help_faq")
@bp.route("/help/faq")
def help_faq():
    """Render the help and FAQ page."""
    return render_template("help_faq.html", tools=tool_catalog())


@bp.route("/tools/<tool_id>/help")
def scientific_help(tool_id: str):
    """Render the curated scientific guide for one released tool."""
    tools = {tool["id"]: tool for tool in tool_catalog()}
    tool = tools.get(tool_id)
    help_content = tool_help(tool_id)
    if tool is None or help_content is None:
        abort(404)
    external_help = None
    if help_content.get("external_help_suffix"):
        external_help = tool["href"].rstrip("/") + help_content["external_help_suffix"]
    return render_template(
        "tool_help.html",
        tool=tool,
        help_content=help_content,
        external_help=external_help,
    )


@bp.route("/pdf-tools", methods=["GET"])
def pdf_tools_home():
    """Render the landing page for PDF Tools."""
    return redirect("/pdf_tools/")
