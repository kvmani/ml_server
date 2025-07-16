# tests/test_hydride_segmentation.py

def test_hydride_segmentation_get(client):
    response = client.get('/hydride_segmentation')
    assert response.status_code == 200
    assert b'<html' in response.data


def test_hydride_segmentation_post_no_file(client):
    response = client.post('/hydride_segmentation', data={})
    assert response.status_code == 400
    assert b'No image uploaded' in response.data
