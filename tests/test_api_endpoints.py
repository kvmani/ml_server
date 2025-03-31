import pytest
import json
import io

def test_super_resolution_predict_api(client, sample_image):
    """Test super resolution prediction API."""
    data = {
        'image': (sample_image, 'test.png')
    }
    response = client.post('/api/v1/super_resolution/predict',
                         content_type='multipart/form-data',
                         data=data)
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['success'] == True
    assert 'enhanced_image' in json_data
    assert 'metadata' in json_data

def test_ebsd_cleanup_predict_api(client, sample_ebsd_file):
    """Test EBSD cleanup prediction API."""
    data = {
        'ebsd_file': (sample_ebsd_file, 'test.ang')
    }
    response = client.post('/api/v1/ebsd/cleanup/predict',
                         content_type='multipart/form-data',
                         data=data)
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['success'] == True
    assert 'processed_data' in json_data

def test_models_status_api(client):
    """Test models status API."""
    response = client.get('/api/v1/models/status')
    assert response.status_code == 200
    json_data = response.get_json()
    assert 'super_resolution_model' in json_data
    assert 'ebsd_cleanup_model' in json_data

def test_invalid_api_request(client):
    """Test invalid API request handling."""
    response = client.post('/api/v1/super_resolution/predict')
    assert response.status_code == 400
    json_data = response.get_json()
    assert 'error' in json_data