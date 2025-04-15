# tests/test_super_resolution.py
import io

def test_super_resolution_get(client):
    response = client.get('/super_resolution')
    assert response.status_code == 200
    assert b'<html' in response.data

def test_super_resolution_post_no_file(client):
    response = client.post('/super_resolution', data={})
    assert response.status_code == 400
    assert b'No image uploaded' in response.data
