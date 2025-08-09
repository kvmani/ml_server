from __future__ import annotations

"""Flask application factory and blueprint registration."""

import os
import time
import logging

from flask import Flask, g, request
from flask_compress import Compress
from flask_talisman import Talisman
from werkzeug.middleware.proxy_fix import ProxyFix

from ..config import load_config
from ..celery_app import celery_init_app
from .services.graceful import install_signal_handlers
from .services.startup import start_services
from .services.metrics import (
    request_latency,
    request_count,
    error_count,
    visit_counter,
    active_users_gauge,
    update_uptime,
)
from .admin.dashboard import init_admin


def create_app(startup: bool = True) -> Flask:
    """Create and configure the Flask application."""
    package_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app = Flask(
        "ml_server",
        template_folder=os.path.join(package_root, "templates"),
        static_folder=os.path.join(package_root, "static"),
    )
    Compress(app)
    Talisman(
        app,
        content_security_policy={
        "default-src": ["'self'"],
        "script-src": ["'self'", "'nonce'"],
        "img-src": ["'self'", "data:"],  # <-- This line allows base64 images
    },
        force_https=False,
        strict_transport_security=False,
    )
    install_signal_handlers()
    logging.getLogger(__name__).info("Server starting")
    app.start_time = time.time()
    cfg = load_config()
    if cfg.admin_token:
        app.config["ADMIN_TOKEN"] = cfg.admin_token
    app.config["MAIN_ICON_SIZE"] = cfg.main_icon_size
    app.config["TOOLS_ICONS_SIZE"] = cfg.tools_icons_size
    app.secret_key = cfg.secret_key or os.urandom(24)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)
    celery_init_app(app)

    # Metrics instrumentation
    @app.before_request
    def _before_request() -> None:
        g.start_time = time.time()

    @app.after_request
    def _after_request(response):  # type: ignore[override]
        latency = time.time() - g.get("start_time", time.time())
        endpoint = request.endpoint or "unknown"
        visit_counter.labels(endpoint=endpoint).inc()
        request_latency.labels(endpoint=endpoint).observe(latency)
        request_count.labels(endpoint=endpoint, status=response.status_code).inc()
        if response.status_code >= 400:
            etype = "5xx" if response.status_code >= 500 else "4xx"
            error_count.labels(endpoint=endpoint, type=etype).inc()
        # Track active users
        active = getattr(app, "_active_users", {})
        now = time.time()
        active[request.remote_addr] = now
        for ip, ts in list(active.items()):
            if now - ts > 300:
                active.pop(ip, None)
        active_users_gauge.set(len(active))
        app._active_users = active
        update_uptime(app.start_time)
        return response

    # Blueprints
    from .routes.api import bp as api_bp
    from .routes.download import bp as download_bp
    from .routes.ebsd_cleanup import bp as ebsd_bp
    from .routes.feedback import bp as feedback_bp
    from .routes.hydride_segmentation import bp as hydride_bp
    from .routes.main import bp as main_bp
    #from .routes.pdf_tools import bp as pdf_tools_bp
    from pdf_tools_service.app.controllers import pdf_tools_bp

    from .routes.super_resolution import bp as super_res_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(feedback_bp)
    app.register_blueprint(super_res_bp)
    app.register_blueprint(ebsd_bp)
    app.register_blueprint(hydride_bp)
    #app.register_blueprint(pdf_tools_bp)
    app.register_blueprint(pdf_tools_bp, url_prefix="/pdf-tools")
    app.register_blueprint(api_bp)
    app.register_blueprint(download_bp)

    # Admin dashboard
    init_admin(app)

    if startup:
        start_services()

    return app
