import logging
import os
import subprocess
import time

import requests

from config import Config


def start_ml_model_service() -> bool:
    """Start the ML model service if it is not already running."""
    config = Config()
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
        print(f"Starting ML model server from: {ml_server_path}")
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
                    print("ML model server started successfully!")
                    return True
            except requests.exceptions.RequestException:
                time.sleep(1)
            print(f"Waiting for ML model server to start... (Attempt {attempt + 1}/{max_attempts})")
        print("Failed to start ML model server")
        return False
    except Exception as e:
        print(f"Error starting ML model server: {e}")
        return False


if __name__ == "__main__":
    start_ml_model_service()
