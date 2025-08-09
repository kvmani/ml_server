from __future__ import annotations

import argparse

from ml_server.app.server import create_app
from ml_server.config import load_config


def main() -> None:
    """Command line entrypoint for starting the Flask development server."""
    parser = argparse.ArgumentParser(description="ML Server")
    parser.add_argument("--no-autostart", action="store_true", help="Disable model autostart")
    args = parser.parse_args()

    cfg = load_config()
    app = create_app(startup=not args.no_autostart)
    app.run(host=cfg.host, port=cfg.port, debug=True)
    #app.run(host=cfg.host, port=cfg.port, debug=cfg.debug)


if __name__ == "__main__":
    main()
