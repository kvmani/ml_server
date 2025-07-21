# tests/test_ebsd_cleanup.py
import io
from unittest.mock import Mock

from ml_server.app.routes import ebsd_cleanup as ec


def test_ebsd_cleanup_get(client):
    response = client.get("/ebsd_cleanup")
    assert response.status_code == 200
    assert b"<html" in response.data


def test_ebsd_cleanup_post_no_file(client):
    response = client.post("/ebsd_cleanup", data={})
    assert response.status_code == 400
    assert b"No EBSD file uploaded" in response.data


def test_ebsd_cleanup_post_success(client, monkeypatch):
    monkeypatch.setattr(ec.requests, "get", lambda *a, **k: Mock(status_code=200))
    monkeypatch.setattr(
        ec.requests,
        "post",
        lambda *a, **k: Mock(status_code=200, json=lambda: {"success": True}),
    )
    data = {"ebsd_file": (io.BytesIO(b"file"), "test.ang")}
    response = client.post(
        "/ebsd_cleanup", data=data, content_type="multipart/form-data"
    )
    assert response.status_code == 200
    assert response.get_json()["success"] is True


def test_ebsd_cleanup_health_failure(client, monkeypatch):
    def raise_exc(*a, **k):
        raise ec.requests.exceptions.RequestException("fail")

    monkeypatch.setattr(ec.requests, "get", raise_exc)
    data = {"ebsd_file": (io.BytesIO(b"file"), "test.ang")}
    response = client.post(
        "/ebsd_cleanup", data=data, content_type="multipart/form-data"
    )
    assert response.status_code == 503
