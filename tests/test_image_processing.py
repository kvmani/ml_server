import unittest
import io
import sys
import os

# Dynamically add the microstructure-analysis-flask directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../microstructure-analysis-flask')))

# Now import app after modifying sys.path
from app import app  

class ImageProcessingTests(unittest.TestCase):

    def setUp(self):
        """Set up test client before each test"""
        app.config['TESTING'] = True
        self.client = app.test_client()

    def tearDown(self):
        """Clean up after each test"""
        pass

    def test_image_upload(self):
        """Test image upload and processing"""
        test_image_path = os.path.join(os.path.dirname(__file__), "test_image.png")

        if not os.path.exists(test_image_path):
            self.fail(f"Test image file not found: {test_image_path}")

        with open(test_image_path, "rb") as img:
            response = self.client.post(
                '/super_resolution/process',
                content_type='multipart/form-data',
                data={'image': (img, "test_image.png")}
            )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'image/png')

if __name__ == "__main__":
    unittest.main()
