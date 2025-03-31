import pytest
from app import app
import io
from PIL import Image
import base64
import os

@pytest.fixture
def client():
    """Create a test client for the app."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def sample_image():
    """Create a sample image for testing."""
    img = Image.new('RGB', (100, 100), color='red')
    img_io = io.BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    return img_io

@pytest.fixture
def sample_ebsd_file():
    """Create a sample EBSD file for testing."""
    content = b"Sample EBSD data content"
    return io.BytesIO(content)

@pytest.fixture
def base64_image():
    """Create a base64 encoded image for testing."""
    img = Image.new('RGB', (100, 100), color='blue')
    img_io = io.BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    return base64.b64encode(img_io.getvalue()).decode()