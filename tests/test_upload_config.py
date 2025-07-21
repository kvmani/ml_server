def test_upload_config(client):
    response = client.get("/api/upload_config")
    assert response.status_code == 200
    data = response.get_json()
    assert "max_size" in data
    assert data["max_size"] > 0
