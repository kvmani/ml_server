# tests/test_super_resolution.py
import io
from unittest.mock import Mock

from ml_server.app.routes import super_resolution as sr


def test_super_resolution_get(client):
    response = client.get("/super_resolution")
    assert response.status_code == 200
    assert b"<html" in response.data


def test_super_resolution_post_no_file(client):
    response = client.post("/super_resolution", data={})
    assert response.status_code == 400
    assert b"No image uploaded" in response.data


def test_super_resolution_post_success(client, monkeypatch):
    monkeypatch.setattr(sr.requests, "get", lambda *a, **k: Mock(status_code=200))
    monkeypatch.setattr(
        sr.requests, "post", lambda *a, **k: Mock(status_code=200, content=b"data")
    )
    data = {"image": (io.BytesIO(b"img"), "test.png")}
    response = client.post(
        "/super_resolution", data=data, content_type="multipart/form-data"
    )
    assert response.status_code == 200
    assert response.get_json()["success"] is True


def test_super_resolution_health_failure(client, monkeypatch):
    def raise_exc(*a, **k):
        raise sr.requests.exceptions.RequestException("fail")

    monkeypatch.setattr(sr.requests, "get", raise_exc)
    monkeypatch.setattr(sr.config, "start_ml_model_service", lambda: False)
    data = {"image": (io.BytesIO(b"img"), "test.png")}
    response = client.post(
        "/super_resolution", data=data, content_type="multipart/form-data"
    )
    assert response.status_code == 503
