# testss/conftest.py
import sys
import os
import pytest

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from microstructure_server import create_app
from config import Config

@pytest.fixture
def client():
    os.environ['APP_LOGGING__LOG_DIR'] = os.path.join('tmp', 'test_logs')
    Config._instance = None
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client
