import pytest
from werkzeug.datastructures import FileStorage
import io  # Add this import at the top

def test_super_resolution_upload(client, sample_image):
    """Test image upload for super resolution."""
    data = {
        'image': (sample_image, 'test.png')
    }
    response = client.post('/super_resolution', 
                         content_type='multipart/form-data',
                         data=data)
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['success'] == True
    assert 'original_image' in json_data
    assert 'enhanced_image' in json_data

def test_ebsd_cleanup_upload(client, sample_ebsd_file):
    """Test EBSD file upload."""
    data = {
        'ebsd_file': (sample_ebsd_file, 'test.ang')
    }
    response = client.post('/ebsd_cleanup',
                         content_type='multipart/form-data',
                         data=data)
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['success'] == True

def test_invalid_file_upload(client):
    """Test upload of invalid files."""
    data = {
        'image': (io.BytesIO(b'invalid data'), 'test.txt')
    }
    response = client.post('/super_resolution',
                         content_type='multipart/form-data',
                         data=data)
    assert response.status_code == 400