import os

from flask import Blueprint, send_file

bp = Blueprint("download", __name__)


@bp.route("/download_processed_data")
def download_processed_data():
    try:
        file_path = "tmp/enhanced_ebsd_map.png"
        if not os.path.exists(file_path):
            return "Processed file not found.", 404
        return send_file(
            file_path,
            mimetype="image/png",
            as_attachment=True,
            download_name="enhanced_ebsd_map.png",
        )
    except Exception:
        return "Internal Server Error", 500
