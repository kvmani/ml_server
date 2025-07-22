import logging
import os
import subprocess
import time
from pathlib import Path
import requests

from ml_server.config import Config


def start_ml_model_service() -> bool:
    """Start the ML model service if it is not already running."""
    cfg_path = r"/opt/ml_server/config.intranet.json"
    print(f"{cfg_path=}")
    config = Config(cfg_path)
    health_url = config.ml_model_health_url
    try:
        response = requests.get(health_url)
        if response.status_code == 200:
            logging.info("ML model service is already running")
            return True
    except requests.exceptions.RequestException:
        logging.info("ML model service not found, attempting to start it...")

    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        ml_server_path = os.path.join(
            os.path.dirname(current_dir), "scripts", "fake_ml_model_server.py"
        )
        logging.info("Starting ML model server from: %s", ml_server_path)
        if os.name == "nt":
            subprocess.Popen(["start", "cmd", "/k", "python", ml_server_path], shell=True)
        else:
            subprocess.Popen(
                ["python", ml_server_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
        max_attempts = 10
        for attempt in range(max_attempts):
            try:
                response = requests.get(health_url)
                if response.status_code == 200:
                    logging.info("ML model server started successfully!")
                    return True
            except requests.exceptions.RequestException:
                time.sleep(1)
            logging.info(
                "Waiting for ML model server to start... (Attempt %d/%d)",
                attempt + 1,
                max_attempts,
            )
        logging.error("Failed to start ML model server")
        return False
    except Exception as e:
        logging.error("Error starting ML model server: %s", e)
        return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    start_ml_model_service()
