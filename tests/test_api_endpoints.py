import pytest
import json
import io

def test_super_resolution_predict_api(client, sample_image):
    """Test /super_resolution endpoint."""
    data = {
        'image': (sample_image, 'test.png')
    }
    response = client.post('/super_resolution',
                           content_type='multipart/form-data',
                           data=data)

    assert response.status_code in (200, 400, 503)  # 400 = bad input, 503 = model down
    json_data = response.get_json()
    assert 'success' in json_data

    if json_data['success']:
        assert 'enhanced_image' in json_data
    else:
        assert 'error' in json_data


def test_ebsd_cleanup_predict_api(client, sample_ebsd_file):
    """Test /ebsd_cleanup endpoint."""
    data = {
        'ebsd_file': (sample_ebsd_file, 'test.ang')
    }
    response = client.post('/ebsd_cleanup',
                           content_type='multipart/form-data',
                           data=data)

    assert response.status_code in (200, 400)
    json_data = response.get_json()
    assert 'success' in json_data

    if json_data['success']:
        assert 'original_map' in json_data
        assert 'enhanced_map' in json_data
    else:
        assert 'error' in json_data


def test_models_status_api(client):
    """Test /api/check_model_status endpoint."""
    response = client.get('/api/check_model_status')
    assert response.status_code == 200
    json_data = response.get_json()
    assert 'running' in json_data
    assert isinstance(json_data['running'], bool)


def test_invalid_api_request(client):
    """Test invalid POST to /super_resolution without a file."""
    response = client.post('/super_resolution')
    assert response.status_code in (400, 503)
    json_data = response.get_json()
    assert json_data['success'] is False
    assert 'error' in json_data
