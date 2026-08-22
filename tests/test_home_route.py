# tests/test_home_route.py
def test_home_route(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"<html" in response.data
    assert b"Search by name, category, or capability" in response.data
    assert response.data.count(b"data-tool-card") == 6
    assert b"Tabular ML Workbench" in response.data
