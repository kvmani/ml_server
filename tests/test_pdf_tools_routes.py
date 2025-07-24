from io import BytesIO

from PyPDF2 import PdfWriter


def _make_pdf(pages: int = 1) -> bytes:
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=72, height=72)
    buf = BytesIO()
    writer.write(buf)
    buf.seek(0)
    return buf.read()


def test_pdf_tools_home(client):
    resp = client.get("/pdf_tools/")
    assert resp.status_code == 200


def test_merge_endpoint(client):
    pdf = _make_pdf()
    data = {
        "file0": (BytesIO(pdf), "a.pdf"),
        "range_file0": "all",
        "file1": (BytesIO(pdf), "b.pdf"),
        "range_file1": "all",
        "order": "0,1",
    }
    resp = client.post("/pdf_tools/merge", data=data, content_type="multipart/form-data")
    assert resp.status_code == 200
    assert resp.mimetype == "application/pdf"


def test_extract_endpoint(client):
    pdf = _make_pdf(2)
    data = {"file": (BytesIO(pdf), "test.pdf"), "range": "1"}
    resp = client.post("/pdf_tools/extract", data=data, content_type="multipart/form-data")
    assert resp.status_code == 200
    assert resp.mimetype == "application/pdf"
