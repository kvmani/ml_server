# tests/test_home_route.py
def test_home_route(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"<html" in response.data
    assert b"Search by name, category, or capability" in response.data
    assert response.data.count(b"data-tool-card") == 7
    assert b"Tabular ML Workbench" in response.data
    assert b"active-user-count" in response.data
    assert b"hero-visual" not in response.data
    assert b"LOCAL \xc2\xb7 VERIFIED" not in response.data
    assert b'data-feedback-kind="feedback"' in response.data
    assert b'data-feedback-kind="feature_request"' in response.data
    assert b'id="feedback-form"' in response.data
    assert response.data.count(b"Scientific help") == 7
    assert b"An AI-assisted advanced segmentation tool" in response.data


def test_every_catalog_tool_has_a_scientific_help_page(client):
    catalog = client.get("/api/catalog").get_json()["tools"]
    for tool in catalog:
        response = client.get(f"/tools/{tool['id']}/help")
        assert response.status_code == 200
        assert tool["name"].encode() in response.data
        assert b"MATHEMATICAL CORE" in response.data
        assert b"CRITICAL INPUTS" in response.data


def test_unknown_tool_help_returns_404(client):
    assert client.get("/tools/not-a-tool/help").status_code == 404


def test_active_user_count_is_anonymized_and_at_least_one(client):
    response = client.get("/api/active-users")
    payload = response.get_json()
    assert response.status_code == 200
    assert payload["status"] == "ok"
    assert payload["active_users"] >= 1


def test_online_annotator_card_and_help(client):
    catalog = {tool["id"]: tool for tool in client.get("/api/catalog").get_json()["tools"]}
    annotator = catalog["online-annotator"]
    assert annotator["category"] == "Microstructure"
    assert annotator["icon"] == "annotator-mark.svg"
    help_page = client.get("/tools/online-annotator/help")
    assert help_page.status_code == 200
    assert b"help/online-annotator-workflow.svg" in help_page.data
    assert b"Otsu threshold" in help_page.data
    assert b"Classes and guidelines" in help_page.data  # critical-inputs section is populated
    manual = annotator["href"].rstrip("/").encode() + b"/help"
    assert manual in help_page.data  # links the tool's own manual
