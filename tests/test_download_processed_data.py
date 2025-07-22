# tests/test_download_processed_data.py
import os

from ml_server.config import Config


def test_download_processed_data_missing_file(client):
    # Ensure the file doesn't exist
    path = Config().processed_data_path
    if os.path.exists(path):
        os.remove(path)

    response = client.get("/download_processed_data")
    assert response.status_code == 404
    assert b"Processed file not found" in response.data
