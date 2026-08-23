# Conftest for tests
import os
import sys

import pytest

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ml_server.app import server as ml_server_app  # noqa: E402


@pytest.fixture(autouse=True)
def disable_signals(monkeypatch):
    monkeypatch.setattr(ml_server_app, "install_signal_handlers", lambda: None)
    monkeypatch.setattr(ml_server_app, "start_services", lambda: None)


@pytest.fixture
def client(tmp_path):
    os.environ["APP_LOGGING__LOG_DIR"] = os.path.join("tmp", "test_logs")
    app = ml_server_app.create_app(startup=False)
    app.config["TESTING"] = True
    app.config["ENGAGEMENT_DATABASE"] = str(tmp_path / "engagement.sqlite3")
    from ml_server.app.services.engagement import initialize_database

    initialize_database(app.config["ENGAGEMENT_DATABASE"])
    with app.test_client() as client:
        yield client
