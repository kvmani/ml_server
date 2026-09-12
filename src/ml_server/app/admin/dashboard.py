from __future__ import annotations

"""The admin dashboard: a password-protected operations console.

The page itself is a thin shell. Every number on it comes from the JSON API in
this module, which lets the browser refresh the live panel every few seconds
without re-rendering anything else, and lets an operator or a script curl the
same figures directly.
"""

import logging
from typing import Any

from flask import Blueprint, current_app, jsonify, redirect, render_template, request, url_for

from ... import __version__
from ...catalog import tool_catalog
from ...celery_app import celery_app
from ...config import Config
from ..services import diagnostics as diag
from ..services.analytics import DEFAULT_WINDOW, WINDOWS, analytics_report
from ..services.engagement import database_stats, list_feedback, prune_analytics
from ..services.live_activity import live_activity
from ..services.logs import LEVELS, read_log
from ..services.metrics import metrics_response, visit_summary
from .auth import (
    admin_access_configured,
    attempt_limiter,
    csrf_token,
    csrf_token_valid,
    end_session,
    is_authenticated,
    login_required,
    start_session,
    verify_password,
)

logger = logging.getLogger(__name__)

bp = Blueprint("admin", __name__, url_prefix="/admin")

#: Records returned by the log API in one page, and the ceiling on a request.
DEFAULT_LOG_LIMIT = 300
MAX_LOG_LIMIT = 2000


def _database_path() -> str:
    return str(current_app.config["ENGAGEMENT_DATABASE"])


def _log_settings() -> tuple[str, str]:
    logging_settings = Config().logging_settings
    return (
        str(logging_settings.get("log_dir", "logs")),
        str(logging_settings.get("log_file", "app.log")),
    )


def _requested_window() -> str:
    window = request.args.get("window", DEFAULT_WINDOW)
    return window if window in WINDOWS else DEFAULT_WINDOW


def _requested_months() -> int:
    """Months of history for the unique-visitor trend, chosen by the operator."""
    try:
        months = int(request.args.get("months", 6))
    except (TypeError, ValueError):
        months = 6
    return max(1, min(months, 120))


# --------------------------------------------------------------------------
# Authentication
# --------------------------------------------------------------------------
def _log_csrf_failure() -> None:
    """Record why a login POST was rejected, in enough detail to fix it.

    A rejected token has exactly two interesting causes, and they need
    different remedies: the browser sent no session cookie back (a cookie the
    browser refused to store or return -- the Secure-over-HTTP failure), or it
    sent a session that holds no token (a session signed with a different key,
    i.e. another worker or a restart). Saying which one happened is the whole
    point; without it an operator is left reading "expired" and guessing.

    Nothing secret is logged: not the token, not the session contents, not the
    admin credential. Only the shape of the failure.
    """
    from flask import session

    cookie_name = current_app.config.get("SESSION_COOKIE_NAME") or "session"
    had_session_cookie = cookie_name in request.cookies
    if not had_session_cookie:
        reason = "no session cookie was returned by the browser"
    elif not session.get("ml_admin_csrf"):
        reason = (
            "the session cookie carried no CSRF token, so it was not the session that "
            "rendered the form (a different worker's signing key, or a restart)"
        )
    elif not request.form.get("csrf_token"):
        reason = "the form was posted without a csrf_token field"
    else:
        reason = "the submitted token did not match the one held in the session"

    logger.warning(
        "Admin CSRF check failed on %s: %s [scheme=%s secure_cookie=%s samesite=%s "
        "ssl_enabled=%s session_cookie_present=%s]",
        request.path,
        reason,
        request.scheme,
        current_app.config.get("SESSION_COOKIE_SECURE"),
        current_app.config.get("SESSION_COOKIE_SAMESITE"),
        current_app.config.get("SSL_ENABLED"),
        had_session_cookie,
    )
    if current_app.config.get("SESSION_COOKIE_SECURE") and request.scheme != "https":
        logger.error(
            "The session cookie is marked Secure but this request arrived over %s, so no "
            "browser will ever return it. Set security.ssl_enabled=false in %s for a "
            "plain-HTTP intranet deployment, then restart the portal.",
            request.scheme,
            current_app.config.get("CONFIG_PATH", "the portal configuration"),
        )


@bp.route("/login", methods=["GET", "POST"])
def login():
    """Render and process the admin password form."""
    if is_authenticated() and request.method == "GET":
        return redirect(url_for("admin.index"))

    address = request.remote_addr or "unknown"
    error = None
    if not admin_access_configured():
        error = (
            "Admin access is not configured on this server. Set "
            "ML_SERVER_ADMIN_PASSWORD_HASH (or ML_SERVER_ADMIN_PASSWORD) in the "
            "service environment and restart the portal."
        )
    elif request.method == "POST":
        locked_for = attempt_limiter.locked_for(address)
        if locked_for:
            error = f"Too many failed attempts. Try again in {locked_for // 60 + 1} minute(s)."
        elif not csrf_token_valid(request.form.get("csrf_token")):
            _log_csrf_failure()
            error = (
                "This form expired. Reload the sign-in page and try again. If it keeps "
                "happening, the server log records why -- see the runbook's "
                '"Page expired" section.'
            )
        elif verify_password(request.form.get("password", "")):
            attempt_limiter.clear(address)
            start_session()
            logger.info("Admin login succeeded")
            target = request.args.get("next") or request.form.get("next") or ""
            # Only ever redirect within this site: an attacker-supplied absolute
            # URL here would turn the login page into an open redirect.
            if target.startswith("/") and not target.startswith("//"):
                return redirect(target)
            return redirect(url_for("admin.index"))
        else:
            remaining = attempt_limiter.record_failure(address)
            logger.warning("Admin login failed from %s", address)
            error = "Incorrect password."
            if remaining <= 2:
                error += f" {max(0, remaining)} attempt(s) left before a temporary lockout."

    response = current_app.make_response(
        render_template(
            "admin_login.html",
            error=error,
            csrf_token=csrf_token(),
            configured=admin_access_configured(),
            next=request.args.get("next", ""),
            version=__version__,
        )
    )
    # A wrong password must never be cached and replayed as a "successful" page.
    response.headers["Cache-Control"] = "no-store"
    return response


