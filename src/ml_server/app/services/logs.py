from __future__ import annotations

"""Read and filter the application log for the admin dashboard.

The log is a plain file written by :mod:`logging` in the configured format
``%(asctime)s [%(levelname)s] %(message)s``. Parsing it back into records lets
the dashboard answer the question operators actually ask -- "show me only the
warnings and errors" -- instead of making them read a wall of INFO lines.

Two details make the result trustworthy. Tracebacks span many lines, so any
line that does not start a new record is attached to the record above it rather
than dropped or mistaken for an unlevelled entry. And only the tail of the file
is read, so a log that has grown to hundreds of megabytes still renders
instantly and cannot exhaust memory.
"""

import os
import re
from pathlib import Path
from typing import Any

#: Log levels in severity order; the dashboard filters at or above a chosen level.
LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
_LEVEL_RANK = {level: index for index, level in enumerate(LEVELS)}

# The default record layout, e.g.
# "2026-09-07 10:15:02,123 [WARNING] Something needs attention".
_RECORD = re.compile(
    r"^(?P<timestamp>\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?)\s*"
    r"[\[\-\s]*(?P<level>DEBUG|INFO|WARNING|WARN|ERROR|CRITICAL|FATAL)\]?\s*"
    r"(?P<message>.*)$"
)

_ALIASES = {"WARN": "WARNING", "FATAL": "CRITICAL"}

#: Bytes read from the end of the file. Comfortably more than the deepest view.
TAIL_BYTES = 2 * 1024 * 1024


def log_file_path(log_dir: str, log_file: str) -> Path:
    return Path(log_dir) / log_file


def available_log_files(log_dir: str, log_file: str) -> list[dict[str, Any]]:
    """List the active log and its rotated siblings, newest first."""
    directory = Path(log_dir)
    if not directory.is_dir():
        return []
    files = []
    for candidate in sorted(directory.glob(f"{log_file}*")):
        try:
            stat = candidate.stat()
        except OSError:  # pragma: no cover - file vanished mid-listing
            continue
        files.append(
            {
                "name": candidate.name,
                "size_bytes": stat.st_size,
                "modified_at": stat.st_mtime,
                "active": candidate.name == log_file,
            }
        )
    files.sort(key=lambda item: (not item["active"], -item["modified_at"]))
    return files


def _read_tail(path: Path, tail_bytes: int = TAIL_BYTES) -> str:
    with path.open("rb") as handle:
        handle.seek(0, os.SEEK_END)
        size = handle.tell()
        handle.seek(max(0, size - tail_bytes))
        chunk = handle.read()
    text = chunk.decode("utf-8", errors="replace")
    if size > tail_bytes:
        # The first line is almost certainly cut in half; drop it rather than
        # present a fragment as if it were a record.
        text = text.split("\n", 1)[-1]
    return text


def parse_records(text: str) -> list[dict[str, Any]]:
    """Turn raw log text into records, folding continuation lines upward."""
    records: list[dict[str, Any]] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        match = _RECORD.match(line)
        if match:
            level = match.group("level").upper()
            records.append(
                {
                    "timestamp": match.group("timestamp"),
                    "level": _ALIASES.get(level, level),
                    "message": match.group("message"),
                    "detail": "",
                }
            )
        elif records:
            records[-1]["detail"] = (records[-1]["detail"] + "\n" + line).strip()
        else:
            # Output that precedes the first parsable record (a startup banner,
            # or a traceback whose header scrolled out of the tail window).
            records.append(
                {"timestamp": "", "level": "INFO", "message": line, "detail": ""}
            )
    return records


def read_log(
    log_dir: str,
    log_file: str,
    *,
    level: str = "ALL",
    search: str = "",
    limit: int = 300,
    tail_bytes: int = TAIL_BYTES,
) -> dict[str, Any]:
    """Return the newest matching log records plus a count of every level.

    ``level`` filters at or above the named severity, so choosing ``WARNING``
    shows warnings, errors and criticals together -- which is what an operator
    triaging an incident means by "show me the problems".
    """
    path = log_file_path(log_dir, log_file)
    result: dict[str, Any] = {
        "path": str(path),
        "exists": path.is_file(),
        "level": level.upper(),
        "search": search,
        "records": [],
        "counts": {name: 0 for name in LEVELS},
        "total_records": 0,
        "matched_records": 0,
        "size_bytes": 0,
        "truncated": False,
        "files": available_log_files(log_dir, log_file),
    }
    if not path.is_file():
        return result

    result["size_bytes"] = path.stat().st_size
    result["truncated"] = result["size_bytes"] > tail_bytes
    try:
        records = parse_records(_read_tail(path, tail_bytes))
    except OSError:  # pragma: no cover - unreadable file
        return result

    for record in records:
        if record["level"] in result["counts"]:
            result["counts"][record["level"]] += 1
    result["total_records"] = len(records)

    minimum = _LEVEL_RANK.get(level.upper())
    needle = search.strip().lower()
    matched = [
        record
        for record in records
        if (minimum is None or _LEVEL_RANK.get(record["level"], 0) >= minimum)
        and (
            not needle
            or needle in record["message"].lower()
            or needle in record["detail"].lower()
        )
    ]
    result["matched_records"] = len(matched)
    # Newest first is what the dashboard shows, and the tail is what matters.
    result["records"] = list(reversed(matched[-max(1, int(limit)) :]))
    return result
