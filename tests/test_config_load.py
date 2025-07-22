from ml_server.config import load_config


def test_load_config():
    cfg = load_config()
    assert isinstance(cfg.port, int)
    assert cfg.config.get("super_resolution")
