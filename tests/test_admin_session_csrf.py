"""The admin login, exercised the way a browser does it.

These tests exist because of a production failure: after an upgrade the portal
served every page happily, ``/health`` was green, and every attempt to sign in
to ``/admin/`` came back with the login form and "This form expired". The
existing admin tests could not see it, because they read the CSRF token out of
the session with ``session_transaction()`` instead of letting the token and the
session cookie travel over the wire the way a browser makes them travel.

Everything here therefore goes through the real GET -> parse HTML -> POST
lifecycle with the test client's cookie jar, and asserts on the ``Set-Cookie``
header rather than on Flask's config.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

import pytest

from ml_server.app import server as ml_server_app
from ml_server.config import Config

PASSWORD = "office-admin-secret"

BASE_CONFIG = {
    "debug": False,
    "host": "127.0.0.1",
    "port": 5000,
    "feedback": {"database_path": "data/engagement.sqlite3"},
    "analytics": {"enabled": False},
    "logging": {"log_dir": "tmp/test_logs", "log_file": "app.log"},
    "security": {
        "csrf_enabled": True,
        "ssl_enabled": False,
        "admin_token": PASSWORD,
    },
}

_TOKEN_RE = re.compile(r'name="csrf_token"\s+value="([^"]+)"')


def write_config(tmp_path: Path, **overrides) -> Path:
    """Write a portal config file, merging ``security`` overrides sensibly."""
    document = json.loads(json.dumps(BASE_CONFIG))
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(document.get(key), dict):
            document[key].update(value)
        else:
            document[key] = value
    path = tmp_path / "config.intranet.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    return path


def build_app(config_path: Path, engagement_db: Path):
    """Build a fresh application from ``config_path``, as a worker process would."""
    Config._instance = None
    os.environ["ML_SERVER_CONFIG"] = str(config_path)
    try:
        app = ml_server_app.create_app(startup=False)
    finally:
        Config._instance = None
    app.config["TESTING"] = True
    app.config["ENGAGEMENT_DATABASE"] = str(engagement_db)
    app.config["ANALYTICS_ENABLED"] = False
    from ml_server.app.services.engagement import initialize_database

    initialize_database(app.config["ENGAGEMENT_DATABASE"])
    return app


@pytest.fixture(autouse=True)
def clean_environment(monkeypatch):
    """No developer .env or exported secret may decide these outcomes.

    ``Config`` loads ``.env`` from the working directory on every construction,
    so clearing the variables is not enough: the loader would put a developer's
    password straight back. The loader itself is stubbed out instead, which is
    what makes these assertions mean the same thing on a laptop and in CI.
    """
    import ml_server.config as config_module

    monkeypatch.setattr(config_module, "load_dotenv", lambda *args, **kwargs: False)
    for name in (
        "ML_SERVER_ADMIN_PASSWORD",
        "ML_SERVER_ADMIN_PASSWORD_HASH",
        "ML_SERVER_CONFIG",
        "ML_SERVER_SECRET_KEY",
        "APP_SECRET_KEY",
        "APP_SECURITY__SSL_ENABLED",
    ):
        monkeypatch.delenv(name, raising=False)
    from ml_server.app.admin import auth

    auth.attempt_limiter.reset()
    yield
    Config._instance = None


def form_token(html: str) -> str:
    """Pull the login form's CSRF token out of the rendered page, as a browser would."""
    match = _TOKEN_RE.search(html)
    assert match, "the login page did not render a CSRF token"
    return match.group(1)


def browser_login(client, password: str = PASSWORD, base_url: str = "http://localhost"):
    """GET the form, then POST it back exactly as a browser would."""
    page = client.get("/admin/login", base_url=base_url)
    assert page.status_code == 200
    token = form_token(page.get_data(as_text=True))
    return client.post(
        "/admin/login",
        data={"password": password, "csrf_token": token},
        base_url=base_url,
        follow_redirects=False,
    )


def session_cookie_header(response) -> str:
    """The Set-Cookie line for Flask's session cookie, or "" when absent."""
    for header in response.headers.getlist("Set-Cookie"):
        if header.startswith("session="):
            return header
    return ""


# ---------------------------------------------------------------------------
# The production regression: HTTP intranet mode
# ---------------------------------------------------------------------------
def test_http_login_succeeds_end_to_end(tmp_path):
    """ssl_enabled=false: a plain-HTTP browser login must work, start to finish."""
    app = build_app(
        write_config(
            tmp_path, secret_key="a-stable-office-secret", security={"ssl_enabled": False}
        ),
        tmp_path / "engagement.sqlite3",
    )
    with app.test_client() as client:
        response = browser_login(client)

    assert response.status_code == 302, response.get_data(as_text=True)[:400]
    assert "/admin/" in response.headers["Location"]


def test_http_session_cookie_is_not_secure(tmp_path):
    """A Secure cookie is never returned over HTTP, so it must not be set here."""
    app = build_app(
        write_config(
            tmp_path, secret_key="a-stable-office-secret", security={"ssl_enabled": False}
        ),
        tmp_path / "engagement.sqlite3",
    )
    with app.test_client() as client:
        page = client.get("/admin/login", base_url="http://localhost")

    header = session_cookie_header(page)
    assert header, "the login page set no session cookie, so the CSRF token has nowhere to live"
    assert "Secure" not in header
    assert "HttpOnly" in header
    assert "SameSite=Lax" in header


