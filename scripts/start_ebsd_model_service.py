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
        logging.info("Starting EBSD model server from: %s", ebsd_server_path)
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
                    logging.info("EBSD model server started successfully!")
                    return True
            except requests.exceptions.RequestException:
                time.sleep(1)
            logging.info(
                "Waiting for EBSD model server to start... (Attempt %d/%d)",
                attempt + 1,
                max_attempts,
            )
        logging.error("Failed to start EBSD model server")
        return False
    except Exception as e:
        logging.error("Error starting EBSD model server: %s", e)
        return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    start_ebsd_model_service()
