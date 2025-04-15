# tests/test_download_processed_data.py
import os

def test_download_processed_data_missing_file(client):
    # Ensure the file doesn't exist
    if os.path.exists("tmp/enhanced_ebsd_map.png"):
        os.remove("tmp/enhanced_ebsd_map.png")

    response = client.get('/download_processed_data')
    assert response.status_code == 404
    assert b'Processed file not found' in response.data
