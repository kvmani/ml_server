"""The admin console: authentication, live activity, analytics and diagnostics."""

from __future__ import annotations

import pytest

from ml_server.app.admin import auth
from ml_server.app.server import create_app
from ml_server.app.services.live_activity import live_activity

PASSWORD = "office-admin-secret"


@pytest.fixture
def admin_client(client, monkeypatch):
    """A client whose application has a known admin password and clean state."""
    # The environment outranks configuration at runtime, which is what a
    # deployment wants and what a test must not inherit from a developer's .env.
    monkeypatch.delenv("ML_SERVER_ADMIN_PASSWORD", raising=False)
    monkeypatch.delenv("ML_SERVER_ADMIN_PASSWORD_HASH", raising=False)
    client.application.config["ADMIN_TOKEN"] = PASSWORD
    client.application.config["ADMIN_PASSWORD"] = PASSWORD
    client.application.config["ADMIN_PASSWORD_HASH"] = ""
    auth.attempt_limiter.reset()
    live_activity.reset()
    return client


def sign_in(client, password: str = PASSWORD):
    page = client.get("/admin/login")
    assert page.status_code == 200
    with client.session_transaction() as session:
        token = session.get("ml_admin_csrf")
    return client.post(
        "/admin/login",
        data={"password": password, "csrf_token": token},
        follow_redirects=False,
    )


# --------------------------------------------------------------------------
# Authentication
# --------------------------------------------------------------------------
def test_dashboard_requires_authentication(admin_client):
    response = admin_client.get("/admin/", follow_redirects=False)

    assert response.status_code == 302
    assert "/admin/login" in response.headers["Location"]


def test_json_api_refuses_anonymous_callers_without_redirecting(admin_client):
    """A dashboard poll that has lost its session must fail, not follow a redirect."""
    for endpoint in ("live", "overview", "logs", "diagnostics", "feedback", "metrics"):
        response = admin_client.get(f"/admin/api/{endpoint}")
        assert response.status_code == 401, endpoint


def test_correct_password_opens_the_console(admin_client):
    response = sign_in(admin_client)

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/admin/")
    assert admin_client.get("/admin/").status_code == 200


def test_wrong_password_is_refused_and_leaves_no_session(admin_client):
    response = sign_in(admin_client, "not-the-password")

    assert response.status_code == 200
    assert "Incorrect password" in response.data.decode("utf-8")
    assert admin_client.get("/admin/", follow_redirects=False).status_code == 302


def test_login_without_a_csrf_token_is_rejected(admin_client):
    admin_client.get("/admin/login")
    response = admin_client.post("/admin/login", data={"password": PASSWORD})

    assert "expired" in response.data.decode("utf-8")
    assert admin_client.get("/admin/", follow_redirects=False).status_code == 302


def test_repeated_failures_lock_the_address_out(admin_client):
    for _ in range(auth.MAX_FAILED_ATTEMPTS):
        sign_in(admin_client, "wrong")

    response = sign_in(admin_client, PASSWORD)

    assert "Too many failed attempts" in response.data.decode("utf-8")
    assert admin_client.get("/admin/", follow_redirects=False).status_code == 302


def test_logout_ends_the_session(admin_client):
    sign_in(admin_client)
    assert admin_client.get("/admin/").status_code == 200

    admin_client.get("/admin/logout")

    assert admin_client.get("/admin/", follow_redirects=False).status_code == 302


def test_a_password_hash_is_accepted_and_the_plaintext_is_not_needed(admin_client):
    admin_client.application.config["ADMIN_PASSWORD_HASH"] = auth.hash_password("from-a-hash")
    admin_client.application.config["ADMIN_PASSWORD"] = ""
    admin_client.application.config["ADMIN_TOKEN"] = ""

    assert sign_in(admin_client, "from-a-hash").status_code == 302
    admin_client.get("/admin/logout")
    assert sign_in(admin_client, "wrong").status_code == 200


def test_an_unconfigured_server_refuses_every_password(admin_client):
    """A deployment that forgot to set a secret must be closed, never open."""
    admin_client.application.config["ADMIN_PASSWORD_HASH"] = ""
    admin_client.application.config["ADMIN_PASSWORD"] = ""
    admin_client.application.config["ADMIN_TOKEN"] = ""

    page = sign_in(admin_client, "")
    body = page.data.decode("utf-8")

    assert "not configured" in body
    assert admin_client.get("/admin/", follow_redirects=False).status_code == 302


def test_placeholder_secrets_do_not_count_as_configured(admin_client):
    admin_client.application.config["ADMIN_PASSWORD_HASH"] = ""
    admin_client.application.config["ADMIN_PASSWORD"] = "changeme"
    admin_client.application.config["ADMIN_TOKEN"] = "changeme"

    assert sign_in(admin_client, "changeme").status_code == 200
    assert admin_client.get("/admin/", follow_redirects=False).status_code == 302


