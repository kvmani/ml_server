# tests/test_hydride_segmentation.py
import io
from unittest.mock import Mock

from microstructure_server.routes import hydride_segmentation as hs


def test_hydride_segmentation_get(client):
    response = client.get("/hydride_segmentation")
    assert response.status_code == 200
    assert b"<html" in response.data


def test_hydride_segmentation_post_no_file(client):
    response = client.post("/hydride_segmentation", data={})
    assert response.status_code == 400
    assert b"No image uploaded" in response.data


def test_hydride_segmentation_success(client, monkeypatch):
    monkeypatch.setattr(hs.service, "is_available", lambda: True)
    monkeypatch.setattr(hs.service, "segment", lambda f: b"data")
    data = {"image": (io.BytesIO(b"img"), "img.png")}
    response = client.post("/hydride_segmentation", data=data, content_type="multipart/form-data")
    assert response.status_code == 200
    assert response.get_json()["success"] is True


def test_hydride_segmentation_unavailable(client, monkeypatch):
    monkeypatch.setattr(hs.service, "is_available", lambda: False)
    data = {"image": (io.BytesIO(b"img"), "img.png")}
    response = client.post("/hydride_segmentation", data=data, content_type="multipart/form-data")
    assert response.status_code == 503
