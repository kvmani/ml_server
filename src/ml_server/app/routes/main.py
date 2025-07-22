from flask import Blueprint, render_template

"""Public site routes such as the home page and help page."""

bp = Blueprint("main", __name__)


@bp.route("/")
def home():
    """Render the landing page."""
    return render_template("home.html")


@bp.route("/help_faq")
def help_faq():
    """Render the help and FAQ page."""
    return render_template("help_faq.html")
