from __future__ import annotations

"""Feedback, feature-request, and browser analytics endpoints."""

import logging
import re
from email.utils import parseaddr

from flask import Blueprint, current_app, g, jsonify, render_template, request

from ...catalog import tool_catalog
from ..services.email_notifications import dispatch_feedback_emails
from ..services.engagement import list_feedback, record_event, save_feedback, utc_now

bp = Blueprint("feedback", __name__)
logger = logging.getLogger(__name__)
_SESSION_ID_RE = re.compile(r"^[A-Za-z0-9_-]{16,80}$")


def _database_path() -> str:
    return str(current_app.config["ENGAGEMENT_DATABASE"])


def _clean(value: object, limit: int) -> str:
    return str(value or "").strip()[:limit]


def _valid_email(value: str) -> bool:
    parsed = parseaddr(value)[1]
    return parsed == value and "@" in parsed and len(parsed) <= 254


def _resolve_tool(tool_id: str) -> tuple[str | None, str]:
    tools = {tool["id"]: tool["name"] for tool in tool_catalog()}
    if tool_id in tools:
        return tool_id, tools[tool_id]
    return None, "Scientific Tools Portal"


@bp.route("/submit_feedback", methods=["POST"])
def submit_feedback():
    """Validate and persist a feedback or feature-request submission."""
    payload = request.get_json(silent=True) or request.form
    message = _clean(payload.get("message") or payload.get("feedback"), 5000)
    name = _clean(payload.get("name"), 120)
    email = _clean(payload.get("email"), 254)
    kind = _clean(payload.get("kind") or "feedback", 32)
    tool_id, tool_name = _resolve_tool(_clean(payload.get("tool_id"), 80))

    if kind not in {"feedback", "feature_request"}:
        return jsonify({"success": False, "message": "Invalid submission type"}), 400
    if not name or not email or not message:
        return jsonify({"success": False, "message": "Name, email, and message are required"}), 400
    if not _valid_email(email):
        return jsonify({"success": False, "message": "Enter a valid email address"}), 400
    if _clean(payload.get("website"), 200):
        return jsonify({"success": True})

    submission = {
        "kind": kind,
        "name": name,
        "email": email,
        "message": message,
        "tool_id": tool_id,
        "tool_name": tool_name,
        "page_url": _clean(payload.get("page_url") or request.referrer, 1000),
        "created_at": utc_now(),
        "acknowledgement_email_status": (
            "pending"
            if current_app.config["EMAIL_SETTINGS"].get("enabled")
            else "not_requested"
        ),
        "developer_email_status": (
            "pending"
            if current_app.config["EMAIL_SETTINGS"].get("enabled")
            else "not_requested"
        ),
    }
    try:
        feedback_id = save_feedback(_database_path(), submission)
    except Exception:
        logger.exception("Feedback persistence failed")
        return jsonify({"success": False, "message": "Could not save your message"}), 500

    dispatch_feedback_emails(
        database_path=_database_path(), feedback_id=feedback_id,
        submission=submission, settings=current_app.config["EMAIL_SETTINGS"]
    )
    return jsonify({"success": True, "reference": feedback_id}), 201


@bp.route("/api/analytics/event", methods=["POST"])
def analytics_event():
    """Accept a deliberately small allow-list of first-party browser events."""
    payload = request.get_json(silent=True) or {}
    event_name = _clean(payload.get("event_name"), 40)
    if event_name not in {"page_view", "tool_open", "heartbeat", "session_end", "major_action"}:
        return jsonify({"success": False, "message": "Invalid event"}), 400
    session_id = getattr(g, "analytics_session_id", "")
    if not _SESSION_ID_RE.fullmatch(session_id):
        return jsonify({"success": False, "message": "Invalid session"}), 400
    tool_id, tool_name = _resolve_tool(_clean(payload.get("tool_id"), 80))
    try:
        record_event(
            _database_path(), session_id=session_id,
            user_agent=request.user_agent.string,
            event_name=event_name, tool_id=tool_id,
            tool_name=tool_name if tool_id else None,
            path=_clean(payload.get("path"), 1000),
            duration_ms=int(payload.get("duration_ms") or 0),
            metadata={"visibility": _clean(payload.get("visibility"), 20)},
        )
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "Invalid duration"}), 400
    except Exception:
        logger.warning("Browser analytics event could not be stored", exc_info=True)
    return jsonify({"success": True})


@bp.route("/admin/feedback")
def admin_feedback():
    """Render stored feedback entries for admins."""
    token = request.args.get("token")
    admin_token = current_app.config.get("ADMIN_TOKEN")
    if not admin_token or token != admin_token:
        return "Unauthorized", 401

    page = max(1, request.args.get("page", 1, type=int))
    entries = list_feedback(_database_path(), limit=10, offset=(page - 1) * 10)
    return render_template("admin_feedback.html", feedback=entries, page=page, token=token)
