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

Counting *distinct* visitors over a period still requires telling one client
from another, so each row carries ``client_hash``: an HMAC-SHA256 digest of the
address keyed with the server secret. It is irreversible without that key, is
never displayed, and is only ever used with ``COUNT(DISTINCT ...)``. Live IP
addresses, when an administrator needs them during an incident, are held in
process memory only -- see :mod:`ml_server.app.services.live_activity`.
"""

import hashlib
import hmac
import json
import logging
import re
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

# Only the major version number is ever kept (e.g. "120"), never the full
# dotted version or any other UA token, so it stays a coarse, non-identifying
# bucket in the same spirit as the browser family.
_VERSION_MARKERS = {
    "Edge": ("edg/", "edge/", "edga/", "edgios/"),
    "Opera": ("opr/",),
    "Chrome": ("chrome/", "crios/", "chromium/"),
    "Firefox": ("firefox/", "fxios/"),
    "Safari": ("version/",),
}


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


def browser_major_version(user_agent: str | None, family: str | None = None) -> str | None:
    """Return only the major version number for ``family`` (e.g. ``"120"``).

    Never returns the full dotted version or any other token from the
    User-Agent string, so it cannot be used to fingerprint a visitor any more
    precisely than :func:`browser_family` already does.
    """
    candidate = (user_agent or "").lower()
    if not candidate:
        return None
    family = family or browser_family(user_agent)
    for marker in _VERSION_MARKERS.get(family, ()):
        index = candidate.find(marker)
        if index == -1:
            continue
        match = re.match(r"(\d+)", candidate[index + len(marker) :])
        if match:
            return match.group(1)
    return None


def client_digest(ip_address: str | None, secret: str | bytes | None) -> str | None:
    """Return an irreversible per-client digest, or ``None`` without an address.

    Distinct-visitor counts need a stable token per client; they do not need the
    address itself. Keying the digest with the server secret means the stored
    value cannot be matched back to an address by anyone who only has the
    database file, and rotating the secret simply starts a new counting epoch.
    """
    address = (ip_address or "").strip()
    if not address:
        return None
    key = secret if isinstance(secret, bytes) else str(secret or "ml_server").encode("utf-8")
    return hmac.new(key, address.encode("utf-8"), hashlib.sha256).hexdigest()[:32]


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
                browser_major_version TEXT,
                client_hash TEXT,
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
                client_hash TEXT,
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
        # Indexes over migrated columns come last: an older database reaches the
        # statements above without a client_hash column, and creating an index
        # on a column that does not exist yet fails the whole upgrade.
        connection.executescript(
            """
            CREATE INDEX IF NOT EXISTS analytics_events_client_idx
                ON analytics_events(client_hash, occurred_at);
            CREATE INDEX IF NOT EXISTS analytics_events_tool_idx
                ON analytics_events(tool_name, occurred_at);
            CREATE INDEX IF NOT EXISTS analytics_sessions_client_idx
                ON analytics_sessions(client_hash);
            """
        )


def _migrate_to_anonymous_analytics(connection: sqlite3.Connection) -> None:
    """Add the browser-family column and erase any previously stored identifiers.

    Deployments created before the privacy contract was tightened may still hold
    IP addresses and full user-agent strings. Clearing them here means upgrading
    the portal is what makes the stated privacy guarantee true, rather than an
    extra manual step an operator could forget.
    """
    columns = {row["name"] for row in connection.execute("PRAGMA table_info(analytics_sessions)")}
    if "browser_family" not in columns:
        connection.execute("ALTER TABLE analytics_sessions ADD COLUMN browser_family TEXT")
    if "browser_major_version" not in columns:
        connection.execute("ALTER TABLE analytics_sessions ADD COLUMN browser_major_version TEXT")
    if "client_hash" not in columns:
        connection.execute("ALTER TABLE analytics_sessions ADD COLUMN client_hash TEXT")
    event_columns = {
        row["name"] for row in connection.execute("PRAGMA table_info(analytics_events)")
    }
    if "client_hash" not in event_columns:
        connection.execute("ALTER TABLE analytics_events ADD COLUMN client_hash TEXT")
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


def list_feedback(database_path: str, *, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
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
    client_hash: str | None = None,
) -> None:
    now = utc_now()
    safe_duration = max(0, min(int(duration_ms or 0), 86_400_000))
    family = browser_family(user_agent)
    version = browser_major_version(user_agent, family)
    with _connect(database_path) as connection:
        connection.execute(
            """
            INSERT INTO analytics_sessions
                (session_id, browser_family, browser_major_version, client_hash,
                 started_at, last_seen_at, duration_ms, last_tool_id, last_tool_name)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(session_id) DO UPDATE SET
                browser_family = COALESCE(
                    excluded.browser_family, analytics_sessions.browser_family
                ),
                browser_major_version = COALESCE(
                    excluded.browser_major_version, analytics_sessions.browser_major_version
                ),
                client_hash = COALESCE(
                    excluded.client_hash, analytics_sessions.client_hash
                ),
                last_seen_at = excluded.last_seen_at,
                duration_ms = MAX(analytics_sessions.duration_ms, excluded.duration_ms),
                last_tool_id = COALESCE(excluded.last_tool_id, analytics_sessions.last_tool_id),
                last_tool_name = COALESCE(
                    excluded.last_tool_name, analytics_sessions.last_tool_name
                )
            """,
            (
                session_id,
                family,
                version,
                client_hash,
                now,
                now,
                safe_duration,
                tool_id,
                tool_name,
            ),
        )
        connection.execute(
            """
            INSERT INTO analytics_events
                (session_id, event_name, tool_id, tool_name, path, duration_ms,
                 status_code, metadata_json, client_hash, occurred_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                client_hash,
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
        browser_versions = connection.execute(
            """SELECT COALESCE(browser_family, 'Unknown') AS browser_family,
                      browser_major_version, COUNT(*) AS sessions
               FROM analytics_sessions
               WHERE browser_major_version IS NOT NULL
               GROUP BY browser_family, browser_major_version
               ORDER BY sessions DESC LIMIT 20"""
        ).fetchall()
        duration_buckets = connection.execute(
            """SELECT CASE
                        WHEN duration_ms < 10000 THEN '<10s'
                        WHEN duration_ms < 60000 THEN '10s-1m'
                        WHEN duration_ms < 300000 THEN '1m-5m'
                        WHEN duration_ms < 900000 THEN '5m-15m'
                        ELSE '15m+'
                      END AS bucket,
                      COUNT(*) AS sessions
               FROM analytics_sessions
               GROUP BY bucket"""
        ).fetchall()
        bucket_order = ["<10s", "10s-1m", "1m-5m", "5m-15m", "15m+"]
        bucket_counts = {row["bucket"]: row["sessions"] for row in duration_buckets}
    return {
        "sessions": int(totals["sessions"]),
        "average_session_ms": round(float(totals["average_session_ms"]), 1),
        "tools": [dict(row) for row in tools],
        "recent_sessions": [dict(row) for row in recent],
        "browsers": [dict(row) for row in browsers],
        "browser_versions": [dict(row) for row in browser_versions],
        "session_duration_buckets": [
            {"bucket": bucket, "sessions": bucket_counts.get(bucket, 0)} for bucket in bucket_order
        ],
    }


def prune_analytics(database_path: str, *, retention_months: int = 24) -> dict[str, int]:
    """Drop analytics older than ``retention_months`` and report what went.

    The database is the only thing on the server that grows purely because
    people used the portal, so it needs a ceiling. Two years is long enough for
    the year-on-year comparisons the dashboard offers and short enough that the
    file stays small on a modest office server.
    """
    months = max(1, int(retention_months))
    cutoff = _months_ago(months)
    with _connect(database_path) as connection:
        events = connection.execute(
            "DELETE FROM analytics_events WHERE occurred_at < ?", (cutoff,)
        ).rowcount
        sessions = connection.execute(
            "DELETE FROM analytics_sessions WHERE last_seen_at < ?", (cutoff,)
        ).rowcount
    return {
        "cutoff": cutoff,
        "events_removed": max(0, events),
        "sessions_removed": max(0, sessions),
    }


def _months_ago(months: int) -> str:
    """Return the ISO timestamp ``months`` whole months before now (UTC)."""
    now = datetime.now(timezone.utc)
    year, month = now.year, now.month - months
    while month <= 0:
        month += 12
        year -= 1
    # Clamp the day so stepping back from, say, the 31st never lands on an
    # impossible date such as 31 February.
    day = min(now.day, _days_in_month(year, month))
    return now.replace(year=year, month=month, day=day).isoformat().replace("+00:00", "Z")


def _days_in_month(year: int, month: int) -> int:
    if month == 2:
        leap = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
        return 29 if leap else 28
    return 30 if month in {4, 6, 9, 11} else 31


def database_stats(database_path: str) -> dict[str, Any]:
    """Return size and row counts so the dashboard can show storage health."""
    path = Path(database_path)
    stats: dict[str, Any] = {
        "path": str(path),
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() else 0,
    }
    if not path.exists():
        return stats
    with _connect(database_path) as connection:
        for table in ("analytics_events", "analytics_sessions", "feedback_submissions"):
            row = connection.execute(f"SELECT COUNT(*) AS total FROM {table}").fetchone()
            stats[table] = int(row["total"])
        oldest = connection.execute(
            "SELECT MIN(occurred_at) AS first, MAX(occurred_at) AS last FROM analytics_events"
        ).fetchone()
        stats["first_event_at"] = oldest["first"]
        stats["last_event_at"] = oldest["last"]
    return stats
