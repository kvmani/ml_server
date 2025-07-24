from __future__ import annotations

"""Flask application factory and blueprint registration."""

import os

from flask import Flask
from flask_compress import Compress
from flask_talisman import Talisman
from werkzeug.middleware.proxy_fix import ProxyFix

from ..config import load_config
from ..celery_app import celery_init_app
from .services.graceful import install_signal_handlers
from .services.startup import start_services


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
    cfg = load_config()
    if cfg.admin_token:
        app.config["ADMIN_TOKEN"] = cfg.admin_token
    app.config["MAIN_ICON_SIZE"] = cfg.main_icon_size
    app.config["TOOLS_ICONS_SIZE"] = cfg.tools_icons_size
    app.secret_key = cfg.secret_key or os.urandom(24)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)
    celery_init_app(app)

    # Blueprints
    from .routes.api import bp as api_bp
    from .routes.download import bp as download_bp
    from .routes.ebsd_cleanup import bp as ebsd_bp
    from .routes.feedback import bp as feedback_bp
    from .routes.hydride_segmentation import bp as hydride_bp
    from .routes.main import bp as main_bp
    from .routes.pdf_tools import bp as pdf_tools_bp
    from .routes.super_resolution import bp as super_res_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(feedback_bp)
    app.register_blueprint(super_res_bp)
    app.register_blueprint(ebsd_bp)
    app.register_blueprint(hydride_bp)
    app.register_blueprint(pdf_tools_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(download_bp)

    if startup:
        start_services()

    return app
