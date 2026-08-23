from __future__ import annotations

"""Flask application factory and blueprint registration."""

import logging
import os
import time
import uuid

from flask import Flask, g, request
from flask_compress import Compress
from flask_talisman import Talisman
from werkzeug.middleware.proxy_fix import ProxyFix

from ..celery_app import celery_init_app
from ..config import load_config
from .admin.dashboard import init_admin
from .services.graceful import install_signal_handlers
from .services.engagement import initialize_database, record_event
from .services.metrics import (
    active_users_gauge,
    error_count,
    request_count,
    request_latency,
    update_uptime,
    visit_counter,
)
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
            "script-src": ["'self'"],
            # Plotly uses runtime style attributes to position its SVG/canvas output.
            "style-src": ["'self'", "'unsafe-inline'"],
            "img-src": ["'self'", "data:", "blob:"],
            "font-src": ["'self'"],
            "connect-src": ["'self'"],
            "worker-src": ["'self'", "blob:"],
            "frame-src": ["'self'", "blob:"],
            "object-src": ["'self'", "blob:"],
        },
        content_security_policy_nonce_in=["script-src"],
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
    app.config["ENGAGEMENT_DATABASE"] = cfg.feedback_settings.get(
        "database_path", "data/engagement.sqlite3"
    )
    app.config["ANALYTICS_ENABLED"] = bool(cfg.analytics_settings.get("enabled", True))
    app.config["EMAIL_SETTINGS"] = cfg.email_settings
    app.secret_key = cfg.secret_key or os.urandom(24)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)
    celery_init_app(app)
    initialize_database(app.config["ENGAGEMENT_DATABASE"])

    # Metrics instrumentation
    @app.before_request
    def _before_request() -> None:
        g.start_time = time.time()
        candidate = request.cookies.get("ml_session", "")
        g.analytics_session_id = (
            candidate
            if 16 <= len(candidate) <= 80 and candidate.replace("-", "").replace("_", "").isalnum()
            else uuid.uuid4().hex
        )

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
        response.set_cookie(
            "ml_session",
            g.analytics_session_id,
            max_age=8 * 60 * 60,
            httponly=True,
            samesite="Lax",
        )
        if (
            app.config["ANALYTICS_ENABLED"]
            and endpoint not in {"feedback.analytics_event", "main.active_users"}
            and not request.path.startswith("/static/")
        ):
            tool_id = tool_name = None
            if request.path.startswith("/pdf_tools"):
                tool_id, tool_name = "pdf-tools", "PDF Tools"
            elif request.path.startswith("/tabular_ml"):
                tool_id, tool_name = "tabular-ml", "Tabular ML Workbench"
            try:
                record_event(
                    app.config["ENGAGEMENT_DATABASE"],
                    session_id=g.analytics_session_id,
                    user_agent=request.user_agent.string,
                    event_name="request",
                    tool_id=tool_id,
                    tool_name=tool_name,
                    path=request.path[:1000],
                    duration_ms=round(latency * 1000),
                    status_code=response.status_code,
                )
            except Exception:
                logging.getLogger(__name__).warning(
                    "Request analytics could not be stored", exc_info=True
                )
        return response

    # Blueprints
    from pdf_tools_service.app import pdf_tools_bp
    from tabular_ml_service.app import tabular_ml_bp

    from .routes.api import bp as api_bp
    from .routes.download import bp as download_bp
    from .routes.feedback import bp as feedback_bp
    from .routes.main import bp as main_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(feedback_bp)
    # The companion service owns the stable /pdf_tools/* contract.
    app.register_blueprint(pdf_tools_bp)
    # Tabular ML owns the same /tabular_ml/* contract standalone and in the portal.
    app.register_blueprint(tabular_ml_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(download_bp)

    # Admin dashboard
    init_admin(app)

    if startup:
        start_services()

    return app
