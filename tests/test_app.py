import unittest
import sys
import os

# Dynamically add the microstructure-analysis-flask directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../microstructure-analysis-flask')))

# Now import app after modifying sys.path
from app import app  

class BasicTests(unittest.TestCase):

    def setUp(self):
        """Set up test client before each test"""
        app.config['TESTING'] = True
        self.client = app.test_client()

    def tearDown(self):
        """Clean up after each test"""
        pass

    def test_home_page(self):
        """Test if the home page loads correctly"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)  # Should redirect to /super_resolution

if __name__ == "__main__":
    unittest.main()
