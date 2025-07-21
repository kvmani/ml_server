from __future__ import annotations

import os
import tempfile

import requests
from flask import Blueprint, current_app, jsonify, render_template, request

"""Endpoints for the EBSD cleanup tool and Celery task orchestration."""

from ...celery_app import celery_app, ebsd_cleanup_task
from ...config import Config
from ..services.utils import allowed_file

bp = Blueprint("ebsd_cleanup", __name__)
config = Config()


@bp.route("/ebsd_cleanup", methods=["GET", "POST"])
def ebsd_cleanup():
    if request.method == "POST":
        if "ebsd_file" not in request.files:
            return jsonify({"success": False, "error": "No EBSD file uploaded"}), 400

        file = request.files["ebsd_file"]
        if file.filename == "":
            return jsonify({"success": False, "error": "No selected file"}), 400

        allowed_exts = config.ebsd_cleanup_settings.get("allowed_extensions", [])
        if not allowed_file(file.filename, allowed_exts):
            return jsonify({"success": False, "error": "Invalid file type"}), 400

        file.seek(0, os.SEEK_END)
        if file.tell() > config.ebsd_cleanup_settings.get("file_settings", {}).get("max_size", 0):
            return jsonify({"success": False, "error": "File size exceeds limit"}), 400
        file.seek(0)

        try:
            health_url = config.ebsd_cleanup_settings.get("ml_model", {}).get("health_url")
            if requests.get(health_url, timeout=3).status_code != 200:
                return (
                    jsonify({"success": False, "error": "EBSD ML model is not running"}),
                    503,
                )
        except requests.exceptions.RequestException:
            return (
                jsonify({"success": False, "error": "EBSD ML model is not reachable"}),
                503,
            )

        upload_dir = os.path.join("tmp", "uploads")
        os.makedirs(upload_dir, exist_ok=True)
        _, ext = os.path.splitext(file.filename)
        with tempfile.NamedTemporaryFile(delete=False, dir=upload_dir, suffix=ext) as tmp:
            file.save(tmp.name)
            tmp_path = tmp.name

        if current_app.config.get("TESTING"):
            result = ebsd_cleanup_task(tmp_path)
            return jsonify(result)

        task = ebsd_cleanup_task.delay(tmp_path)
        return jsonify({"task_id": task.id}), 202

    return render_template("ebsd_cleanup.html")


@bp.route("/ebsd_cleanup_status/<task_id>")
def ebsd_cleanup_status(task_id: str):
    task = celery_app.AsyncResult(task_id)
    if not task.ready():
        return jsonify({"status": task.state}), 202
    if task.successful():
        return jsonify(task.result)
    return jsonify({"status": "failure", "error": str(task.result)}), 500
