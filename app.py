from __future__ import annotations

import argparse

from config import load_config
from microstructure_server import create_app


def main() -> None:
    parser = argparse.ArgumentParser(description="Microstructure server")
    parser.add_argument("--no-autostart", action="store_true", help="Disable model autostart")
    args = parser.parse_args()

    cfg = load_config()
    app = create_app(startup=not args.no_autostart)
    app.run(host=cfg.host, port=cfg.port, debug=cfg.debug)


if __name__ == "__main__":
    main()
