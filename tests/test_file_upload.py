import pytest
import io

def test_super_resolution_upload(client, sample_image):
    """Test image upload for super resolution (/super_resolution endpoint)."""
    data = {
        'image': (sample_image, 'test.png')
    }
    response = client.post('/super_resolution', 
                           content_type='multipart/form-data',
                           data=data)

    assert response.status_code in (200, 400, 503)
    json_data = response.get_json()
    assert 'success' in json_data

    if json_data['success']:
        assert 'enhanced_image' in json_data
    else:
        assert 'error' in json_data


def test_ebsd_cleanup_upload(client, sample_ebsd_file):
    """Test EBSD file upload and cleanup simulation (/ebsd_cleanup endpoint)."""
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


def test_invalid_file_upload(client):
    """Test upload of unsupported file type (e.g., .txt) to /super_resolution."""
    data = {
        'image': (io.BytesIO(b'invalid data'), 'test.txt')  # .txt is not allowed
    }
    response = client.post('/super_resolution',
                           content_type='multipart/form-data',
                           data=data)

    assert response.status_code == 400
    json_data = response.get_json()
    assert json_data['success'] is False
    assert 'error' in json_data
