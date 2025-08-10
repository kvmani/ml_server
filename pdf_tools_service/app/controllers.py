from __future__ import annotations

from io import BytesIO

from flask import Blueprint, Response, request
from PyPDF2 import PdfMerger, PdfReader, PdfWriter

pdf_tools_bp = Blueprint("pdf_tools", __name__)


@pdf_tools_bp.get("/")
def home() -> str:
    return "pdf tools"


@pdf_tools_bp.post("/merge")
def merge() -> Response:
    merger = PdfMerger()
    order = request.form.get("order", "").split(",")
    for idx in order:
        file = request.files.get(f"file{idx}")
        if file:
            merger.append(PdfReader(file))
    out = BytesIO()
    merger.write(out)
    merger.close()
    out.seek(0)
    return Response(out.read(), mimetype="application/pdf")


@pdf_tools_bp.post("/extract")
def extract() -> Response:
    file = request.files["file"]
    pages = request.form.get("range", "")
    reader = PdfReader(file)
    writer = PdfWriter()
    for p in pages.split(","):
        if p.isdigit():
            writer.add_page(reader.pages[int(p) - 1])
    out = BytesIO()
    writer.write(out)
    out.seek(0)
    return Response(out.read(), mimetype="application/pdf")
