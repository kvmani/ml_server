import shutil

import redis
from flask import Blueprint, jsonify

from ...celery_app import celery_app
from ...config import Config
from ..services.metrics import disk_usage_percent, metrics_response
from ..services.utils import check_service_health

"""API endpoints for checking service status and metrics."""

bp = Blueprint("api", __name__)
config = Config()


@bp.route("/api/check_model_status")
def api_check_model_status():
    """Health check for the super-resolution model."""
    return jsonify({"running": check_service_health(config.ml_model_health_url)})


@bp.route("/api/check_ebsd_model_status")
def api_check_ebsd_model_status():
    """Health check for the EBSD cleanup model."""
    health_url = config.config["ebsd_cleanup"]["ml_model"]["health_url"]
    return jsonify({"running": check_service_health(health_url)})


@bp.route("/api/check_hydride_model_status")
def api_check_hydride_model_status():
    """Health check for the hydride segmentation model."""
    health_url = config.hydride_segmentation_settings.get("ml_model", {}).get("health_url")
    return jsonify({"running": check_service_health(health_url)})


@bp.route("/api/upload_config")
def api_upload_config():
    """Expose frontend upload limits."""
    max_size = config.super_resolution_settings.get("image_settings", {}).get("max_size", 0)
    return jsonify({"max_size": max_size})


@bp.route("/health")
def health() -> tuple:
    """Aggregated health check for all services."""
    services = {
        "super_resolution": check_service_health(config.ml_model_health_url),
        "ebsd_cleanup": check_service_health(
            config.config["ebsd_cleanup"]["ml_model"]["health_url"]
        ),
        "hydride_segmentation": check_service_health(
            config.hydride_segmentation_settings.get("ml_model", {}).get("health_url")
        ),
    }
    try:
        r = redis.Redis(host="redis", port=6379)
        r.ping()
        services["redis"] = True
    except redis.RedisError:
        services["redis"] = False

    try:
        services["celery"] = bool(celery_app.control.ping(timeout=1.0))
    except Exception:  # noqa: BLE001
        services["celery"] = False

    overall = "healthy" if all(services.values()) else "degraded"
    return jsonify({"services": services, "status": overall})


@bp.route("/disk-usage")
def disk_usage():
    """Return server disk usage information."""
    usage = shutil.disk_usage("/")
    percent = usage.used / usage.total * 100
    disk_usage_percent.set(percent)
    return jsonify(
        {
            "total": usage.total,
            "used": usage.used,
            "free": usage.free,
            "percent": percent,
        }
    )


@bp.route("/metrics")
def metrics():
    """Expose Prometheus metrics."""
    return metrics_response()
