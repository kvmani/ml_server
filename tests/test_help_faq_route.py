# tests/test_help_faq_route.py
def test_help_faq_route(client):
    response = client.get("/help_faq")
    assert response.status_code == 200
    assert b"<html" in response.data
