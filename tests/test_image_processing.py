import pytest
from PIL import Image
import numpy as np
import io

def test_process_image_with_model(client, sample_image):
    """Test image processing function."""
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

def test_process_ebsd_with_model(client, sample_ebsd_file):
    """Test EBSD processing function."""
    data = {
        'ebsd_file': (sample_ebsd_file, 'test.ang')
    }
    response = client.post('/ebsd_cleanup',
                         content_type='multipart/form-data',
                         data=data)
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['success'] == True

def test_image_preprocessing():
    """Test image preprocessing function."""
    # Create a sample image array
    img_array = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    
    # Convert numpy array to PIL Image for processing
    img = Image.fromarray(img_array)
    
    # Flip the image using PIL
    flipped_img = img.transpose(Image.FLIP_LEFT_RIGHT)
    
    # Convert back to numpy array
    flipped_array = np.array(flipped_img)
    
    # Verify the processing
    assert isinstance(flipped_array, np.ndarray)
    assert flipped_array.shape == img_array.shape
    assert not np.array_equal(flipped_array, img_array)  # Arrays should be different after flipping
    
    # Verify the flip operation worked correctly
    # The first column of the original should equal the last column of the flipped image
    np.testing.assert_array_equal(img_array[:, 0], flipped_array[:, -1])