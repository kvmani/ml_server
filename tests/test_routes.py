import pytest
from flask import url_for

def test_home_page(client):
    """Test the home page route."""
    response = client.get('/')
    assert response.status_code == 200

def test_super_resolution_page(client):
    """Test the super resolution page route."""
    response = client.get('/super_resolution')
    assert response.status_code == 200
    assert b'Super Resolution' in response.data

def test_ebsd_cleanup_page(client):
    """Test the EBSD cleanup page route."""
    response = client.get('/ebsd_cleanup')
    assert response.status_code == 200
    assert b'EBSD Clean-Up' in response.data

def test_invalid_route(client):
    """Test handling of invalid routes."""
    response = client.get('/nonexistent')
    assert response.status_code == 404