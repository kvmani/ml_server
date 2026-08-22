from flask import Blueprint, jsonify, redirect, render_template

from ...catalog import tool_catalog
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
def help_faq():
    """Render the help and FAQ page."""
    return render_template("help_faq.html")


@bp.route("/pdf-tools", methods=["GET"])
def pdf_tools_home():
    """Render the landing page for PDF Tools."""
    return redirect("/pdf_tools/")
