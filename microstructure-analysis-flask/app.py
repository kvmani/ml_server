from flask import Flask, redirect, url_for
import yaml
import os
import logging
from apps.super_resolution import super_resolution_bp

def load_config(config_path='config.yml'):
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)

def create_app():
    app = Flask(__name__)
    
    # Load configuration
    if os.path.exists('config.yml'):
        config = load_config()
        app.config.update(config.get('app', {}))
    
    # Set secret key for session management
    app.secret_key = os.environ.get('SECRET_KEY', 'dev')
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s: %(message)s'
    )
    
    # Register blueprints
    app.register_blueprint(super_resolution_bp, url_prefix='/super_resolution')
    
    # Add root route to redirect to super_resolution
    @app.route('/')
    def index():
        return redirect(url_for('super_resolution.index'))
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(
        host=app.config.get('host', '127.0.0.1'),
        port=app.config.get('port', 5000),
        debug=app.config.get('debug', True)
    ) 