"""Validate, migrate and describe ``config.intranet.json`` from the shell.

``deploy/update.sh`` runs this against the live shared configuration *before* it
switches the ``current`` symlink, so a config the new release cannot use is
caught while the old release is still serving. It is deliberately importable
without Flask, Celery or any application state: it reads a JSON file and exits.

    python -m ml_server.config_cli check    <path>   # exit 0 when usable as is
    python -m ml_server.config_cli plan     <path>   # what migration would change
    python -m ml_server.config_cli migrate  <path>   # migrate in place, with a backup
    python -m ml_server.config_cli summary  <path>   # secret-free status, --json for machines

Exit codes: 0 success, 1 the configuration is unusable, 2 the migration would
be a guess and a human has to decide, 3 the file is missing or unreadable.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from . import config_schema

EXIT_OK = 0
EXIT_INVALID = 1
EXIT_AMBIGUOUS = 2
EXIT_UNREADABLE = 3


def _stamp() -> str:
    return time.strftime("%Y%m%dT%H%M%S", time.gmtime())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="ml_server.config_cli", description=__doc__.splitlines()[0]
    )
    parser.add_argument(
        "action", choices=("check", "plan", "migrate", "summary"), help="what to do"
    )
    parser.add_argument("path", help="path to config.intranet.json")
    parser.add_argument("--json", action="store_true", help="machine-readable output, for scripts")
    parser.add_argument(
        "--stamp",
        default="",
        help="suffix for the backup file written by 'migrate' (default: UTC timestamp)",
    )
    parser.add_argument(
        "--no-generate-secret-key",
        action="store_true",
        help=(
            "do not mint a 'secret_key' when the file has none. Without a key the "
            "portal generates and persists one itself, which works but leaves the "
            "value out of the file an operator backs up."
        ),
    )
    args = parser.parse_args(argv)

    path = Path(args.path)
    generate = not args.no_generate_secret_key

    try:
        if args.action == "summary":
            document = config_schema.load_document(path)
            report = config_schema.summarize(document)
            report["config_path"] = str(path)
            if args.json:
                print(json.dumps(report, indent=2))
            else:
                for key, value in report.items():
                    print(f"{key}: {value}")
            return EXIT_OK

        if args.action == "check":
            document = config_schema.load_document(path)
            result = config_schema.validate(document)
        else:
            result = config_schema.migrate_file(
                path,
                apply=args.action == "migrate",
                stamp=args.stamp or _stamp(),
                generate_secret_key=generate,
            )
    except config_schema.ConfigError as exc:
        message = str(exc)
        if args.json:
            print(json.dumps({"ok": False, "error": message}, indent=2))
        else:
            print(f"ERROR: {message}", file=sys.stderr)
        # "cannot read" is an environment problem; anything else from migration
        # is a config a human has to resolve. The caller distinguishes them so
        # it can print the right instruction.
        if "cannot read" in message or "not valid JSON" in message:
            return EXIT_UNREADABLE
        return EXIT_AMBIGUOUS

    if args.json:
        print(
            json.dumps(
                {
                    "ok": result.ok,
                    "changed": result.changed,
                    "changes": result.changes,
                    "warnings": result.warnings,
                    "errors": result.errors,
                    "summary": config_schema.summarize(result.document),
                },
                indent=2,
            )
        )
    else:
        for line in config_schema.format_report(path, result, applied=args.action == "migrate"):
            print(line)

    return EXIT_OK if result.ok else EXIT_INVALID


if __name__ == "__main__":  # pragma: no cover - module execution entry point
    raise SystemExit(main())
