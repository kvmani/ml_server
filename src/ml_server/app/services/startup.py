"""Helpers for launching local model services during development."""

import logging
import os
import socket
import subprocess
import time
from pathlib import Path
from typing import Optional

from ...config import Config

_LOG = logging.getLogger(__name__)


def _is_port_open(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(1)
        return sock.connect_ex((host, port)) == 0


def launch_service(
    script: str, port: int, retries: int = 3
) -> Optional[subprocess.Popen]:
    """Launch a Python service script and wait for its port to become available."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    stdout = open(log_dir / f"{Path(script).stem}.out.log", "a")
    stderr = open(log_dir / f"{Path(script).stem}.err.log", "a")

    for attempt in range(retries):
        process = subprocess.Popen(
            [
                "python",
                script,
            ],
            stdout=stdout,
            stderr=stderr,
        )
        _LOG.info("Starting %s on port %s (pid=%s)", script, port, process.pid)
        for _ in range(10):
            if _is_port_open(port):
                _LOG.info("%s ready", script)
                return process
            if process.poll() is not None:
                break
            time.sleep(1)
        _LOG.warning("%s failed to start (attempt %s)", script, attempt + 1)
    return None


def start_services() -> None:
    config = Config()
    services = [
        (
            os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "scripts",
                "fake_ml_model_server.py",
            ),
            config.super_resolution_settings.get("ml_model", {}).get("port", 5002),
        ),
        (
            os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "scripts",
                "fake_ebsd_model.py",
            ),
            config.ebsd_cleanup_settings.get("ml_model", {}).get("port", 5003),
        ),
    ]
    for script, port in services:
        if not _is_port_open(port):
            launch_service(script, port)
