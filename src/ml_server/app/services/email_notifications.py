from __future__ import annotations

"""Best-effort, optional SMTP notifications for feedback submissions."""

import logging
import smtplib
import threading
from email.message import EmailMessage
from typing import Any

from .engagement import update_feedback_email_status

logger = logging.getLogger(__name__)


def _send(settings: dict[str, Any], recipient: str, subject: str, body: str) -> bool:
    try:
        host = str(settings.get("smtp_host") or "").strip()
        if not host:
            raise ValueError("SMTP host is not configured")
        message = EmailMessage()
        message["From"] = settings.get("from_address") or "noreply@intranet.local"
        message["To"] = recipient
        message["Subject"] = subject
        message.set_content(body)
        with smtplib.SMTP(
            host, int(settings.get("smtp_port", 25)), timeout=10
        ) as server:
            if settings.get("use_tls", False):
                server.starttls()
            username = settings.get("username")
            password = settings.get("password")
            if bool(username) != bool(password):
                raise ValueError("SMTP authentication requires both username and password")
            if username and password:
                server.login(username, password)
            server.send_message(message)
        return True
    except Exception:
        logger.warning("Optional feedback email to %s failed", recipient, exc_info=True)
        return False


def dispatch_feedback_emails(
    *, database_path: str, feedback_id: int, submission: dict[str, Any], settings: dict[str, Any]
) -> None:
    """Return immediately; SMTP work runs in a daemon thread and never raises to callers."""
    if not settings.get("enabled", False):
        return

    def deliver() -> None:
        kind_label = "feature request" if submission["kind"] == "feature_request" else "feedback"
        ack_ok = _send(
            settings,
            submission["email"],
            f"We received your {kind_label}",
            (
                f"Hello {submission['name']},\n\n"
                f"Thank you. Your {kind_label} for {submission['tool_name']} was received "
                f"as reference #{feedback_id}.\n\n"
                "This is an automated acknowledgement; no reply is required."
            ),
        )
        developer = settings.get("developer_address", "kvmani@barc.gov.in")
        developer_ok = _send(
            settings,
            developer,
            f"[{submission['tool_name']}] New {kind_label} #{feedback_id}",
            (
                f"Type: {kind_label}\nName: {submission['name']}\n"
                f"Email: {submission['email']}\nTool: {submission['tool_name']}\n"
                f"Date: {submission['created_at']}\n"
                f"Page: {submission.get('page_url') or 'not recorded'}\n\n"
                f"{submission['message']}"
            ),
        )
        update_feedback_email_status(
            database_path,
            feedback_id,
            acknowledgement="sent" if ack_ok else "failed",
            developer="sent" if developer_ok else "failed",
        )

    threading.Thread(target=deliver, name=f"feedback-email-{feedback_id}", daemon=True).start()
