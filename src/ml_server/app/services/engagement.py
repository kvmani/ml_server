from __future__ import annotations

"""Persistent feedback and lightweight, anonymous first-party usage analytics.

Privacy contract
----------------
The portal tells every visitor that no personal information is collected or
stored, so this module must not persist anything that identifies a person or a
machine. Client IP addresses and full ``User-Agent`` strings are therefore never
written to the database. Support still needs to know which browsers are in use,
so the user agent is reduced to a coarse, non-identifying browser family before
it is stored. The legacy ``ip_address``/``user_agent`` columns are retained only
so existing deployments keep opening; they are always left empty.
"""

import json
import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_BROWSER_FAMILIES = (
    ("Edge", ("edg/", "edge/", "edga/", "edgios/")),
    ("Opera", ("opr/", "opera")),
    ("Chrome", ("chrome/", "crios/", "chromium")),
    ("Firefox", ("firefox/", "fxios/")),
    ("Safari", ("safari/",)),
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def browser_family(user_agent: str | None) -> str:
    """Reduce a User-Agent string to a coarse, non-identifying browser family.

    Only the family name is ever stored, so the result cannot be used to
    fingerprint or re-identify a visitor.
    """
    candidate = (user_agent or "").lower()
    if not candidate:
        return "Unknown"
    for family, markers in _BROWSER_FAMILIES:
        if any(marker in candidate for marker in markers):
            return family
    return "Other"


def _connect(database_path: str) -> sqlite3.Connection:
    path = Path(database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=5)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 5000")
    return connection


def initialize_database(database_path: str) -> None:
    """Create the small, append-oriented engagement database if needed."""
    with _connect(database_path) as connection:
        connection.execute("PRAGMA journal_mode = WAL")
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS feedback_submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kind TEXT NOT NULL CHECK (kind IN ('feedback', 'feature_request')),
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                message TEXT NOT NULL,
                tool_id TEXT,
                tool_name TEXT NOT NULL,
                page_url TEXT,
                ip_address TEXT,
                user_agent TEXT,
                created_at TEXT NOT NULL,
                acknowledgement_email_status TEXT NOT NULL DEFAULT 'not_requested',
                developer_email_status TEXT NOT NULL DEFAULT 'not_requested'
            );
            CREATE INDEX IF NOT EXISTS feedback_created_at_idx
                ON feedback_submissions(created_at DESC);

            CREATE TABLE IF NOT EXISTS analytics_sessions (
                session_id TEXT PRIMARY KEY,
                -- Retained for backward compatibility with existing databases
                -- and deliberately always NULL; see the module privacy contract.
                ip_address TEXT,
                user_agent TEXT,
                browser_family TEXT,
                started_at TEXT NOT NULL,
                last_seen_at TEXT NOT NULL,
                duration_ms INTEGER NOT NULL DEFAULT 0,
                last_tool_id TEXT,
                last_tool_name TEXT
            );
            CREATE INDEX IF NOT EXISTS analytics_sessions_last_seen_idx
                ON analytics_sessions(last_seen_at DESC);

            CREATE TABLE IF NOT EXISTS analytics_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                event_name TEXT NOT NULL,
                tool_id TEXT,
                tool_name TEXT,
                path TEXT,
                duration_ms INTEGER,
                status_code INTEGER,
                metadata_json TEXT,
                occurred_at TEXT NOT NULL,
                FOREIGN KEY(session_id) REFERENCES analytics_sessions(session_id)
            );
            CREATE INDEX IF NOT EXISTS analytics_events_time_idx
                ON analytics_events(occurred_at DESC);
            CREATE INDEX IF NOT EXISTS analytics_events_session_idx
                ON analytics_events(session_id, occurred_at);
            """
        )
        _migrate_to_anonymous_analytics(connection)


def _migrate_to_anonymous_analytics(connection: sqlite3.Connection) -> None:
    """Add the browser-family column and erase any previously stored identifiers.

    Deployments created before the privacy contract was tightened may still hold
    IP addresses and full user-agent strings. Clearing them here means upgrading
    the portal is what makes the stated privacy guarantee true, rather than an
    extra manual step an operator could forget.
    """
    columns = {
        row["name"] for row in connection.execute("PRAGMA table_info(analytics_sessions)")
    }
    if "browser_family" not in columns:
        connection.execute("ALTER TABLE analytics_sessions ADD COLUMN browser_family TEXT")
    connection.execute(
        "UPDATE analytics_sessions SET ip_address = NULL, user_agent = NULL "
        "WHERE ip_address IS NOT NULL OR user_agent IS NOT NULL"
    )
    connection.execute(
        "UPDATE feedback_submissions SET ip_address = NULL, user_agent = NULL "
        "WHERE ip_address IS NOT NULL OR user_agent IS NOT NULL"
    )


def save_feedback(database_path: str, submission: dict[str, Any]) -> int:
    """Persist a feedback submission.

    Only what the visitor deliberately typed is stored. Any ``ip_address`` or
    ``user_agent`` present in ``submission`` is intentionally discarded.
    """
    with _connect(database_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO feedback_submissions
                (kind, name, email, message, tool_id, tool_name, page_url,
                 created_at,
                 acknowledgement_email_status, developer_email_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                submission["kind"],
                submission["name"],
                submission["email"],
                submission["message"],
                submission.get("tool_id"),
                submission["tool_name"],
                submission.get("page_url"),
                submission.get("created_at", utc_now()),
                submission.get("acknowledgement_email_status", "not_requested"),
                submission.get("developer_email_status", "not_requested"),
            ),
        )
        return int(cursor.lastrowid)


def update_feedback_email_status(
    database_path: str, feedback_id: int, *, acknowledgement: str, developer: str
) -> None:
    try:
        with _connect(database_path) as connection:
            connection.execute(
                """UPDATE feedback_submissions
                   SET acknowledgement_email_status = ?, developer_email_status = ?
                   WHERE id = ?""",
                (acknowledgement, developer, feedback_id),
            )
    except Exception:  # email status is advisory and must never affect submission
        logger.warning("Could not update feedback email status", exc_info=True)


def list_feedback(
    database_path: str, *, limit: int = 100, offset: int = 0
) -> list[dict[str, Any]]:
    with _connect(database_path) as connection:
        rows = connection.execute(
            "SELECT * FROM feedback_submissions ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
    return [dict(row) for row in rows]


def record_event(
    database_path: str,
    *,
    session_id: str,
    user_agent: str | None = None,
    event_name: str,
    tool_id: str | None = None,
    tool_name: str | None = None,
    path: str | None = None,
    duration_ms: int | None = None,
    status_code: int | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    now = utc_now()
    safe_duration = max(0, min(int(duration_ms or 0), 86_400_000))
    family = browser_family(user_agent)
    with _connect(database_path) as connection:
        connection.execute(
            """
            INSERT INTO analytics_sessions
                (session_id, browser_family, started_at, last_seen_at,
                 duration_ms, last_tool_id, last_tool_name)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(session_id) DO UPDATE SET
                browser_family = COALESCE(
                    excluded.browser_family, analytics_sessions.browser_family
                ),
                last_seen_at = excluded.last_seen_at,
                duration_ms = MAX(analytics_sessions.duration_ms, excluded.duration_ms),
                last_tool_id = COALESCE(excluded.last_tool_id, analytics_sessions.last_tool_id),
                last_tool_name = COALESCE(
                    excluded.last_tool_name, analytics_sessions.last_tool_name
                )
            """,
            (session_id, family, now, now, safe_duration, tool_id, tool_name),
        )
        connection.execute(
            """
            INSERT INTO analytics_events
                (session_id, event_name, tool_id, tool_name, path, duration_ms,
                 status_code, metadata_json, occurred_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                event_name,
                tool_id,
                tool_name,
                path,
                safe_duration if duration_ms is not None else None,
                status_code,
                json.dumps(metadata or {}, separators=(",", ":")),
                now,
            ),
        )


