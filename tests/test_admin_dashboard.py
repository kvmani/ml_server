from ml_server.app.server import create_app


def test_admin_dashboard_access():
    app = create_app(startup=False)
    app.config["TESTING"] = True
    app.config["ADMIN_TOKEN"] = "secret"
    with app.test_client() as client:
        resp = client.get("/admin?token=secret", follow_redirects=True)
        assert resp.status_code == 200

