import base64
import io

import requests
from flask import Blueprint, jsonify, render_template, request

"""Super-resolution image enhancement routes."""

from ...config import Config
from ..services.utils import allowed_file

bp = Blueprint("super_resolution", __name__)
config = Config()


@bp.route("/super_resolution", methods=["GET", "POST"])
def super_resolution():
    if request.method == "POST":
        if "image" not in request.files:
            return jsonify({"success": False, "error": "No image uploaded"}), 400

        try:
            response = requests.get(config.config["super_resolution"]["ml_model"]["health_url"])
            if response.status_code != 200:
                if config.start_ml_model_service():
                    return (
                        jsonify(
                            {
                                "success": False,
                                "error": (
                                    "ML model server was not running. "
                                    "It has been started. Please try your request again."
                                ),
                            }
                        ),
                        503,
                    )
                else:
                    return (
                        jsonify(
                            {
                                "success": False,
                                "error": (
                                    "ML model server is not running and could not be started. "
                                    "Please try again later."
                                ),
                            }
                        ),
                        503,
                    )
        except requests.exceptions.RequestException:
            if config.start_ml_model_service():
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": (
                                "ML model server was not running. "
                                "It has been started. Please try your request again."
                            ),
                        }
                    ),
                    503,
                )
            else:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": (
                                "ML model server is not running and could not be started. "
                                "Please try again later."
                            ),
                        }
                    ),
                    503,
                )

        file = request.files["image"]
        if file.filename == "":
            return jsonify({"success": False, "error": "No image selected"}), 400

        if allowed_file(file.filename, config.config["super_resolution"]["allowed_extensions"]):
            try:
                response = requests.post(config.ml_model_url, files={"image": file})
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
                else:
                    return (
                        jsonify({"success": False, "error": "Model processing failed"}),
                        500,
                    )
            except Exception as e:
                bp.logger.error(f"Super resolution error: {str(e)}")
                return jsonify({"success": False, "error": str(e)}), 500
        return jsonify({"success": False, "error": "Invalid file type"}), 400
    return render_template("super_resolution.html")
