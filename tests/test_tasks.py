import os
import tempfile
from unittest.mock import Mock

import pytest

from ml_server.tasks import ebsd_cleanup_task


class DummyConfig:
    def __init__(self):
        self.ebsd_cleanup_settings = {"ml_model": {"url": "http://model", "timeout": 1}}


def test_ebsd_cleanup_task_success(monkeypatch):
    monkeypatch.setattr("ml_server.tasks.Config", lambda: DummyConfig())
    monkeypatch.setattr(
        "ml_server.tasks.requests.post",
        lambda *a, **k: Mock(status_code=200, json=lambda: {"ok": True}),
    )
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"data")
    result = ebsd_cleanup_task.run(tmp.name)
    assert result == {"ok": True}
    assert not os.path.exists(tmp.name)


def test_ebsd_cleanup_task_retry(monkeypatch):
    monkeypatch.setattr("ml_server.tasks.Config", lambda: DummyConfig())

    def raise_exc(*_a, **_k):
        raise RuntimeError("fail")

    monkeypatch.setattr("ml_server.tasks.requests.post", raise_exc)
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"data")
    with pytest.raises(RuntimeError):
        ebsd_cleanup_task.run(tmp.name)
