from ml_server.app.routes import api


def test_health_endpoint(client, monkeypatch):
    monkeypatch.setattr(api, "check_service_health", lambda *a, **k: True)
    monkeypatch.setattr(
        api.redis, "Redis", lambda *a, **k: type("R", (), {"ping": lambda self: True})()
    )
    monkeypatch.setattr(api.celery_app.control, "ping", lambda timeout=1.0: ["ok"])
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "healthy"
    assert data["services"]["redis"] is True


def test_disk_usage_endpoint(client):
    resp = client.get("/disk-usage")
    assert resp.status_code == 200
    json_data = resp.get_json()
    assert "percent" in json_data
    assert 0 <= json_data["percent"] <= 100
