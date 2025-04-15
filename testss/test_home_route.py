# tests/test_home_route.py
def test_home_route(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'<html' in response.data
