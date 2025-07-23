"""Routes handling hydride segmentation requests."""

from __future__ import annotations

import base64
import io

from flask import Blueprint, current_app, render_template, request
from PIL import Image

from ...config import Config
from ..services.utils import allowed_file

bp = Blueprint("hydride_segmentation", __name__)
config = Config()


def _to_b64(image: Image.Image) -> str:
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


@bp.route("/hydride_segmentation", methods=["GET", "POST"])
def hydride_segmentation():
    """Run hydride segmentation on an uploaded image."""
    if request.method == "POST":
        if "image" not in request.files:
            return (
                render_template("hydride_segmentation.html", error="No image uploaded"),
                400,
            )

        file = request.files["image"]
        if file.filename == "":
            return (
                render_template("hydride_segmentation.html", error="No image selected"),
                400,
            )

        allowed_exts = config.hydride_segmentation_settings.get(
            "allowed_extensions", []
        )
        if not allowed_file(file.filename, allowed_exts):
            return (
                render_template("hydride_segmentation.html", error="Invalid file type"),
                400,
            )

        try:
            from hydride_segmentation_api import segment_hydride_image
        except ImportError:
            return (
                render_template(
                    "hydride_segmentation.html",
                    error="Segmentation library not installed",
                ),
                500,
            )

        algorithm = request.form.get("algorithm", "ml")
        params = {}
        if algorithm == "conventional":
            try:
                params["area_threshold"] = int(request.form.get("area_threshold", "95"))
                params["tile_size"] = int(request.form.get("tile_size", "8"))
            except ValueError:
                return (
                    render_template(
                        "hydride_segmentation.html", error="Invalid parameter values"
                    ),
                    400,
                )

        try:
            img = Image.open(file.stream).convert("RGB")
            result = segment_hydride_image(img, model=algorithm, params=params)
        except Exception as e:  # noqa: BLE001
            current_app.logger.error(f"Hydride segmentation error: {e}")
            return (
                render_template(
                    "hydride_segmentation.html", error="Segmentation failed"
                ),
                500,
            )

        images = {
            name: f"data:image/png;base64,{_to_b64(im)}" for name, im in result.items()
        }
        return render_template("hydride_results.html", images=images)

    return render_template("hydride_segmentation.html")
