"""Command-line entry point for the portal service."""

from __future__ import annotations

import argparse
import getpass
import sys

from .app.server import create_app
from .config import load_config


def main() -> None:
    """Run the portal with a production WSGI server by default."""
    parser = argparse.ArgumentParser(description="ML Server")
    parser.add_argument("--no-autostart", action="store_true", help="Disable model autostart")
    parser.add_argument("--host", help="Override the configured bind host")
    parser.add_argument("--port", type=int, help="Override the configured bind port")
    parser.add_argument("--debug", action="store_true", help="Use Flask's development server")
    parser.add_argument(
        "--hash-admin-password",
        action="store_true",
        help=(
            "Prompt for an admin dashboard password and print its hash, for "
            "ML_SERVER_ADMIN_PASSWORD_HASH. Nothing is started or written."
        ),
    )
    args = parser.parse_args()

    if args.hash_admin_password:
        _print_admin_password_hash()
        return

    cfg = load_config()
    app = create_app(startup=not args.no_autostart)
    host = args.host or cfg.host
    port = args.port or cfg.port
    if args.debug:
        app.run(host=host, port=port, debug=True)
        return

    from waitress import serve

    serve(app, host=host, port=port, threads=4)


def _print_admin_password_hash() -> None:
    """Turn a typed password into a hash the operator can paste into a unit file.

    The password is read from a prompt rather than an argument so it never
    reaches the shell history or the process list, and only the hash is printed.
    """
    from werkzeug.security import generate_password_hash

    password = getpass.getpass("New admin password: ")
    if len(password) < 12:
        print("Choose a password of at least 12 characters.", file=sys.stderr)
        raise SystemExit(1)
    if password != getpass.getpass("Repeat the password: "):
        print("The two entries did not match.", file=sys.stderr)
        raise SystemExit(1)
    print()
    print("Add this to the service environment (not to git):")
    print()
    digest = generate_password_hash(password, method="pbkdf2:sha256:600000")
    print(f"ML_SERVER_ADMIN_PASSWORD_HASH={digest}")


if __name__ == "__main__":  # pragma: no cover - module execution entry point
    main()
