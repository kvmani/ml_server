from ml_server.app.server import create_app


def test_admin_dashboard_access():
    app = create_app(startup=False)
    app.config["TESTING"] = True
    app.config["ADMIN_TOKEN"] = "secret"
    with app.test_client() as client:
        resp = client.get("/admin?token=secret", follow_redirects=True)
        assert resp.status_code == 200


def test_admin_dashboard_shows_anonymous_analytics(client):
    """The dashboard must render browser families and never an IP column."""
    client.post(
        "/api/analytics/event",
        json={"event_name": "tool_open", "tool_id": "pdf-tools", "duration_ms": 500},
        headers={"User-Agent": "Mozilla/5.0 Firefox/121.0"},
    )
    client.application.config["ADMIN_TOKEN"] = "secret"
    response = client.get("/admin/?token=secret")

    assert response.status_code == 200
    body = response.data.decode("utf-8")
    assert "Firefox" in body
    assert "Recent anonymous sessions" in body
    assert "IP addresses" not in body
