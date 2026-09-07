from __future__ import annotations

"""Host, process and dependency diagnostics for the admin dashboard.

Everything here answers a question an operator asks when something looks wrong:
how long has this been up, is the disk filling, is Redis reachable, which
config file did it actually load. ``psutil`` gives richer numbers when it is
installed, but every function degrades to a useful answer without it so the
dashboard never breaks on a minimal install.
"""

import os
import platform
import shutil
import socket
import sys
import time
from typing import Any

try:  # pragma: no cover - exercised implicitly by whichever branch runs
    import psutil
except ImportError:  # pragma: no cover - optional dependency
    psutil = None  # type: ignore[assignment]


def format_duration(seconds: float) -> str:
    """Render a duration the way an operator reads one: ``3d 04h 12m``."""
    total = int(max(0, seconds))
    days, remainder = divmod(total, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, secs = divmod(remainder, 60)
    if days:
        return f"{days}d {hours:02d}h {minutes:02d}m"
    if hours:
        return f"{hours}h {minutes:02d}m {secs:02d}s"
    return f"{minutes}m {secs:02d}s"


def format_bytes(count: float) -> str:
    size = float(max(0, count))
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} B"
        size /= 1024
    return f"{size:.1f} TB"


def uptime_report(start_time: float) -> dict[str, Any]:
    """Portal uptime, plus host uptime when the platform can report it."""
    now = time.time()
    process_seconds = max(0.0, now - start_time)
    report: dict[str, Any] = {
        "started_at": start_time,
        "process_seconds": round(process_seconds, 1),
        "process_human": format_duration(process_seconds),
        "host_seconds": None,
        "host_human": "unavailable",
    }
    if psutil is not None:
        try:
            host_seconds = now - psutil.boot_time()
            report["host_seconds"] = round(host_seconds, 1)
            report["host_human"] = format_duration(host_seconds)
        except Exception:  # pragma: no cover - platform dependent
            pass
    return report


def host_report() -> dict[str, Any]:
    report: dict[str, Any] = {
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "pid": os.getpid(),
        "cpu_count": os.cpu_count(),
        "load_average": None,
        "cpu_percent": None,
        "memory": None,
        "process_memory_bytes": None,
        "threads": None,
    }
    if hasattr(os, "getloadavg"):
        try:
            report["load_average"] = [round(value, 2) for value in os.getloadavg()]
        except OSError:  # pragma: no cover - platform dependent
            pass
    if psutil is not None:
        try:
            # A zero interval reports the average since the previous call rather
            # than blocking the dashboard request for a sampling window.
            report["cpu_percent"] = psutil.cpu_percent(interval=0.0)
            memory = psutil.virtual_memory()
            report["memory"] = {
                "total_bytes": memory.total,
                "used_bytes": memory.total - memory.available,
                "available_bytes": memory.available,
                "percent": memory.percent,
                "total_human": format_bytes(memory.total),
                "used_human": format_bytes(memory.total - memory.available),
            }
            process = psutil.Process()
            report["process_memory_bytes"] = process.memory_info().rss
            report["process_memory_human"] = format_bytes(process.memory_info().rss)
            report["threads"] = process.num_threads()
        except Exception:  # pragma: no cover - platform dependent
            pass
    return report


def disk_report(paths: list[str] | None = None) -> list[dict[str, Any]]:
    """Usage for the volumes that matter: the install root, data and logs."""
    candidates = paths or [os.getcwd()]
    seen: set[str] = set()
    reports = []
    for candidate in candidates:
        path = os.path.abspath(candidate)
        while path and not os.path.isdir(path):
            parent = os.path.dirname(path)
            if parent == path:
                break
            path = parent
        if not os.path.isdir(path) or path in seen:
            continue
        seen.add(path)
        try:
            usage = shutil.disk_usage(path)
        except OSError:  # pragma: no cover - unreadable mount
            continue
        reports.append(
            {
                "path": path,
                "total_bytes": usage.total,
                "used_bytes": usage.used,
                "free_bytes": usage.free,
                "percent": round(usage.used / usage.total * 100, 1) if usage.total else 0.0,
                "total_human": format_bytes(usage.total),
                "free_human": format_bytes(usage.free),
            }
        )
    return reports


def dependency_report(celery_app: Any = None) -> list[dict[str, Any]]:
    """Reachability of the optional back-end services, each checked cheaply."""
    checks: list[dict[str, Any]] = []
    checks.append(_redis_check())
    checks.append(_celery_check(celery_app))
    return checks


def _redis_check() -> dict[str, Any]:
    started = time.time()
    try:
        import redis  # imported lazily so a Redis-less install still loads

        from ...config import Config

        url = Config().celery_settings.get("broker_url", "redis://localhost:6379/0")
        client = redis.Redis.from_url(url, socket_connect_timeout=1, socket_timeout=1)
        client.ping()
        return _check("Redis", True, url, started)
    except Exception as error:  # noqa: BLE001 - any failure means "not reachable"
        return _check("Redis", False, str(error)[:200], started)


def _celery_check(celery_app: Any) -> dict[str, Any]:
    started = time.time()
    if celery_app is None:
        return _check("Celery workers", False, "not configured", started)
    try:
        workers = celery_app.control.ping(timeout=1.0)
        count = len(workers or [])
        return _check("Celery workers", bool(count), f"{count} responding", started)
    except Exception as error:  # noqa: BLE001
        return _check("Celery workers", False, str(error)[:200], started)


def _check(name: str, healthy: bool, detail: str, started: float) -> dict[str, Any]:
    return {
        "name": name,
        "healthy": healthy,
        "detail": detail,
        "checked_in_ms": round((time.time() - started) * 1000, 1),
    }


def application_report(app: Any) -> dict[str, Any]:
    """What this process is actually running: version, config, routes, flags."""
    from ... import __version__
    from ...config import Config

    config = Config()
    routes = sorted(
        {rule.rule for rule in app.url_map.iter_rules() if not rule.rule.startswith("/static")}
    )
    return {
        "version": __version__,
        "config_path": str(getattr(config, "config_path", "unknown")),
        "debug": bool(app.debug),
        "testing": bool(app.config.get("TESTING")),
        "analytics_enabled": bool(app.config.get("ANALYTICS_ENABLED")),
        "email_enabled": bool((app.config.get("EMAIL_SETTINGS") or {}).get("enabled")),
        "database_path": str(app.config.get("ENGAGEMENT_DATABASE", "")),
        "log_directory": config.logging_settings.get("log_dir", "logs"),
        "bind": f"{config.host}:{config.port}",
        "blueprints": sorted(app.blueprints),
        "route_count": len(routes),
        "routes": routes,
        "working_directory": os.getcwd(),
    }
