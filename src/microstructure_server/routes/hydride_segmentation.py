import base64

from flask import Blueprint, jsonify, render_template, request

from config import Config

from ..services.hydride_segmentation import HydrideSegmentationService
from ..services.utils import allowed_file

bp = Blueprint("hydride_segmentation", __name__)
config = Config()
service = HydrideSegmentationService(config)


@bp.route("/hydride_segmentation", methods=["GET", "POST"])
def hydride_segmentation():
    if request.method == "POST":
        if "image" not in request.files:
            return jsonify({"success": False, "error": "No image uploaded"}), 400

        file = request.files["image"]
        if file.filename == "":
            return jsonify({"success": False, "error": "No image selected"}), 400

        allowed_exts = config.config["hydride_segmentation"]["allowed_extensions"]
        if not allowed_file(file.filename, allowed_exts):
            return jsonify({"success": False, "error": "Invalid file type"}), 400

        if not service.is_available():
            return jsonify({"success": False, "error": "Hydride model is not running"}), 503

        try:
            result = service.segment(file)
            file.seek(0)
            original_b64 = base64.b64encode(file.read()).decode()
            segmented_b64 = base64.b64encode(result).decode()
            return jsonify(
                {
                    "success": True,
                    "original_image": f"data:image/png;base64,{original_b64}",
                    "segmented_image": f"data:image/png;base64,{segmented_b64}",
                }
            )
        except Exception as e:
            bp.logger.error(f"Hydride segmentation error: {e}")
            return jsonify({"success": False, "error": str(e)}), 500

    return render_template("hydride_segmentation.html")