def test_http_mode_does_not_force_https(tmp_path):
    """No redirect to https:// and no HSTS while the site is served over HTTP."""
    app = build_app(
        write_config(
            tmp_path, secret_key="a-stable-office-secret", security={"ssl_enabled": False}
        ),
        tmp_path / "engagement.sqlite3",
    )
    with app.test_client() as client:
        page = client.get("/admin/login", base_url="http://localhost")

    assert page.status_code == 200
    assert "Strict-Transport-Security" not in page.headers


def test_csrf_is_still_enforced_over_http(tmp_path):
    """The fix must not be "turn CSRF off": a POST without the token still fails."""
    app = build_app(
        write_config(tmp_path, secret_key="a-stable-office-secret"),
        tmp_path / "engagement.sqlite3",
    )
    with app.test_client() as client:
        client.get("/admin/login")
        response = client.post("/admin/login", data={"password": PASSWORD}, follow_redirects=False)

    assert response.status_code == 200
    assert "expired" in response.get_data(as_text=True).lower()


def test_a_stolen_token_from_another_session_is_refused(tmp_path):
    """The token is bound to the session cookie, not merely to the form."""
    app = build_app(
        write_config(tmp_path, secret_key="a-stable-office-secret"),
        tmp_path / "engagement.sqlite3",
    )
    with app.test_client() as victim, app.test_client() as attacker:
        stolen = form_token(victim.get("/admin/login").get_data(as_text=True))
        response = attacker.post(
            "/admin/login",
            data={"password": PASSWORD, "csrf_token": stolen},
            follow_redirects=False,
        )

    assert response.status_code == 200
    assert "expired" in response.get_data(as_text=True).lower()


# ---------------------------------------------------------------------------
# The root cause: a secret key that differs between workers
# ---------------------------------------------------------------------------
def test_secret_key_is_stable_across_worker_processes(tmp_path):
    """Two workers built from one config must sign sessions with the same key.

    Production runs ``gunicorn --workers 2``. With a per-process random key the
    GET that issues the CSRF token and the POST that returns it land on
    different workers roughly half the time, the second worker cannot verify the
    session cookie the first one signed, and the login reports an expired form.
    """
    config_path = write_config(tmp_path, secret_key="")

    worker_one = build_app(config_path, tmp_path / "engagement.sqlite3")
    worker_two = build_app(config_path, tmp_path / "engagement.sqlite3")

    assert worker_one.secret_key, "a server with no configured secret_key must still have one"
    assert worker_one.secret_key == worker_two.secret_key


def test_login_survives_the_request_landing_on_another_worker(tmp_path):
    """The GET on one worker, the POST on another -- the v1.4-v1.6 failure."""
    config_path = write_config(tmp_path, secret_key="")
    worker_one = build_app(config_path, tmp_path / "engagement.sqlite3")
    worker_two = build_app(config_path, tmp_path / "engagement.sqlite3")

    with worker_one.test_client() as client_one:
        page = client_one.get("/admin/login")
        token = form_token(page.get_data(as_text=True))
        cookie = session_cookie_header(page).split(";", 1)[0]

    with worker_two.test_client() as client_two:
        client_two.set_cookie("session", cookie.split("=", 1)[1], domain="localhost")
        response = client_two.post(
            "/admin/login",
            data={"password": PASSWORD, "csrf_token": token},
            follow_redirects=False,
        )

    assert response.status_code == 302, response.get_data(as_text=True)[:400]


def test_a_configured_secret_key_is_used_verbatim(tmp_path):
    """An operator-set key must win over any generated one."""
    app = build_app(
        write_config(tmp_path, secret_key="the-operators-own-key"),
        tmp_path / "engagement.sqlite3",
    )
    assert app.secret_key == "the-operators-own-key"


def test_placeholder_secret_key_does_not_become_the_signing_key(tmp_path):
    """__SET_SECRET_KEY__ ships in the template; it must never sign anything."""
    app = build_app(
        write_config(tmp_path, secret_key="__SET_SECRET_KEY__"),
        tmp_path / "engagement.sqlite3",
    )
    assert "__SET_" not in str(app.secret_key)
    assert app.secret_key


# ---------------------------------------------------------------------------
# HTTPS mode, tested separately
# ---------------------------------------------------------------------------
def test_https_mode_marks_the_session_cookie_secure(tmp_path):
    app = build_app(
        write_config(tmp_path, secret_key="a-stable-office-secret", security={"ssl_enabled": True}),
        tmp_path / "engagement.sqlite3",
    )
    with app.test_client() as client:
        page = client.get("/admin/login", base_url="https://localhost")

    assert page.status_code == 200
    assert "Secure" in session_cookie_header(page)


def test_https_login_succeeds_end_to_end(tmp_path):
    app = build_app(
        write_config(tmp_path, secret_key="a-stable-office-secret", security={"ssl_enabled": True}),
        tmp_path / "engagement.sqlite3",
    )
    with app.test_client() as client:
        response = browser_login(client, base_url="https://localhost")

    assert response.status_code == 302, response.get_data(as_text=True)[:400]


