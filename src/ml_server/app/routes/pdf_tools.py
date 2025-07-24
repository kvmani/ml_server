from __future__ import annotations

from io import BytesIO

from flask import Blueprint, jsonify, render_template, request, send_file

from ..services.pdf_tools.merge_service import MergeService
from ..services.pdf_tools.extract_service import ExtractService

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
        files = [(BytesIO(f.read()), "all") for f in request.files.getlist("files")]
        if not files:
            return (
                jsonify({"success": False, "error": "No files uploaded"}),
                400,
            )
        try:
            output = merge_service.process(files)
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
