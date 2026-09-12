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

from .. import __version__
from ..catalog import resolve_service
from ..celery_app import celery_init_app
from ..config import load_config
from .admin.dashboard import init_admin
from .services.engagement import browser_family, client_digest, initialize_database, record_event
from .services.graceful import install_signal_handlers
from .services.live_activity import live_activity
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
    install_signal_handlers()
    logging.getLogger(__name__).info("Server starting")
    app.start_time = time.time()
    cfg = load_config()

    # Whether this portal is an HTTPS site decides three things at once, so it is
    # read once and handed to all three rather than re-derived in each place.
    #
    # Getting this wrong is what broke admin logins in production. Talisman
    # defaults `session_cookie_secure` to True and -- this is the part that made
    # it so hard to see -- re-applies it from a before_request hook on EVERY
    # request, so assigning app.config["SESSION_COOKIE_SECURE"] afterwards had no
    # effect whatsoever: the value was correct at startup and flipped back to
    # True before the first response was built. On the plain-HTTP intranet the
    # browser then discarded the Secure session cookie, the login form's CSRF
    # token had nowhere to live, and the POST came back "This form expired"
    # every single time. Every Talisman option below is therefore explicit.
    ssl_enabled = cfg.ssl_enabled
    Talisman(
        app,
        force_https=ssl_enabled,
        strict_transport_security=ssl_enabled,
        session_cookie_secure=ssl_enabled,
        session_cookie_http_only=True,
        session_cookie_samesite="Lax",
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
    )
    if cfg.admin_token:
        app.config["ADMIN_TOKEN"] = cfg.admin_token
    app.config["PORTAL_VERSION"] = __version__
    app.config["MAIN_ICON_SIZE"] = cfg.main_icon_size
    app.config["TOOLS_ICONS_SIZE"] = cfg.tools_icons_size
    app.config["ENGAGEMENT_DATABASE"] = cfg.feedback_settings.get(
        "database_path", "data/engagement.sqlite3"
    )
    app.config["ANALYTICS_ENABLED"] = bool(cfg.analytics_settings.get("enabled", True))
    app.config["ANALYTICS_RETENTION_MONTHS"] = int(
        cfg.analytics_settings.get("retention_months", 24)
    )
    app.config["EMAIL_SETTINGS"] = cfg.email_settings
    # The dashboard password. A hash is preferred; the legacy admin token still
    # works as a password so an upgrade does not lock an operator out.
    app.config["ADMIN_PASSWORD_HASH"] = cfg.admin_password_hash
    app.config["ADMIN_PASSWORD"] = cfg.admin_password
    # Never os.urandom() here. Production runs `gunicorn --workers 2`, so a
    # per-process key means the worker that verifies the login POST cannot read
    # the session the worker that rendered the form wrote. resolved_secret_key()
    # returns the configured key, or one generated once and kept beside the
    # configuration in shared/, which every worker and every restart then share.
    app.secret_key = cfg.resolved_secret_key()
    app.config["SSL_ENABLED"] = ssl_enabled
    app.config["CSRF_ENABLED"] = cfg.csrf_enabled
    app.config["CONFIG_PATH"] = str(cfg.config_path)
    app.config["CONFIG_SCHEMA_VERSION"] = cfg.schema_version
    # The admin session rides in this cookie. SameSite=Lax is what stops another
    # page from driving a signed-in administrator's browser into a state-changing
    # admin request; it is a browser default today, but defaults are not a policy.
    #
    # These three restate what Talisman was told above. They are not redundant:
    # they are what a developer reads when asking "what is the cookie policy?",
    # and a test asserts that the header on the wire agrees with them.
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_SECURE"] = ssl_enabled
    logging.getLogger(__name__).info(
        "Session policy: scheme=%s secure_cookie=%s samesite=Lax csrf=%s "
        "secret_key=%s trusted_proxies=%d",
        "https" if ssl_enabled else "http",
        ssl_enabled,
        cfg.csrf_enabled,
        "configured" if cfg.secret_key else "generated-and-persisted",
        cfg.trusted_proxy_count,
    )
    # X-Forwarded-* is believed only when a proxy is actually in front of the
    # portal. In the office deployment gunicorn is reached directly, so trusting
    # those headers would let any client on the intranet claim someone else's
    # address and walk past the admin login lockout.
    if cfg.trusted_proxy_count:
        app.wsgi_app = ProxyFix(
            app.wsgi_app,
            x_for=cfg.trusted_proxy_count,
            x_proto=cfg.trusted_proxy_count,
        )
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
        # An earlier before_request can short-circuit the request before ours
        # runs -- Talisman's HTTPS redirect does exactly that -- and then none
        # of the analytics state exists. Reading it defensively is the
        # difference between a redirect and a 500 on every plain-HTTP request
        # to an HTTPS deployment.
        if "analytics_session_id" not in g:
            return response
        latency = time.time() - g.get("start_time", time.time())
        endpoint = request.endpoint or "unknown"
        visit_counter.labels(endpoint=endpoint).inc()
        request_latency.labels(endpoint=endpoint).observe(latency)
        request_count.labels(endpoint=endpoint, status=response.status_code).inc()
        if response.status_code >= 400:
            etype = "5xx" if response.status_code >= 500 else "4xx"
            error_count.labels(endpoint=endpoint, type=etype).inc()
        # Who is using what, right now. Held in memory only; see live_activity.
        tool_id, tool_name = resolve_service(request.path)
        family = browser_family(request.user_agent.string)
        if not request.path.startswith("/static/"):
            live_activity.record(
                ip=request.remote_addr,
                service_name=tool_name,
                path=request.path,
                status_code=response.status_code,
                duration_ms=latency * 1000,
                browser=family,
            )
        active_users_gauge.set(live_activity.active_client_count())
        update_uptime(app.start_time)
        response.set_cookie(
            "ml_session",
            g.analytics_session_id,
            max_age=8 * 60 * 60,
            httponly=True,
            samesite="Lax",
        )
        # The console polls itself every few seconds; persisting that would
        # swamp the usage figures it exists to report. Admin traffic still shows
        # up in the live view, which expires on its own.
        if (
            app.config["ANALYTICS_ENABLED"]
            and endpoint not in {"feedback.analytics_event", "main.active_users"}
            and not request.path.startswith("/static/")
            and tool_name != "Admin"
        ):
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
                    client_hash=client_digest(request.remote_addr, app.secret_key),
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

    # Admin dashboard. Registered last so its /admin/* rules are unambiguous.
    init_admin(app)

    if startup:
        start_services()

    return app