def analytics_summary(database_path: str) -> dict[str, Any]:
    """Return compact admin-facing totals without exposing raw data publicly."""
    with _connect(database_path) as connection:
        totals = connection.execute(
            """SELECT COUNT(*) AS sessions,
                      COALESCE(AVG(duration_ms), 0) AS average_session_ms
               FROM analytics_sessions"""
        ).fetchone()
        tools = connection.execute(
            """SELECT COALESCE(tool_name, 'Portal') AS tool_name, COUNT(*) AS uses,
                      ROUND(AVG(CASE WHEN event_name = 'request'
                                     THEN duration_ms END), 1) AS average_action_ms
               FROM analytics_events
               WHERE event_name IN ('tool_open', 'request')
               GROUP BY COALESCE(tool_name, 'Portal')
               ORDER BY uses DESC LIMIT 20"""
        ).fetchall()
        recent = connection.execute(
            """SELECT session_id, browser_family, started_at, last_seen_at, duration_ms,
                      last_tool_name
               FROM analytics_sessions ORDER BY last_seen_at DESC LIMIT 20"""
        ).fetchall()
        browsers = connection.execute(
            """SELECT COALESCE(browser_family, 'Unknown') AS browser_family,
                      COUNT(*) AS sessions
               FROM analytics_sessions
               GROUP BY COALESCE(browser_family, 'Unknown')
               ORDER BY sessions DESC"""
        ).fetchall()
    return {
        "sessions": int(totals["sessions"]),
        "average_session_ms": round(float(totals["average_session_ms"]), 1),
        "tools": [dict(row) for row in tools],
        "recent_sessions": [dict(row) for row in recent],
        "browsers": [dict(row) for row in browsers],
    }
