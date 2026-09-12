from __future__ import annotations

"""The analytics engine behind the admin dashboard.

Every figure the dashboard shows is derived here, from the append-only event
log written by :mod:`ml_server.app.services.engagement`. Keeping the queries in
one module means the dashboard, the JSON API and any future report all agree on
what "a request", "a unique visitor" or "the 95th percentile" means.

Two conventions make the SQL simple. Timestamps are stored as ISO-8601 UTC
strings ending in ``Z``, so lexicographic comparison is chronological
comparison and ``substr`` slices out the year, month, day or hour bucket.
Distinct visitors are counted over ``client_hash``, the irreversible per-client
digest, so "how many different people used this in the last six months" is
answerable without the database ever holding an address.
"""

import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable

from .engagement import _connect, _months_ago

#: Selectable dashboard windows, in hours. ``None`` means "everything on record".
WINDOWS: dict[str, int | None] = {
    "1h": 1,
    "24h": 24,
    "7d": 24 * 7,
    "30d": 24 * 30,
    "90d": 24 * 90,
    "365d": 24 * 365,
    "all": None,
}

DEFAULT_WINDOW = "24h"

# Percentiles are computed in Python over the most recent samples rather than in
# SQL, which has no percentile aggregate. The cap bounds both memory and the
# time the dashboard spends waiting; it is far above a normal office day's
# traffic, so in practice the figures cover the whole window.
PERCENTILE_SAMPLE_CAP = 50_000

_PERCENTILES = (50, 75, 90, 95, 99)


def window_start(window: str) -> str | None:
    """Return the ISO timestamp ``window`` ago, or ``None`` for the all-time view."""
    hours = WINDOWS.get(window, WINDOWS[DEFAULT_WINDOW])
    if hours is None:
        return None
    moment = datetime.now(timezone.utc) - timedelta(hours=hours)
    return moment.isoformat().replace("+00:00", "Z")


def window_label(window: str) -> str:
    return {
        "1h": "last hour",
        "24h": "last 24 hours",
        "7d": "last 7 days",
        "30d": "last 30 days",
        "90d": "last 90 days",
        "365d": "last 12 months",
        "all": "all time",
    }.get(window, window)


