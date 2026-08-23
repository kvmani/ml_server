"""Command-line entry point for the portal service."""

from __future__ import annotations

import argparse

from .app.server import create_app
from .config import load_config


def main() -> None:
    """Run the portal with a production WSGI server by default."""
    parser = argparse.ArgumentParser(description="ML Server")
    parser.add_argument("--no-autostart", action="store_true", help="Disable model autostart")
    parser.add_argument("--host", help="Override the configured bind host")
    parser.add_argument("--port", type=int, help="Override the configured bind port")
    parser.add_argument("--debug", action="store_true", help="Use Flask's development server")
    args = parser.parse_args()

    cfg = load_config()
    app = create_app(startup=not args.no_autostart)
    host = args.host or cfg.host
    port = args.port or cfg.port
    if args.debug:
        app.run(host=host, port=port, debug=True)
        return

    from waitress import serve

    serve(app, host=host, port=port, threads=4)


if __name__ == "__main__":  # pragma: no cover - module execution entry point
    main()
