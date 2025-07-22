import base64
import io

import requests
from flask import Blueprint, jsonify, render_template, request

"""Super-resolution image enhancement routes."""

from ...config import Config
from ..services.utils import allowed_file, ensure_service_available

bp = Blueprint("super_resolution", __name__)
config = Config()


@bp.route("/super_resolution", methods=["GET", "POST"])
def super_resolution():
    """Upscale an uploaded image using the demo model."""
    if request.method == "POST":
        if "image" not in request.files:
            return jsonify({"success": False, "error": "No image uploaded"}), 400

        file = request.files["image"]
        if file.filename == "":
            return jsonify({"success": False, "error": "No image selected"}), 400

        allowed_exts = config.super_resolution_settings.get("allowed_extensions", [])
        if not allowed_file(file.filename, allowed_exts):
            return jsonify({"success": False, "error": "Invalid file type"}), 400

        err = ensure_service_available(
            config.super_resolution_settings.get("ml_model", {}).get("health_url", ""),
            start_cb=config.start_ml_model_service,
            service_name="ML model server",
        )
        if err:
            return err

        try:
            response = requests.post(
                config.ml_model_url,
                files={"image": file},
                timeout=config.super_resolution_settings.get("ml_model", {}).get("timeout", 30),
            )
            if response.status_code == 200:
                orig_io = io.BytesIO()
                file.seek(0)
                file.save(orig_io)
                orig_io.seek(0)
                original_b64 = base64.b64encode(orig_io.getvalue()).decode()

                enhanced_b64 = base64.b64encode(response.content).decode()

                return jsonify(
                    {
                        "success": True,
                        "original_image": f"data:image/png;base64,{original_b64}",
                        "enhanced_image": f"data:image/png;base64,{enhanced_b64}",
                    }
                )
            return (
                jsonify({"success": False, "error": "Model processing failed"}),
                500,
            )
        except Exception as e:
            bp.logger.error(f"Super resolution error: {str(e)}")
            return jsonify({"success": False, "error": str(e)}), 500

    return render_template("super_resolution.html")