def test_https_mode_redirects_plain_http_and_sends_hsts(tmp_path):
    """With ssl_enabled=true the site is an HTTPS site, and says so."""
    app = build_app(
        write_config(tmp_path, secret_key="a-stable-office-secret", security={"ssl_enabled": True}),
        tmp_path / "engagement.sqlite3",
    )
    with app.test_client() as client:
        plain = client.get("/admin/login", base_url="http://localhost")
        secure = client.get("/admin/login", base_url="https://localhost")

    assert plain.status_code in (301, 302, 308)
    assert plain.headers["Location"].startswith("https://")
    assert "Strict-Transport-Security" in secure.headers


# ---------------------------------------------------------------------------
# Logout, and the admin entry point
# ---------------------------------------------------------------------------
def test_logout_ends_the_session(tmp_path):
    app = build_app(
        write_config(tmp_path, secret_key="a-stable-office-secret"),
        tmp_path / "engagement.sqlite3",
    )
    with app.test_client() as client:
        assert browser_login(client).status_code == 302
        assert client.get("/admin/", follow_redirects=False).status_code == 200

        client.post("/admin/logout", follow_redirects=False)

        after = client.get("/admin/", follow_redirects=False)
    assert after.status_code == 302
    assert "/admin/login" in after.headers["Location"]


def test_changing_the_admin_token_changes_the_password(tmp_path):
    """Editing the shared config and restarting is all a token change needs."""
    config_path = write_config(
        tmp_path, secret_key="a-stable-office-secret", security={"admin_token": "first-secret"}
    )
    app = build_app(config_path, tmp_path / "engagement.sqlite3")
    with app.test_client() as client:
        assert browser_login(client, "first-secret").status_code == 302

    write_config(
        tmp_path, secret_key="a-stable-office-secret", security={"admin_token": "second-secret"}
    )
    restarted = build_app(config_path, tmp_path / "engagement.sqlite3")
    with restarted.test_client() as client:
        assert browser_login(client, "second-secret").status_code == 302
    with restarted.test_client() as client:
        assert browser_login(client, "first-secret").status_code == 200


# ---------------------------------------------------------------------------
# Diagnostics: enough to fix it, nothing that must not be written down
# ---------------------------------------------------------------------------
def test_a_csrf_failure_logs_the_reason_and_the_cookie_mode(tmp_path, caplog):
    app = build_app(
        write_config(tmp_path, secret_key="a-stable-office-secret"),
        tmp_path / "engagement.sqlite3",
    )
    with caplog.at_level("WARNING"), app.test_client() as client:
        client.post("/admin/login", data={"password": PASSWORD}, follow_redirects=False)

    logged = caplog.text
    assert "/admin/login" in logged
    assert "no session cookie" in logged
    assert "scheme=http" in logged
    assert "secure_cookie=False" in logged


def test_a_csrf_failure_logs_no_secret(tmp_path, caplog):
    """Not the token, not the session, not the password, not the signing key."""
    app = build_app(
        write_config(tmp_path, secret_key="a-stable-office-secret"),
        tmp_path / "engagement.sqlite3",
    )
    with caplog.at_level("DEBUG"), app.test_client() as client:
        page = client.get("/admin/login")
        token = form_token(page.get_data(as_text=True))
        with client.session_transaction() as session:
            session["ml_admin_csrf"] = "a-different-token"
        client.post(
            "/admin/login",
            data={"password": PASSWORD, "csrf_token": token},
            follow_redirects=False,
        )

    logged = caplog.text
    assert token not in logged
    assert "a-different-token" not in logged
    assert PASSWORD not in logged
    assert "a-stable-office-secret" not in logged


def test_a_secure_cookie_served_over_http_is_called_out_by_name(tmp_path, caplog):
    """The exact production misconfiguration must name itself in the log."""
    app = build_app(
        write_config(tmp_path, secret_key="a-stable-office-secret"),
        tmp_path / "engagement.sqlite3",
    )
    # Exactly the production state: an HTTP site whose session cookie is marked
    # Secure anyway. That is what Talisman's default did on every request, and
    # it is the one failure whose remedy an operator cannot guess from
    # "This form expired".
    app.config["SESSION_COOKIE_SECURE"] = True
    with caplog.at_level("ERROR"), app.test_client() as client:
        client.post(
            "/admin/login",
            data={"password": PASSWORD},
            base_url="http://localhost",
            follow_redirects=False,
        )

    assert "ssl_enabled=false" in caplog.text
    assert "no browser will ever return it" in caplog.text


def test_the_portal_footer_links_to_the_admin_sign_in(tmp_path):
    """The console is reachable from the UI, not only from a bookmark."""
    app = build_app(
        write_config(tmp_path, secret_key="a-stable-office-secret"),
        tmp_path / "engagement.sqlite3",
    )
    with app.test_client() as client:
        home = client.get("/")

    assert home.status_code == 200
    assert "/admin/login" in home.get_data(as_text=True)
