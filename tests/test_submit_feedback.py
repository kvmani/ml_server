# tests/test_submit_feedback.py
import json
import os
from microstructure_server.routes import feedback as fb

def test_submit_feedback_success(client, monkeypatch):
    tmp_file = os.path.join('tmp', 'test_feedback.json')
    monkeypatch.setattr(fb, 'FEEDBACK_FILE', tmp_file)
    with open(tmp_file, 'w') as f:
        json.dump({'feedback': []}, f)
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

def test_submit_feedback_missing_fields(client, monkeypatch):
    monkeypatch.setattr(fb, 'FEEDBACK_FILE', os.path.join('tmp', 'test_feedback.json'))
    data = {
        'name': 'Test User',
        'email': '',
        'rating': 5,
        'feedback': ''
    }
    response = client.post('/submit_feedback', data=data)
    assert response.status_code == 400
    assert b'All fields are required' in response.data
