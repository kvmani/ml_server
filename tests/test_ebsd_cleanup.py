# tests/test_ebsd_cleanup.py
import io

def test_ebsd_cleanup_get(client):
    response = client.get('/ebsd_cleanup')
    assert response.status_code == 200
    assert b'<html' in response.data

def test_ebsd_cleanup_post_no_file(client):
    response = client.post('/ebsd_cleanup', data={})
    assert response.status_code == 400
    assert b'No EBSD file uploaded' in response.data
