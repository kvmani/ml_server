"""Proxy endpoints that forward PDF requests to the external pdf_tools plugin.

The endpoints here expose only thin wrappers that forward to pdf_tools via the
standard plugin interface. No PDF processing logic is implemented in
ml_server.
"""
from __future__ import annotations

import json
from typing import Any, Dict, cast

import requests
from flask import Blueprint, Response, current_app, render_template, request

PDF_TIMEOUT = 30

bp = Blueprint("pdf_tools", __name__, url_prefix="/pdf_tools")


def _plugin_base_url() -> str | None:
    """Return the configured base URL for the pdf_tools plugin."""
    registry = current_app.config.get("PLUGIN_REGISTRY")
    plugin = registry.get_tool("pdf_tools") if registry else None
    return getattr(plugin, "base_url", None)


def _forward(path: str) -> Response:
    """Forward the current request to the pdf_tools service."""
    base = _plugin_base_url()
    if not base:
        data = {"error": {"code": "unavailable", "message": "pdf_tools plugin not configured"}}
        return Response(json.dumps(data), status=503, mimetype="application/json")

    files: Dict[str, tuple[str, Any, str]] = {
        k: (f.filename, f.stream, f.mimetype or "application/octet-stream")
        for k, f in request.files.items()
    }
    try:
        resp = requests.post(
            f"{base}{path}", data=request.form, files=cast(Any, files), timeout=PDF_TIMEOUT
        )
    except requests.RequestException as exc:
        data = {"error": {"code": "network", "message": str(exc)}}
        return Response(json.dumps(data), status=502, mimetype="application/json")
    return Response(
        resp.content, status=resp.status_code, mimetype=resp.headers.get("Content-Type")
    )


@bp.get("/merge", endpoint="merge_form")
def merge_form() -> str:
    """Render the PDF merge form."""
    return render_template("merge_pdfs.html")


@bp.post("/merge")
def merge() -> Response:
    """Proxy a merge request to the pdf_tools plugin via the standard plugin interface.

    No PDF logic is implemented in ml_server.
    """
    return _forward("/tasks/merge")


@bp.get("/extract", endpoint="extract_form")
def extract_form() -> str:
    """Render the PDF extract form."""
    return render_template("extract_from_pdf.html")


@bp.post("/extract")
def extract() -> Response:
    """Proxy a page extraction request to the pdf_tools plugin via the standard
    plugin interface.

    No PDF logic is implemented in ml_server.
    """
    return _forward("/tasks/extract")
