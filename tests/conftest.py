# testss/conftest.py
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from microstructure_server import create_app


@pytest.fixture
def client():
    os.environ["APP_LOGGING__LOG_DIR"] = os.path.join("tmp", "test_logs")
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client
