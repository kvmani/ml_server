from __future__ import annotations

"""Password authentication for the admin dashboard.

The dashboard shows live client addresses, logs and diagnostics, so it needs a
real login rather than a URL anyone could paste into chat. Three properties
matter for the office deployment:

* **The secret never lives in the repository.** It is read from the environment
  (or an operator-written config file), so a clean checkout, a CI run and a
  release build all work without it, and the built artifact contains no
  credential. See ``docs/ADMIN_DASHBOARD.md``.
* **A hash is preferred to a password.** ``ML_SERVER_ADMIN_PASSWORD_HASH``
  holds a PBKDF2 digest, so the server never stores the password itself.
* **An unconfigured server is closed, not open.** With no secret set, every
  login fails with an explanatory message instead of letting anyone in.
"""

import hmac
import logging
import os
import secrets
import threading
import time
from functools import wraps
from typing import Any, Callable

from flask import current_app, redirect, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

logger = logging.getLogger(__name__)

#: How long a login stays valid, and how long it may sit idle, in seconds.
SESSION_MAX_AGE = 12 * 60 * 60
SESSION_IDLE_TIMEOUT = 60 * 60

#: Failed logins tolerated from one address before it is locked out, and for how long.
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_SECONDS = 15 * 60

_SESSION_KEY = "ml_admin_authenticated_at"
_SESSION_SEEN_KEY = "ml_admin_last_seen_at"
_CSRF_KEY = "ml_admin_csrf"

# Placeholders shipped in the sample configuration. Treating them as "unset"
# stops a deployment that forgot to set a real secret from being protected by a
# password that is public knowledge.
_PLACEHOLDERS = {"", "changeme", "__set_admin_token__", "__set_secret_key__", "admin", "password"}


class _AttemptLimiter:
    """Track failed logins per client address, in memory only."""

    def __init__(self) -> None:
        self._failures: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def _recent(self, address: str, now: float) -> list[float]:
        attempts = [at for at in self._failures.get(address, []) if now - at < LOCKOUT_SECONDS]
        if attempts:
            self._failures[address] = attempts
        else:
            self._failures.pop(address, None)
        return attempts

    def locked_for(self, address: str, now: float | None = None) -> int:
        """Return the seconds remaining in a lockout, or 0 when not locked."""
        moment = time.time() if now is None else now
        with self._lock:
            attempts = self._recent(address, moment)
            if len(attempts) < MAX_FAILED_ATTEMPTS:
                return 0
            return max(0, int(LOCKOUT_SECONDS - (moment - min(attempts))))

    def record_failure(self, address: str, now: float | None = None) -> int:
        moment = time.time() if now is None else now
        with self._lock:
            attempts = self._recent(address, moment)
            attempts.append(moment)
            self._failures[address] = attempts
            return max(0, MAX_FAILED_ATTEMPTS - len(attempts))

    def clear(self, address: str) -> None:
        with self._lock:
            self._failures.pop(address, None)

    def reset(self) -> None:
        with self._lock:
            self._failures.clear()


attempt_limiter = _AttemptLimiter()


def _configured(value: Any) -> str:
    """Return ``value`` as a usable secret, or "" when it is a placeholder."""
    candidate = str(value or "").strip()
    return "" if candidate.lower() in _PLACEHOLDERS else candidate


def admin_password_hash() -> str:
    """Return the configured PBKDF2 hash of the admin password, if any."""
    return _configured(
        os.getenv("ML_SERVER_ADMIN_PASSWORD_HASH")
        or current_app.config.get("ADMIN_PASSWORD_HASH")
    )


def admin_password() -> str:
    """Return the configured plaintext admin password, if any.

    The legacy ``security.admin_token`` doubles as the password so existing
    deployments keep working after an upgrade without an operator having to
    change anything on the day of the release.
    """
    return _configured(
        os.getenv("ML_SERVER_ADMIN_PASSWORD")
        or current_app.config.get("ADMIN_PASSWORD")
        or current_app.config.get("ADMIN_TOKEN")
    )


def admin_access_configured() -> bool:
    """Whether this server has any admin credential at all."""
    return bool(admin_password_hash() or admin_password())


def verify_password(candidate: str) -> bool:
    """Check ``candidate`` against the configured hash or password."""
    if not candidate:
        return False
    hashed = admin_password_hash()
    if hashed:
        try:
            return check_password_hash(hashed, candidate)
        except ValueError:
            logger.error("ADMIN_PASSWORD_HASH is not a valid password hash; refusing login")
            return False
    password = admin_password()
    if not password:
        return False
    return hmac.compare_digest(password, candidate)


def hash_password(password: str) -> str:
    """Return a PBKDF2 hash suitable for ``ML_SERVER_ADMIN_PASSWORD_HASH``."""
    return generate_password_hash(password, method="pbkdf2:sha256:600000")


def csrf_token() -> str:
    """Return this browser session's login-form token, creating it if needed."""
    token = session.get(_CSRF_KEY)
    if not token:
        token = secrets.token_urlsafe(32)
        session[_CSRF_KEY] = token
    return token


def csrf_token_valid(candidate: str | None) -> bool:
    expected = session.get(_CSRF_KEY)
    return bool(expected and candidate and hmac.compare_digest(str(expected), str(candidate)))


def start_session() -> None:
    now = time.time()
    session[_SESSION_KEY] = now
    session[_SESSION_SEEN_KEY] = now
    session.permanent = False


def end_session() -> None:
    for key in (_SESSION_KEY, _SESSION_SEEN_KEY, _CSRF_KEY):
        session.pop(key, None)


def _legacy_token_accepted() -> bool:
    """Honour the pre-1.2 ``?token=`` links that scripts and bookmarks still use."""
    token = request.args.get("token") or request.headers.get("X-Admin-Token")
    if not token:
        return False
    password = admin_password()
    return bool(password and hmac.compare_digest(password, token))


def session_active() -> bool:
    """Whether the caller holds a live, non-expired admin session."""
    started = session.get(_SESSION_KEY)
    last_seen = session.get(_SESSION_SEEN_KEY, started)
    if not started:
        return False
    now = time.time()
    if now - float(started) > SESSION_MAX_AGE or now - float(last_seen) > SESSION_IDLE_TIMEOUT:
        end_session()
        return False
    session[_SESSION_SEEN_KEY] = now
    return True


def is_authenticated() -> bool:
    return session_active() or _legacy_token_accepted()


def login_required(view: Callable) -> Callable:
    """Send anonymous callers to the login page, or refuse a JSON request."""

    @wraps(view)
    def wrapper(*args: Any, **kwargs: Any):
        if is_authenticated():
            return view(*args, **kwargs)
        if request.path.startswith("/admin/api/") or request.accept_mimetypes.best == (
            "application/json"
        ):
            return {"status": "error", "message": "Authentication required"}, 401
        return redirect(url_for("admin.login", next=request.full_path))

    return wrapper
