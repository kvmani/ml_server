# tests/test_submit_feedback.py
import json

def test_submit_feedback_success(client):
    data = {
        'name': 'Test User',
        'email': 'test@example.com',
        'rating': 5,
        'feedback': 'Great app!'
    }
    response = client.post('/submit_feedback', data=data)
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert response_data['success'] is True

def test_submit_feedback_missing_fields(client):
    data = {
        'name': 'Test User',
        'email': '',
        'rating': 5,
        'feedback': ''
    }
    response = client.post('/submit_feedback', data=data)
    assert response.status_code == 400
    assert b'All fields are required' in response.data
