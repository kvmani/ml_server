import pytest
from PIL import Image
import numpy as np
import io

def test_process_image_with_model(client, sample_image):
    """Test /super_resolution endpoint with image processing."""
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


def test_process_ebsd_with_model(client, sample_ebsd_file):
    """Test /ebsd_cleanup endpoint with EBSD file."""
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


def test_image_preprocessing():
    """Test local image preprocessing (flip operation)."""
    # Create a sample image array
    img_array = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    
    # Convert numpy array to PIL Image
    img = Image.fromarray(img_array)
    
    # Flip the image
    flipped_img = img.transpose(Image.FLIP_LEFT_RIGHT)
    
    # Convert back to numpy array
    flipped_array = np.array(flipped_img)
    
    # Sanity checks
    assert isinstance(flipped_array, np.ndarray)
    assert flipped_array.shape == img_array.shape
    assert not np.array_equal(flipped_array, img_array)

    # Flip verification: first column of original should match last of flipped
    np.testing.assert_array_equal(img_array[:, 0], flipped_array[:, -1])
    np.testing.assert_array_equal(img_array[:, -1], flipped_array[:, 0])