def test_the_legacy_token_link_still_works(admin_client):
    """Existing bookmarks and scripts must survive the upgrade."""
    response = admin_client.get(f"/admin/?token={PASSWORD}")

    assert response.status_code == 200


def test_login_never_redirects_off_site(admin_client):
    admin_client.get("/admin/login")
    with admin_client.session_transaction() as session:
        token = session.get("ml_admin_csrf")

    response = admin_client.post(
        "/admin/login?next=https://example.com/steal",
        data={"password": PASSWORD, "csrf_token": token},
    )

    assert response.headers["Location"].endswith("/admin/")


# --------------------------------------------------------------------------
# Live activity
# --------------------------------------------------------------------------
def test_live_activity_reports_which_address_uses_which_service(admin_client):
    sign_in(admin_client)
    admin_client.get("/pdf_tools/", environ_overrides={"REMOTE_ADDR": "10.4.1.7"})
    admin_client.get("/", environ_overrides={"REMOTE_ADDR": "10.4.1.9"})

    payload = admin_client.get("/admin/api/live").get_json()

    addresses = {client["ip"]: client for client in payload["clients"]}
    assert "10.4.1.7" in addresses
    assert addresses["10.4.1.7"]["current_service"] == "PDF Tools"
    assert "10.4.1.9" in addresses
    services = {service["service"] for service in payload["services"]}
    assert {"PDF Tools", "Portal"} <= services


def test_live_activity_forgets_idle_clients(admin_client):
    live_activity.record(ip="10.9.9.9", service_name="Portal", now=1000.0)

    assert live_activity.active_client_count(now=1000.0) == 1
    assert live_activity.active_client_count(now=1000.0 + live_activity.ttl_seconds + 1) == 0


def test_live_activity_is_capped(admin_client):
    registry = type(live_activity)(ttl_seconds=300, max_clients=3)
    for index in range(10):
        registry.record(ip=f"10.0.0.{index}", service_name="Portal", now=1000.0 + index)

    assert registry.active_client_count(now=1010.0) == 3


# --------------------------------------------------------------------------
# Analytics
# --------------------------------------------------------------------------
def test_overview_reports_usage_timing_and_unique_visitors(admin_client):
    sign_in(admin_client)
    admin_client.post(
        "/api/analytics/event",
        json={"event_name": "tool_open", "tool_id": "pdf-tools", "duration_ms": 500},
        headers={"User-Agent": "Mozilla/5.0 Firefox/121.0"},
    )
    admin_client.get("/pdf_tools/", environ_overrides={"REMOTE_ADDR": "10.4.1.7"})
    admin_client.get("/", environ_overrides={"REMOTE_ADDR": "10.4.2.2"})

    payload = admin_client.get("/admin/api/overview?window=all&months=3").get_json()

    assert payload["status"] == "ok"
    assert payload["totals"]["requests"] >= 2
    assert payload["totals"]["unique_clients"] >= 2
    assert "p95" in payload["totals"]
    assert len(payload["unique_clients_by_month"]) == 3
    assert any(tool["tool_name"] == "PDF Tools" for tool in payload["tools"])
    assert any(entry["window"] == "365d" for entry in payload["unique_clients_by_window"])
    assert payload["browsers"]


def test_months_of_history_is_settable(admin_client):
    sign_in(admin_client)

    for months, expected in ((1, 1), (24, 24), (500, 120), (0, 1)):
        payload = admin_client.get(f"/admin/api/overview?window=all&months={months}").get_json()
        assert len(payload["unique_clients_by_month"]) == expected


def test_unknown_window_falls_back_instead_of_failing(admin_client):
    sign_in(admin_client)

    payload = admin_client.get("/admin/api/overview?window=nonsense").get_json()

    assert payload["window"] == "24h"


def test_percentiles_are_ordered(admin_client):
    sign_in(admin_client)
    for _ in range(20):
        admin_client.get("/")

    totals = admin_client.get("/admin/api/overview?window=all").get_json()["totals"]

    assert totals["p50"] <= totals["p90"] <= totals["p95"] <= totals["p99"]


def test_stored_analytics_hold_no_address(admin_client):
    """The durable database must keep a digest, never an address."""
    import sqlite3

    admin_client.get("/", environ_overrides={"REMOTE_ADDR": "10.4.7.1"})
    connection = sqlite3.connect(admin_client.application.config["ENGAGEMENT_DATABASE"])
    rows = connection.execute(
        "SELECT ip_address, user_agent, client_hash FROM analytics_sessions"
    ).fetchall()
    connection.close()

    assert rows
    for ip_address, user_agent, client_hash in rows:
        assert ip_address is None
        assert user_agent is None
        assert client_hash and "10.4.7.1" not in client_hash


