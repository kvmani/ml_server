from ml_server.config import load_config


def test_load_config():
    cfg = load_config()
    assert isinstance(cfg.port, int)
    assert all("cleanup" not in key.lower() for key in cfg.config)