def _percentiles(values: list[int]) -> dict[str, float]:
    """Return the nearest-rank percentiles of ``values`` (already unsorted)."""
    if not values:
        return {f"p{p}": 0.0 for p in _PERCENTILES}
    ordered = sorted(values)
    result: dict[str, float] = {}
    for percentile in _PERCENTILES:
        # Nearest-rank: the smallest value at or above the requested percentile.
        rank = max(1, min(len(ordered), -(-percentile * len(ordered) // 100)))
        result[f"p{percentile}"] = float(ordered[rank - 1])
    return result


def _duration_samples(
    connection: sqlite3.Connection, since: str | None, tool_name: str | None = None
) -> list[int]:
    clauses = ["event_name = 'request'", "duration_ms IS NOT NULL"]
    params: list[Any] = []
    if since:
        clauses.append("occurred_at >= ?")
        params.append(since)
    if tool_name is not None:
        clauses.append("COALESCE(tool_name, 'Portal') = ?")
        params.append(tool_name)
    params.append(PERCENTILE_SAMPLE_CAP)
    rows = connection.execute(
        f"SELECT duration_ms FROM analytics_events WHERE {' AND '.join(clauses)} "
        "ORDER BY occurred_at DESC LIMIT ?",
        params,
    ).fetchall()
    return [int(row["duration_ms"]) for row in rows]


def _scope(since: str | None, column: str = "occurred_at") -> tuple[str, list[Any]]:
    """Return a WHERE fragment and parameters restricting rows to the window."""
    if since is None:
        return "1 = 1", []
    return f"{column} >= ?", [since]


def overview_totals(connection: sqlite3.Connection, since: str | None) -> dict[str, Any]:
    scope, params = _scope(since)
    row = connection.execute(
        f"""SELECT COUNT(*) AS events,
                   SUM(CASE WHEN event_name = 'request' THEN 1 ELSE 0 END) AS requests,
                   SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) AS errors,
                   SUM(CASE WHEN status_code >= 500 THEN 1 ELSE 0 END) AS server_errors,
                   COUNT(DISTINCT session_id) AS sessions,
                   COUNT(DISTINCT client_hash) AS unique_clients,
                   COALESCE(AVG(CASE WHEN event_name = 'request'
                                     THEN duration_ms END), 0) AS average_ms,
                   COALESCE(MAX(CASE WHEN event_name = 'request'
                                     THEN duration_ms END), 0) AS slowest_ms,
                   COALESCE(SUM(CASE WHEN event_name = 'request'
                                     THEN duration_ms END), 0) AS total_ms
            FROM analytics_events WHERE {scope}""",
        params,
    ).fetchone()
    requests = int(row["requests"] or 0)
    errors = int(row["errors"] or 0)
    totals: dict[str, Any] = {
        "events": int(row["events"] or 0),
        "requests": requests,
        "errors": errors,
        "server_errors": int(row["server_errors"] or 0),
        "error_rate": round(errors / requests * 100, 2) if requests else 0.0,
        "sessions": int(row["sessions"] or 0),
        "unique_clients": int(row["unique_clients"] or 0),
        "average_ms": round(float(row["average_ms"] or 0), 1),
        "slowest_ms": int(row["slowest_ms"] or 0),
        "total_seconds": round(float(row["total_ms"] or 0) / 1000, 1),
    }
    totals.update(_percentiles(_duration_samples(connection, since)))
    return totals


def tool_statistics(
    connection: sqlite3.Connection, since: str | None, limit: int = 25
) -> list[dict[str, Any]]:
    """Per-service usage and timing, including percentiles for each service."""
    scope, params = _scope(since)
    rows = connection.execute(
        f"""SELECT COALESCE(tool_name, 'Portal') AS tool_name,
                   COUNT(*) AS events,
                   SUM(CASE WHEN event_name = 'request' THEN 1 ELSE 0 END) AS requests,
                   SUM(CASE WHEN event_name = 'tool_open' THEN 1 ELSE 0 END) AS opens,
                   SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) AS errors,
                   COUNT(DISTINCT session_id) AS sessions,
                   COUNT(DISTINCT client_hash) AS unique_clients,
                   COALESCE(AVG(CASE WHEN event_name = 'request'
                                     THEN duration_ms END), 0) AS average_ms,
                   COALESCE(MAX(CASE WHEN event_name = 'request'
                                     THEN duration_ms END), 0) AS slowest_ms,
                   COALESCE(SUM(CASE WHEN event_name = 'request'
                                     THEN duration_ms END), 0) AS total_ms,
                   MAX(occurred_at) AS last_used_at
            FROM analytics_events WHERE {scope}
            GROUP BY COALESCE(tool_name, 'Portal')
            ORDER BY events DESC LIMIT ?""",
        [*params, limit],
    ).fetchall()
    statistics = []
    for row in rows:
        entry = dict(row)
        requests = int(entry["requests"] or 0)
        entry["average_ms"] = round(float(entry["average_ms"] or 0), 1)
        entry["total_seconds"] = round(float(entry["total_ms"] or 0) / 1000, 1)
        entry["error_rate"] = (
            round(int(entry["errors"] or 0) / requests * 100, 2) if requests else 0.0
        )
        entry.update(_percentiles(_duration_samples(connection, since, entry["tool_name"])))
        statistics.append(entry)
    return statistics


def endpoint_statistics(
    connection: sqlite3.Connection, since: str | None, limit: int = 20
) -> dict[str, list[dict[str, Any]]]:
    """The busiest and the slowest paths, which rarely turn out to be the same."""
    scope, params = _scope(since)
    select = f"""SELECT path,
                        COUNT(*) AS requests,
                        SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) AS errors,
                        ROUND(AVG(duration_ms), 1) AS average_ms,
                        MAX(duration_ms) AS slowest_ms
                 FROM analytics_events
                 WHERE {scope} AND event_name = 'request' AND path IS NOT NULL
                 GROUP BY path"""
    busiest = connection.execute(
        f"{select} ORDER BY requests DESC LIMIT ?", [*params, limit]
    ).fetchall()
    # Single-sample outliers make a "slowest endpoint" list useless, so require a
    # handful of requests before a path can be called slow.
    slowest = connection.execute(
        f"{select} HAVING COUNT(*) >= 3 ORDER BY average_ms DESC LIMIT ?", [*params, limit]
    ).fetchall()
    return {
        "busiest": [dict(row) for row in busiest],
        "slowest": [dict(row) for row in slowest],
    }


def status_breakdown(connection: sqlite3.Connection, since: str | None) -> list[dict[str, Any]]:
    scope, params = _scope(since)
    rows = connection.execute(
        f"""SELECT status_code, COUNT(*) AS responses
            FROM analytics_events
            WHERE {scope} AND status_code IS NOT NULL
            GROUP BY status_code ORDER BY responses DESC""",
        params,
    ).fetchall()
    return [
        {"status_code": int(row["status_code"]), "responses": int(row["responses"])} for row in rows
    ]


def traffic_series(connection: sqlite3.Connection, window: str) -> dict[str, Any]:
    """Requests over time, bucketed by hour for short windows and by day for long ones."""
    hours = WINDOWS.get(window, WINDOWS[DEFAULT_WINDOW])
    by_hour = hours is not None and hours <= 24 * 3
    # 13 characters is "YYYY-MM-DDTHH"; 10 is "YYYY-MM-DD".
    slice_length = 13 if by_hour else 10
    since = window_start(window)
    scope, params = _scope(since)
    rows = connection.execute(
        f"""SELECT substr(occurred_at, 1, {slice_length}) AS bucket,
                   COUNT(*) AS events,
                   SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) AS errors,
                   COUNT(DISTINCT client_hash) AS unique_clients,
                   COUNT(DISTINCT session_id) AS sessions,
                   ROUND(AVG(duration_ms), 1) AS average_ms
            FROM analytics_events WHERE {scope}
            GROUP BY bucket ORDER BY bucket""",
        params,
    ).fetchall()
    return {
        "granularity": "hour" if by_hour else "day",
        "points": [dict(row) for row in rows],
    }


def unique_clients_by_month(
    connection: sqlite3.Connection, months: int = 6
) -> list[dict[str, Any]]:
    """Distinct visitors, sessions and requests for each of the last ``months``.

    This is the headline capacity figure: how many different machines actually
    used the platform, month by month, rather than how many times they clicked.
    """
    span = max(1, min(int(months), 120))
    since = _months_ago(span - 1)[:7] + "-01T00:00:00Z"
    rows = connection.execute(
        """SELECT substr(occurred_at, 1, 7) AS month,
                  COUNT(DISTINCT client_hash) AS unique_clients,
                  COUNT(DISTINCT session_id) AS sessions,
                  COUNT(*) AS events,
                  SUM(CASE WHEN event_name = 'request' THEN 1 ELSE 0 END) AS requests,
                  ROUND(COALESCE(SUM(duration_ms), 0) / 1000.0, 1) AS total_seconds
           FROM analytics_events WHERE occurred_at >= ?
           GROUP BY month ORDER BY month""",
        (since,),
    ).fetchall()
    counted = {row["month"]: dict(row) for row in rows}
    # Months with no traffic must still appear, or a quiet August silently
    # disappears from the chart and the trend looks continuous when it is not.
    return [
        counted.get(
            month,
            {
                "month": month,
                "unique_clients": 0,
                "sessions": 0,
                "events": 0,
                "requests": 0,
                "total_seconds": 0.0,
            },
        )
        for month in _recent_months(span)
    ]


def _recent_months(span: int) -> Iterable[str]:
    now = datetime.now(timezone.utc)
    months = []
    year, month = now.year, now.month
    for _ in range(span):
        months.append(f"{year:04d}-{month:02d}")
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    return reversed(months)


def unique_clients_by_window(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    """Distinct visitors across every selectable window, for the summary strip."""
    counts = []
    for window in ("24h", "7d", "30d", "90d", "365d", "all"):
        since = window_start(window)
        scope, params = _scope(since)
        row = connection.execute(
            f"""SELECT COUNT(DISTINCT client_hash) AS unique_clients,
                       COUNT(DISTINCT session_id) AS sessions
                FROM analytics_events WHERE {scope}""",
            params,
        ).fetchone()
        counts.append(
            {
                "window": window,
                "label": window_label(window),
                "unique_clients": int(row["unique_clients"] or 0),
                "sessions": int(row["sessions"] or 0),
            }
        )
    return counts


def hour_of_day_profile(connection: sqlite3.Connection, since: str | None) -> list[dict[str, Any]]:
    """When the platform is actually busy, in UTC hours."""
    scope, params = _scope(since)
    rows = connection.execute(
        f"""SELECT substr(occurred_at, 12, 2) AS hour, COUNT(*) AS events
            FROM analytics_events WHERE {scope} GROUP BY hour""",
        params,
    ).fetchall()
    counted = {row["hour"]: int(row["events"]) for row in rows}
    return [{"hour": f"{hour:02d}", "events": counted.get(f"{hour:02d}", 0)} for hour in range(24)]


def event_breakdown(connection: sqlite3.Connection, since: str | None) -> list[dict[str, Any]]:
    scope, params = _scope(since)
    rows = connection.execute(
        f"""SELECT event_name, COUNT(*) AS events
            FROM analytics_events WHERE {scope}
            GROUP BY event_name ORDER BY events DESC""",
        params,
    ).fetchall()
    return [dict(row) for row in rows]


def browser_breakdown(connection: sqlite3.Connection) -> dict[str, list[dict[str, Any]]]:
    families = connection.execute(
        """SELECT COALESCE(browser_family, 'Unknown') AS browser_family,
                  COUNT(*) AS sessions
           FROM analytics_sessions GROUP BY 1 ORDER BY sessions DESC"""
    ).fetchall()
    versions = connection.execute(
        """SELECT COALESCE(browser_family, 'Unknown') AS browser_family,
                  browser_major_version, COUNT(*) AS sessions
           FROM analytics_sessions WHERE browser_major_version IS NOT NULL
           GROUP BY 1, 2 ORDER BY sessions DESC LIMIT 25"""
    ).fetchall()
    return {
        "browsers": [dict(row) for row in families],
        "browser_versions": [dict(row) for row in versions],
    }


def session_statistics(connection: sqlite3.Connection) -> dict[str, Any]:
    totals = connection.execute(
        """SELECT COUNT(*) AS sessions,
                  COALESCE(AVG(duration_ms), 0) AS average_ms,
                  COALESCE(MAX(duration_ms), 0) AS longest_ms,
                  COUNT(DISTINCT client_hash) AS unique_clients,
                  MIN(started_at) AS first_session_at
           FROM analytics_sessions"""
    ).fetchone()
    buckets = connection.execute(
        """SELECT CASE
                    WHEN duration_ms < 10000 THEN '<10s'
                    WHEN duration_ms < 60000 THEN '10s-1m'
                    WHEN duration_ms < 300000 THEN '1m-5m'
                    WHEN duration_ms < 900000 THEN '5m-15m'
                    ELSE '15m+'
                  END AS bucket, COUNT(*) AS sessions
           FROM analytics_sessions GROUP BY bucket"""
    ).fetchall()
    order = ["<10s", "10s-1m", "1m-5m", "5m-15m", "15m+"]
    counted = {row["bucket"]: int(row["sessions"]) for row in buckets}
    recent = connection.execute(
        """SELECT session_id, browser_family, browser_major_version, started_at,
                  last_seen_at, duration_ms, last_tool_name
           FROM analytics_sessions ORDER BY last_seen_at DESC LIMIT 25"""
    ).fetchall()
    return {
        "sessions": int(totals["sessions"] or 0),
        "unique_clients": int(totals["unique_clients"] or 0),
        "average_session_ms": round(float(totals["average_ms"] or 0), 1),
        "longest_session_ms": int(totals["longest_ms"] or 0),
        "first_session_at": totals["first_session_at"],
        "duration_buckets": [
            {"bucket": bucket, "sessions": counted.get(bucket, 0)} for bucket in order
        ],
        "recent_sessions": [dict(row) for row in recent],
    }


def analytics_report(
    database_path: str, *, window: str = DEFAULT_WINDOW, months: int = 6
) -> dict[str, Any]:
    """Assemble the complete dashboard payload for one window."""
    selected = window if window in WINDOWS else DEFAULT_WINDOW
    since = window_start(selected)
    with _connect(database_path) as connection:
        report: dict[str, Any] = {
            "window": selected,
            "window_label": window_label(selected),
            "since": since,
            "months": max(1, min(int(months), 120)),
            "totals": overview_totals(connection, since),
            "tools": tool_statistics(connection, since),
            "endpoints": endpoint_statistics(connection, since),
            "status_codes": status_breakdown(connection, since),
            "traffic": traffic_series(connection, selected),
            "unique_clients_by_month": unique_clients_by_month(connection, months),
            "unique_clients_by_window": unique_clients_by_window(connection),
            "hour_profile": hour_of_day_profile(connection, since),
            "events": event_breakdown(connection, since),
            "sessions": session_statistics(connection),
        }
        report.update(browser_breakdown(connection))
    return report


def analytics_summary(database_path: str) -> dict[str, Any]:
    """Backwards-compatible compact summary used by the legacy dashboard view."""
    report = analytics_report(database_path, window="all")
    sessions = report["sessions"]
    return {
        "sessions": sessions["sessions"],
        "average_session_ms": sessions["average_session_ms"],
        "tools": [
            {
                "tool_name": tool["tool_name"],
                "uses": tool["events"],
                "average_action_ms": tool["average_ms"],
            }
            for tool in report["tools"]
        ],
        "recent_sessions": sessions["recent_sessions"],
        "browsers": report["browsers"],
        "browser_versions": report["browser_versions"],
        "session_duration_buckets": sessions["duration_buckets"],
    }
