# tests/test_submit_feedback.py
from ml_server.app.services.engagement import list_feedback


def test_submit_feedback_success(client):
    data = {
        "name": "Test User",
        "email": "test@example.com",
        "kind": "feature_request",
        "tool_id": "pdf-tools",
        "message": "Please add OCR.",
    }
    response = client.post("/submit_feedback", data=data, environ_base={"REMOTE_ADDR": "10.1.2.3"})
    assert response.status_code == 201
    response_data = response.get_json()
    assert response_data["success"] is True
    rows = list_feedback(client.application.config["ENGAGEMENT_DATABASE"])
    assert rows[0]["kind"] == "feature_request"
    assert rows[0]["tool_name"] == "PDF Tools"
    assert rows[0]["message"] == "Please add OCR."
    # The portal promises that no personal information is collected or stored:
    # only what the visitor deliberately typed may be persisted.
    assert rows[0]["ip_address"] is None
    assert rows[0]["user_agent"] is None


def test_submit_feedback_missing_fields(client):
    data = {"name": "Test User", "email": "", "message": ""}
    response = client.post("/submit_feedback", data=data)
    assert response.status_code == 400
    assert b"Name, email, and message are required" in response.data


def test_feedback_is_saved_when_optional_email_fails(client, monkeypatch):
    from ml_server.app.services import email_notifications

    client.application.config["EMAIL_SETTINGS"] = {
        "enabled": True,
        "smtp_host": "relay.invalid",
        "from_address": "noreply@example.com",
    }
    monkeypatch.setattr(email_notifications, "_send", lambda *args, **kwargs: False)

    class ImmediateThread:
        def __init__(self, *, target, **kwargs):
            self.target = target

        def start(self):
            self.target()

    monkeypatch.setattr(email_notifications.threading, "Thread", ImmediateThread)
    response = client.post("/submit_feedback", data={
        "name": "Test User", "email": "test@example.com", "message": "Still save this"
    })
    assert response.status_code == 201
    rows = list_feedback(client.application.config["ENGAGEMENT_DATABASE"])
    assert len(rows) == 1
    assert rows[0]["acknowledgement_email_status"] == "failed"
    assert rows[0]["developer_email_status"] == "failed"


def test_browser_analytics_is_persisted(client):
    response = client.post("/api/analytics/event", json={
        "event_name": "tool_open", "tool_id": "tabular-ml", "duration_ms": 1250
    })
    assert response.status_code == 200
    from ml_server.app.services.engagement import analytics_summary

    summary = analytics_summary(client.application.config["ENGAGEMENT_DATABASE"])
    assert summary["sessions"] == 1
    assert summary["tools"][0]["tool_name"] == "Tabular ML Workbench"


def test_analytics_stores_no_identifying_information(client):
    """Browsing analytics must keep only a coarse browser family."""
    response = client.post(
        "/api/analytics/event",
        json={"event_name": "page_view", "duration_ms": 10},
        environ_base={"REMOTE_ADDR": "10.9.8.7"},
        headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Chrome/120.0.0.0 Safari/537.36"},
    )
    assert response.status_code == 200

    import sqlite3

    connection = sqlite3.connect(client.application.config["ENGAGEMENT_DATABASE"])
    connection.row_factory = sqlite3.Row
    row = connection.execute("SELECT * FROM analytics_sessions").fetchone()
    connection.close()

    assert row["ip_address"] is None
    assert row["user_agent"] is None
    assert row["browser_family"] == "Chrome"
    # Only a coarse major-version bucket is kept, never the full dotted version.
    assert row["browser_major_version"] == "120"


def test_browser_major_version_is_coarse_bucket_only():
    from ml_server.app.services.engagement import browser_family, browser_major_version

    ua = "Mozilla/5.0 (X11; Linux x86_64) Firefox/121.5.2"
    family = browser_family(ua)
    assert family == "Firefox"
    assert browser_major_version(ua, family) == "121"
    assert browser_major_version(None) is None
    assert browser_major_version("no markers here") is None


def test_existing_identifiers_are_erased_on_upgrade(tmp_path):
    """Upgrading an older deployment must clear anything previously stored."""
    from ml_server.app.services.engagement import initialize_database

    database = str(tmp_path / "legacy.sqlite3")
    initialize_database(database)

    import sqlite3

    connection = sqlite3.connect(database)
    connection.execute(
        "INSERT INTO analytics_sessions (session_id, ip_address, user_agent,"
        " started_at, last_seen_at) VALUES ('s1', '10.0.0.5', 'Firefox/1.0', 'x', 'x')"
    )
    connection.commit()
    connection.close()

    initialize_database(database)

    connection = sqlite3.connect(database)
    row = connection.execute(
        "SELECT ip_address, user_agent FROM analytics_sessions WHERE session_id = 's1'"
    ).fetchone()
    connection.close()
    assert row == (None, None)
