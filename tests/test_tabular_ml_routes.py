def test_tabular_ml_is_mounted_with_same_origin_assets(client):
    response = client.get("/tabular_ml/")

    assert response.status_code == 200
    assert b"Tabular ML Workbench" in response.data
    assert b"/tabular_ml/assets/ui/app.js" in response.data


def test_tabular_ml_health_and_dataset_catalog(client):
    health = client.get("/tabular_ml/api/v1/health")
    catalog = client.get("/tabular_ml/api/v1/datasets")

    assert health.status_code == 200
    assert health.get_json()["data"]["status"] == "ok"
    datasets = catalog.get_json()["data"]["datasets"]
    assert len(datasets) >= 6
    assert {"classification", "regression"} <= {item["task"] for item in datasets}


def test_tabular_ml_builtin_load_uses_portal_contract(client):
    response = client.post("/tabular_ml/api/v1/datasets/palmer_penguins/load")

    assert response.status_code == 201
    payload = response.get_json()["data"]
    assert payload["dataset"]["rows"] == 344
    assert payload["profile"]["target_candidates"][0]["column"] == "species"
