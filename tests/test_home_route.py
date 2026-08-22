# tests/test_home_route.py
def test_home_route(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"<html" in response.data
    assert b"Search by name, category, or capability" in response.data
    assert response.data.count(b"data-tool-card") == 6
    assert b"Tabular ML Workbench" in response.data
    assert b"active-user-count" in response.data


def test_active_user_count_is_anonymized_and_at_least_one(client):
    response = client.get("/api/active-users")
    payload = response.get_json()
    assert response.status_code == 200
    assert payload["status"] == "ok"
    assert payload["active_users"] >= 1