def test_export_downloads_the_report(admin_client):
    sign_in(admin_client)

    response = admin_client.get("/admin/api/export?window=7d")

    assert response.status_code == 200
    assert "attachment" in response.headers["Content-Disposition"]
    assert response.get_json()["window"] == "7d"


def test_pruning_respects_the_retention_window(admin_client):
    from ml_server.app.services.engagement import prune_analytics, record_event

    database = admin_client.application.config["ENGAGEMENT_DATABASE"]
    record_event(database, session_id="a" * 20, event_name="request", duration_ms=5)
    result = prune_analytics(database, retention_months=24)

    assert result["events_removed"] == 0
    assert result["sessions_removed"] == 0


# --------------------------------------------------------------------------
# Logs
# --------------------------------------------------------------------------
def test_logs_can_be_filtered_by_level_and_text(tmp_path):
    from ml_server.app.services.logs import read_log

    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    (log_dir / "app.log").write_text(
        "2026-09-07 10:00:00,001 [INFO] Server starting\n"
        "2026-09-07 10:00:01,002 [WARNING] Disk is filling up\n"
        "2026-09-07 10:00:02,003 [ERROR] Upload failed\n"
        "Traceback (most recent call last):\n"
        "  ValueError: broken\n"
        "2026-09-07 10:00:03,004 [DEBUG] Cache hit\n",
        encoding="utf-8",
    )

    everything = read_log(str(log_dir), "app.log")
    assert everything["total_records"] == 4
    assert everything["counts"]["ERROR"] == 1
    assert everything["counts"]["DEBUG"] == 1

    problems = read_log(str(log_dir), "app.log", level="WARNING")
    assert [record["level"] for record in problems["records"]] == ["ERROR", "WARNING"]

    # A traceback belongs to the record above it, not to a record of its own.
    error = problems["records"][0]
    assert "ValueError: broken" in error["detail"]

    searched = read_log(str(log_dir), "app.log", search="disk")
    assert len(searched["records"]) == 1
    assert searched["records"][0]["level"] == "WARNING"


def test_missing_log_file_is_reported_not_raised(tmp_path):
    from ml_server.app.services.logs import read_log

    payload = read_log(str(tmp_path / "nowhere"), "app.log")

    assert payload["exists"] is False
    assert payload["records"] == []


def test_log_api_returns_records_and_counts(admin_client):
    sign_in(admin_client)

    payload = admin_client.get("/admin/api/logs?level=WARNING&limit=50").get_json()

    assert payload["status"] == "ok"
    assert payload["level"] == "WARNING"
    assert set(payload["counts"]) == {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


# --------------------------------------------------------------------------
# Diagnostics
# --------------------------------------------------------------------------
def test_diagnostics_report_host_application_and_dependencies(admin_client):
    sign_in(admin_client)

    payload = admin_client.get("/admin/api/diagnostics").get_json()

    assert payload["status"] == "ok"
    assert payload["application"]["version"]
    assert payload["application"]["route_count"] > 0
    assert payload["host"]["hostname"]
    assert payload["uptime"]["process_human"]
    assert payload["disks"]
    assert {check["name"] for check in payload["dependencies"]} == {"Redis", "Celery workers"}
    assert payload["storage"]["analytics_events"] >= 0


def test_metrics_text_is_available_to_administrators(admin_client):
    sign_in(admin_client)

    payload = admin_client.get("/admin/api/metrics").get_json()

    assert "active_users" in payload["metrics"]


def test_dashboard_shell_loads_vendored_chart_library(admin_client):
    """The office server has no internet, so charts must not come from a CDN."""
    sign_in(admin_client)

    body = admin_client.get("/admin/").data.decode("utf-8")

    assert "/static/vendor/chartjs/chart.umd.min.js" in body
    assert "cdn.jsdelivr.net" not in body
    assert "cdnjs" not in body


def test_feedback_view_is_protected_and_renders(admin_client):
    assert admin_client.get("/admin/feedback", follow_redirects=False).status_code == 302

    sign_in(admin_client)

    assert admin_client.get("/admin/feedback").status_code == 200


def test_home_page_offers_an_admin_sign_in(client):
    body = client.get("/").data.decode("utf-8")

    assert "/admin/login" in body


def test_admin_pages_are_not_indexable(admin_client):
    body = admin_client.get("/admin/login").data.decode("utf-8")

    assert "noindex" in body


def test_create_app_registers_the_admin_blueprint():
    app = create_app(startup=False)

    assert "admin" in app.blueprints
