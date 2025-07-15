from flask import Flask
import os
from config import Config
from .services.startup import start_services


def create_app(startup: bool = False) -> Flask:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    app = Flask(
        'microstructure_server',
        template_folder=os.path.join(base_dir, '..', 'templates'),
        static_folder=os.path.join(base_dir, '..', 'static'),
    )
    app.secret_key = os.urandom(24)
    config = Config()

    # Register blueprints
    from .routes.main import bp as main_bp
    from .routes.feedback import bp as feedback_bp
    from .routes.super_resolution import bp as super_res_bp
    from .routes.ebsd_cleanup import bp as ebsd_bp
    from .routes.api import bp as api_bp
    from .routes.download import bp as download_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(feedback_bp)
    app.register_blueprint(super_res_bp)
    app.register_blueprint(ebsd_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(download_bp)

    if startup:
        start_services()

    return app
