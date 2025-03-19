import unittest
import io
#from app import app
from microstructure-analysis-flask.app import app


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
        with open("test_image.png", "rb") as img:
            response = self.client.post(
                '/super_resolution/process',
                content_type='multipart/form-data',
                data={'image': (img, "test_image.png")}
            )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'image/png')

if __name__ == "__main__":
    unittest.main()
