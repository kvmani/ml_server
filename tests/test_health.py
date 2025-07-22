from ml_server.app.microstructure_server import create_app


def test_health_endpoint():
    app = create_app(startup=False)
    app.config["TESTING"] = True
    with app.test_client() as client:
        resp = client.get("/health")
        assert resp.status_code == 200
