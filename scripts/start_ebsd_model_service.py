import logging
import os
import subprocess
import time

import requests

from ml_server.config import Config


def start_ebsd_model_service() -> bool:
    """Start the EBSD model service if it is not already running."""
    config = Config()
    health_url = config.ebsd_cleanup_settings.get("ml_model", {}).get("health_url")
    try:
        response = requests.get(health_url, timeout=3)
        if response.status_code == 200:
            logging.info("EBSD model service is already running")
            return True
    except requests.exceptions.RequestException:
        logging.info("EBSD model service not found, attempting to start it...")

    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        ebsd_server_path = os.path.join(
            os.path.dirname(current_dir), "scripts", "fake_ebsd_model.py"
        )
        print(f"Starting EBSD model server from: {ebsd_server_path}")
        if os.name == "nt":
            subprocess.Popen(["start", "cmd", "/k", "python", ebsd_server_path], shell=True)
        else:
            subprocess.Popen(
                ["python", ebsd_server_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
        max_attempts = 10
        for attempt in range(max_attempts):
            try:
                response = requests.get(health_url)
                if response.status_code == 200:
                    print("EBSD model server started successfully!")
                    return True
            except requests.exceptions.RequestException:
                time.sleep(1)
            print(
                f"Waiting for EBSD model server to start... (Attempt {attempt + 1}/{max_attempts})"
            )
        print("Failed to start EBSD model server")
        return False
    except Exception as e:
        print(f"Error starting EBSD model server: {e}")
        return False


if __name__ == "__main__":
    start_ebsd_model_service()
