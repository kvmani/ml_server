"""Utility helpers for route modules."""

from functools import wraps

import requests
from flask import jsonify, request


def allowed_file(filename: str, allowed_extensions: set[str]) -> bool:
    """Return True if ``filename`` has an allowed extension."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions


def check_service_health(health_url: str, timeout: int = 3) -> bool:
    """Return ``True`` if ``health_url`` responds with HTTP 200 within ``timeout`` seconds."""
    try:
        response = requests.get(health_url, timeout=timeout)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


def require_service(
    health_url: str,
    start_cb=None,
    service_name: str = "Service",
    methods: tuple[str, ...] | None = None,
) -> callable:
    """Decorator ensuring an external service is available before executing a view."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if methods is None or request.method in methods:
                if not check_service_health(health_url):
                    if start_cb and start_cb():
                        msg = (
                            f"{service_name} was not running. It has been started. "
                            "Please try your request again."
                        )
                    else:
                        msg = f"{service_name} is not running."
                    return jsonify({"success": False, "error": msg}), 503
            return func(*args, **kwargs)

        return wrapper

    return decorator


def ensure_service_available(
    health_url: str,
    start_cb=None,
    service_name: str = "Service",
) -> tuple | None:
    """Return an error response if the given service is unavailable."""
    if not check_service_health(health_url):
        if start_cb and start_cb():
            msg = (
                f"{service_name} was not running. It has been started. "
                "Please try your request again."
            )
        else:
            msg = f"{service_name} is not running."
        return jsonify({"success": False, "error": msg}), 503
    return None