@bp.route("/logout", methods=["GET", "POST"])
def logout():
    end_session()
    return redirect(url_for("main.home"))


# --------------------------------------------------------------------------
# Pages
# --------------------------------------------------------------------------
@bp.route("/")
@login_required
def index():
    """Render the dashboard shell; the panels fetch their own data."""
    return render_template(
        "admin_dashboard.html",
        version=__version__,
        windows=list(WINDOWS),
        default_window=DEFAULT_WINDOW,
        levels=LEVELS,
        tools=tool_catalog(),
    )


@bp.route("/feedback")
@login_required
def feedback():
    page = max(1, request.args.get("page", 1, type=int))
    entries = list_feedback(_database_path(), limit=25, offset=(page - 1) * 25)
    return render_template("admin_feedback.html", feedback=entries, page=page)


# --------------------------------------------------------------------------
# JSON API
# --------------------------------------------------------------------------
@bp.get("/api/live")
@login_required
def api_live():
    """Who is using which service right now, from the in-memory registry."""
    snapshot = live_activity.snapshot()
    snapshot["status"] = "ok"
    snapshot["uptime"] = diag.uptime_report(current_app.start_time)
    return jsonify(snapshot)


@bp.get("/api/overview")
@login_required
def api_overview():
    report = analytics_report(
        _database_path(), window=_requested_window(), months=_requested_months()
    )
    report["status"] = "ok"
    report["uptime"] = diag.uptime_report(current_app.start_time)
    report["live"] = {
        "active_clients": live_activity.active_client_count(),
        "window_seconds": live_activity.ttl_seconds,
    }
    report["endpoint_visits"] = visit_summary()
    report["storage"] = database_stats(_database_path())
    return jsonify(report)


@bp.get("/api/diagnostics")
@login_required
def api_diagnostics():
    log_dir, log_file = _log_settings()
    application = diag.application_report(current_app)
    return jsonify(
        {
            "status": "ok",
            "uptime": diag.uptime_report(current_app.start_time),
            "host": diag.host_report(),
            "application": application,
            "disks": diag.disk_report(
                [application["working_directory"], application["database_path"], log_dir]
            ),
            "dependencies": diag.dependency_report(celery_app),
            "storage": database_stats(_database_path()),
            "catalog": [
                {
                    "id": tool["id"],
                    "name": tool["name"],
                    "state": tool["state"],
                    "internal": tool["internal"],
                    "href": tool["href"],
                }
                for tool in tool_catalog()
            ],
        }
    )


@bp.get("/api/logs")
@login_required
def api_logs():
    log_dir, log_file = _log_settings()
    try:
        limit = int(request.args.get("limit", DEFAULT_LOG_LIMIT))
    except (TypeError, ValueError):
        limit = DEFAULT_LOG_LIMIT
    payload = read_log(
        log_dir,
        log_file,
        level=request.args.get("level", "ALL"),
        search=request.args.get("search", "")[:200],
        limit=max(1, min(limit, MAX_LOG_LIMIT)),
    )
    payload["status"] = "ok"
    return jsonify(payload)


@bp.get("/api/metrics")
@login_required
def api_metrics():
    """The raw Prometheus exposition text, for the diagnostics panel."""
    body, _status, _headers = metrics_response()
    return jsonify({"status": "ok", "metrics": body.decode("utf-8", errors="replace")})


@bp.get("/api/feedback")
@login_required
def api_feedback():
    limit = max(1, min(request.args.get("limit", 25, type=int) or 25, 200))
    entries = list_feedback(_database_path(), limit=limit)
    return jsonify({"status": "ok", "feedback": entries})


@bp.get("/api/export")
@login_required
def api_export():
    """Download the current analytics report as a JSON file."""
    report = analytics_report(
        _database_path(), window=_requested_window(), months=_requested_months()
    )
    report["exported_by"] = "ml_server admin dashboard"
    report["version"] = __version__
    response = jsonify(report)
    response.headers[
        "Content-Disposition"
    ] = f"attachment; filename=ml-server-analytics-{report['window']}.json"
    return response


@bp.post("/api/prune")
@login_required
def api_prune():
    """Apply the analytics retention policy on demand."""
    payload: dict[str, Any] = request.get_json(silent=True) or {}
    try:
        months = int(payload.get("retention_months", 24))
    except (TypeError, ValueError):
        months = 24
    result = prune_analytics(_database_path(), retention_months=max(1, min(months, 120)))
    logger.info("Analytics pruned before %s", result["cutoff"])
    return jsonify({"status": "ok", **result})


def init_admin(app) -> None:
    """Register the admin blueprint on ``app``."""
    app.register_blueprint(bp)
