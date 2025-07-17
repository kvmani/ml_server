from flask import Blueprint, jsonify

from config import Config

from ..services.utils import check_service_health

bp = Blueprint("api", __name__)
config = Config()


@bp.route("/api/check_model_status")
def api_check_model_status():
    return jsonify({"running": check_service_health(config.ml_model_health_url)})


@bp.route("/api/check_ebsd_model_status")
def api_check_ebsd_model_status():
    health_url = config.config["ebsd_cleanup"]["ml_model"]["health_url"]
    return jsonify({"running": check_service_health(health_url)})


@bp.route("/api/check_hydride_model_status")
def api_check_hydride_model_status():
    health_url = config.config["hydride_segmentation"]["ml_model"]["health_url"]
    return jsonify({"running": check_service_health(health_url)})
