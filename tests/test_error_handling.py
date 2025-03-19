import unittest
import io
from app import app

class ErrorHandlingTests(unittest.TestCase):

    def setUp(self):
        """Set up test client before each test"""
        app.config['TESTING'] = True
        self.client = app.test_client()

    def test_invalid_file_upload(self):
        """Test non-image file upload"""
        response = self.client.post(
            '/super_resolution/process',
            content_type='multipart/form-data',
            data={'image': (io.BytesIO(b"Hello"), "test.txt")}
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn(b'Invalid file type', response.data)

if __name__ == "__main__":
    unittest.main()
