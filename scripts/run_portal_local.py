"""Run the portal without model-service autostart for the local platform stack."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ml_server.app.server import create_app  # noqa: E402


if __name__ == "__main__":
    create_app(startup=False).run(
        host="127.0.0.1", port=5000, debug=False, use_reloader=False
    )
