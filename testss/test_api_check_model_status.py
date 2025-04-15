# tests/test_api_check_model_status.py
def test_api_check_model_status(client):
    response = client.get('/api/check_model_status')
    assert response.status_code == 200
    assert 'running' in response.get_json()
