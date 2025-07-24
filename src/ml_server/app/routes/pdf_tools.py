from __future__ import annotations

from io import BytesIO

from flask import Blueprint, jsonify, render_template, request, send_file

from ..services.pdf_tools.extract_service import ExtractService
from ..services.pdf_tools.merge_service import MergeService

bp = Blueprint("pdf_tools", __name__, url_prefix="/pdf_tools")
merge_service = MergeService()
extract_service = ExtractService()


@bp.route("/")
def pdf_tools_home():
    """Landing page for PDF utilities."""
    return render_template("pdf_tools.html")


@bp.route("/merge", methods=["GET", "POST"])
def merge_pdfs():
    """Merge multiple PDF files."""
    if request.method == "POST":
        files: list[tuple[BytesIO, str]] = []
        idx = 0
        while True:
            file = request.files.get(f"file{idx}")
            if not file:
                break
            range_str = request.form.get(f"range_file{idx}", "all")
            files.append((BytesIO(file.read()), range_str))
            idx += 1

        if not files:
            return (
                jsonify({"success": False, "error": "No files uploaded"}),
                400,
            )

        order_param = request.form.get("order")
        order = [int(x) for x in order_param.split(",")] if order_param else None
        output_name = request.form.get("output_name")

        try:
            output = merge_service.process(files, order=order, output_name=output_name)
            return send_file(
                output,
                as_attachment=True,
                download_name=merge_service.output_name,
                mimetype="application/pdf",
            )
        except Exception as exc:  # noqa: BLE001
            return jsonify({"success": False, "error": str(exc)}), 400
    return render_template("merge_pdfs.html")


@bp.route("/extract", methods=["GET", "POST"])
def extract_from_pdf():
    """Extract pages from a PDF file."""
    if request.method == "POST":
        file = request.files.get("file")
        if not file:
            return jsonify({"success": False, "error": "No file uploaded"}), 400
        range_str = request.form.get("range", "all")
        try:
            output = extract_service.process(BytesIO(file.read()), range_str)
            return send_file(
                output,
                as_attachment=True,
                download_name="extracted.pdf",
                mimetype="application/pdf",
            )
        except Exception as exc:  # noqa: BLE001
            return jsonify({"success": False, "error": str(exc)}), 400
    return render_template("extract_from_pdf.html")
