import pytest
import io  # Add this import at the top

def test_missing_file_error(client):
    """Test error handling for missing files."""
    response = client.post('/super_resolution')
    assert response.status_code == 400
    json_data = response.get_json()
    assert 'error' in json_data

def test_invalid_file_type_error(client):
    """Test error handling for invalid file types."""
    data = {
        'image': (io.BytesIO(b'invalid'), 'test.txt')
    }
    response = client.post('/super_resolution',
                         content_type='multipart/form-data',
                         data=data)
    assert response.status_code == 400

def test_processing_error_handling(client, sample_image):
    """Test error handling during processing."""
    # Corrupt the image data to trigger processing error
    sample_image.seek(0)
    sample_image.write(b'corrupt data')
    sample_image.seek(0)
    
    response = client.post('/super_resolution',
                         data={'image': (sample_image, 'test.png')})
    assert response.status_code == 500
    data = response.get_json()
    assert 'error' in data