from __future__ import annotations

import os

from flask import Flask
from flask_compress import Compress
from flask_talisman import Talisman
from werkzeug.middleware.proxy_fix import ProxyFix

from config import load_config

from .services.startup import start_services
from .services.graceful import install_signal_handlers


def create_app(startup: bool = True) -> Flask:
    """Create and configure the Flask application."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(base_dir))
    app = Flask(
        "microstructure_server",
        template_folder=os.path.join(project_root, "templates"),
        static_folder=os.path.join(project_root, "static"),
    )
    Compress(app)
    Talisman(
        app,
        content_security_policy={
            "default-src": "'self'",
            "script-src": ["'self'", "'nonce'"],
        },
        force_https=False,
        strict_transport_security=False,
    )
    install_signal_handlers()
    cfg = load_config()
    if cfg.admin_token:
        app.config["ADMIN_TOKEN"] = cfg.admin_token
    app.secret_key = cfg.secret_key or os.urandom(24)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

    # Blueprints
    from .routes.api import bp as api_bp
    from .routes.download import bp as download_bp
    from .routes.ebsd_cleanup import bp as ebsd_bp
    from .routes.feedback import bp as feedback_bp
    from .routes.hydride_segmentation import bp as hydride_bp
    from .routes.main import bp as main_bp
    from .routes.super_resolution import bp as super_res_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(feedback_bp)
    app.register_blueprint(super_res_bp)
    app.register_blueprint(ebsd_bp)
    app.register_blueprint(hydride_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(download_bp)

    if startup:
        start_services()

    return app
