from ml_server.config import load_config


def test_load_config():
    cfg = load_config()
    assert isinstance(cfg.port, int)
    assert all("cleanup" not in key.lower() for key in cfg.config)
    assert not cfg.secret_key.startswith("__SET_")
    assert not cfg.admin_token.startswith("__SET_")
