from unittest.mock import Mock

from ml_server.tasks import ebsd_cleanup_task


class DummyConfig:
    def __init__(self):
        self.ebsd_cleanup_settings = {"ml_model": {"url": "http://model", "timeout": 1}}


def test_ebsd_cleanup_task_returns_json(monkeypatch, tmp_path):
    monkeypatch.setattr("ml_server.tasks.Config", lambda: DummyConfig())
    monkeypatch.setattr(
        "ml_server.tasks.requests.post",
        lambda *a, **k: Mock(status_code=200, json=lambda: {"ok": True}),
    )
    file_path = tmp_path / "file.ang"
    file_path.write_bytes(b"data")
    result = ebsd_cleanup_task.run(str(file_path))
    assert result == {"ok": True}
