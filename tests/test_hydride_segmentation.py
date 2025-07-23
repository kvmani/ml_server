import io
import sys

from PIL import Image


def _dummy_result():
    img = Image.new("RGB", (1, 1), color="white")
    return {
        "original": img,
        "mask": img,
        "overlay": img,
        "orientation": img,
        "size_distribution": img,
        "angle_distribution": img,
    }


def test_hydride_segmentation_get(client):
    resp = client.get("/hydride_segmentation")
    assert resp.status_code == 200
    assert b"form" in resp.data


def test_hydride_segmentation_post_no_file(client):
    resp = client.post("/hydride_segmentation", data={})
    assert resp.status_code == 400
    assert b"No image uploaded" in resp.data


def test_hydride_segmentation_success(client, monkeypatch):
    module = type("m", (), {"segment_hydride_image": lambda *a, **k: _dummy_result()})
    monkeypatch.setitem(sys.modules, "hydride_segmentation_api", module)
    buf = io.BytesIO()
    Image.new("RGB", (1, 1)).save(buf, format="PNG")
    buf.seek(0)
    data = {"image": (buf, "img.png")}
    resp = client.post(
        "/hydride_segmentation", data=data, content_type="multipart/form-data"
    )
    assert resp.status_code == 200
    assert b"Segmentation Results" in resp.data
