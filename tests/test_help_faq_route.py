# tests/test_help_faq_route.py
def test_help_faq_route(client):
    response = client.get("/help/faq")
    assert response.status_code == 200
    assert b"<html" in response.data
    assert response.data.count(b"/help\"") >= 6
    assert b"Scientific guides" in response.data


def test_legacy_help_faq_route_remains_available(client):
    assert client.get("/help_faq").status_code == 200
