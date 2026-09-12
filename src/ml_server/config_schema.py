"""The canonical shape of ``config.intranet.json``, and how to migrate into it.

One file owns the answer to "what is this setting called?". Before this module
the same value went by several names in different places -- ``admin_token`` in
the JSON, ``ADMIN_TOKEN`` and ``ADMIN_PASSWORD`` in Flask's config,
``ML_SERVER_ADMIN_PASSWORD`` in the environment -- and an operator poking at the
live file with ``d["security"]["adminToken"]`` got a bare ``KeyError`` with
nothing to say which spelling was right.

Three things live here:

* :data:`SCHEMA_VERSION` and :data:`DEFAULTS` -- the shape a current portal wants.
* :func:`migrate` -- take whatever is on disk, keep every local value and every
  secret, add what is missing, and say exactly what it changed.
* :func:`validate` -- refuse a configuration that would start a broken portal,
  and warn about one that would merely be surprising.

The module deliberately imports nothing from Flask and nothing from the rest of
the package, so ``deploy/update.sh`` can run it against a shared config file on
the server *before* it switches the ``current`` symlink to a new release.
"""

from __future__ import annotations

import copy
import json
import secrets
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

#: Bumped when a release needs a setting that an older config cannot supply.
#: A config carrying a *higher* version than this is refused: it belongs to a
#: newer release, and silently downgrading it would drop settings.
SCHEMA_VERSION = 2

#: The key that records the version. Absent means "pre-versioned", i.e. v1.
VERSION_KEY = "config_version"

#: Values that ship in the sample file. They are real strings, so nothing
#: crashes on them, but they must never be treated as a configured secret.
PLACEHOLDER_VALUES = {
    "",
    "changeme",
    "change-me",
    "admin",
    "password",
    "your-secret-key",
    "__set_secret_key__",
    "__set_admin_token__",
}

#: Legacy and mis-cased spellings, mapped to the one canonical path.
#:
#: Keys are dotted paths as they might appear in a hand-edited file; values are
#: the dotted path the portal actually reads. Migration moves the value and
#: removes the old spelling, so the file that results has exactly one name for
#: each setting.
ALIASES: Dict[str, str] = {
    "adminToken": "security.admin_token",
    "admin_token": "security.admin_token",
    "admin-token": "security.admin_token",
    "security.adminToken": "security.admin_token",
    "security.admin-token": "security.admin_token",
    "security.adminPassword": "security.admin_password",
    "security.admin-password": "security.admin_password",
    "security.adminPasswordHash": "security.admin_password_hash",
    "security.admin-password-hash": "security.admin_password_hash",
    "security.sslEnabled": "security.ssl_enabled",
    "security.ssl-enabled": "security.ssl_enabled",
    "security.csrfEnabled": "security.csrf_enabled",
    "security.csrf-enabled": "security.csrf_enabled",
    "security.allowedOrigins": "security.allowed_origins",
    "secretKey": "secret_key",
    "secret-key": "secret_key",
}

#: Settings a current portal reads, with the value used when the file omits it.
#: Only leaves appear here; a missing parent object is created on the way.
DEFAULTS: Dict[str, Any] = {
    "debug": False,
    "host": "127.0.0.1",
    "port": 5000,
    "secret_key": "",
    "feedback.database_path": "data/engagement.sqlite3",
    "analytics.enabled": True,
    "analytics.retention_months": 24,
    "logging.log_dir": "logs",
    "logging.log_file": "app.log",
    "logging.format": "%(asctime)s [%(levelname)s] %(message)s",
    "security.csrf_enabled": True,
    "security.ssl_enabled": False,
    "security.admin_token": "",
    "security.admin_password_hash": "",
    # How many reverse proxies sit in front of the portal. 0 -- the office
    # deployment, where gunicorn is reached directly -- means X-Forwarded-For
    # and X-Forwarded-Proto are NOT trusted, so a client cannot forge its own
    # address past the login lockout or claim an HTTPS scheme it does not have.
    "security.trusted_proxy_count": 0,
    "mainIconSize": [100, 100],
    "toolsIconsSize": [75, 75],
}

#: Settings whose value must never be printed, logged or put in a report.
SECRET_PATHS = {
    "secret_key",
    "security.admin_token",
    "security.admin_password",
    "security.admin_password_hash",
    "email.password",
}

_TYPES: Dict[str, type | Tuple[type, ...]] = {
    "debug": bool,
    "port": int,
    "secret_key": str,
    "analytics.enabled": bool,
    "analytics.retention_months": int,
    "security.csrf_enabled": bool,
    "security.ssl_enabled": bool,
    "security.admin_token": str,
    "security.admin_password_hash": str,
    "security.trusted_proxy_count": int,
    "security.allowed_origins": list,
}


class ConfigError(Exception):
    """A configuration that cannot be used, or cannot be migrated unambiguously."""


@dataclass
class Result:
    """What a migration did, and what is still wrong with the outcome."""

    document: Dict[str, Any]
    changes: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    @property
    def changed(self) -> bool:
        return bool(self.changes)


# ---------------------------------------------------------------------------
# Dotted-path helpers
# ---------------------------------------------------------------------------
def get_path(document: Dict[str, Any], path: str, default: Any = None) -> Any:
    """Return the value at a dotted ``path``, or ``default`` when absent."""
    node: Any = document
    for part in path.split("."):
        if not isinstance(node, dict) or part not in node:
            return default
        node = node[part]
    return node


def has_path(document: Dict[str, Any], path: str) -> bool:
    sentinel = object()
    return get_path(document, path, sentinel) is not sentinel


def set_path(document: Dict[str, Any], path: str, value: Any) -> None:
    """Set the value at a dotted ``path``, creating intermediate objects."""
    parts = path.split(".")
    node = document
    for part in parts[:-1]:
        if not isinstance(node.get(part), dict):
            node[part] = {}
        node = node[part]
    node[parts[-1]] = value


def pop_path(document: Dict[str, Any], path: str) -> Any:
    parts = path.split(".")
    node = document
    for part in parts[:-1]:
        if not isinstance(node.get(part), dict):
            return None
        node = node[part]
    return node.pop(parts[-1], None)


def is_placeholder(value: Any) -> bool:
    """Whether ``value`` is one of the sample file's stand-ins for a real secret."""
    text = str(value or "").strip()
    return text.lower() in PLACEHOLDER_VALUES or text.startswith("__SET_")


# ---------------------------------------------------------------------------
# Migration
# ---------------------------------------------------------------------------
def detect_version(document: Dict[str, Any]) -> int:
    """Return the schema version a document declares, defaulting to 1."""
    raw = document.get(VERSION_KEY, 1)
    try:
        return int(raw)
    except (TypeError, ValueError) as exc:
        raise ConfigError(
            f"{VERSION_KEY} is {raw!r}, which is not a version number. "
            "Remove the key to have it treated as the original schema."
        ) from exc


def _resolve_aliases(document: Dict[str, Any], result: Result) -> None:
    """Move every legacy spelling onto its canonical path.

    A file holding two spellings of one setting with two different values is
    ambiguous: guessing which the operator meant is exactly the kind of silent
    choice that produced the incident this module exists to prevent. Migration
    stops instead.
    """
    for alias, canonical in ALIASES.items():
        if alias == canonical or not has_path(document, alias):
            continue
        value = get_path(document, alias)
        if has_path(document, canonical):
            existing = get_path(document, canonical)
            if existing != value and not is_placeholder(existing) and not is_placeholder(value):
                raise ConfigError(
                    f"the config sets both {alias!r} and {canonical!r} to different values. "
                    f"Delete {alias!r} -- {canonical!r} is the name the portal reads -- "
                    "and run the update again."
                )
            pop_path(document, alias)
            result.changes.append(f"removed the duplicate spelling {alias!r}")
            continue
        pop_path(document, alias)
        set_path(document, canonical, value)
        result.changes.append(f"renamed {alias!r} to {canonical!r}")


def _drop_empty_parents(document: Dict[str, Any]) -> None:
    for key in [k for k, v in document.items() if isinstance(v, dict) and not v]:
        if key in {"security", "analytics", "logging", "feedback", "email", "celery"}:
            continue
        document.pop(key)


def migrate(document: Dict[str, Any], *, generate_secret_key: bool = False) -> Result:
    """Bring ``document`` up to :data:`SCHEMA_VERSION` without losing anything.

    Local values and secrets are preserved exactly. Missing settings are added
    from :data:`DEFAULTS`. Unknown keys are left alone -- a site may carry
    settings this release does not read, and dropping them would break the next
    rollback. Raises :class:`ConfigError` when the outcome would be a guess.

    With ``generate_secret_key`` the migration mints a strong ``secret_key``
    when the file has none, which is what a deployment wants: the portal signs
    admin sessions with it, and a key that is not in the file cannot be shared
    between gunicorn workers or survive a restart.
    """
    result = Result(document=copy.deepcopy(document))
    doc = result.document

    if not isinstance(doc, dict):
        raise ConfigError("the configuration file must contain a JSON object")

    version = detect_version(doc)
    if version > SCHEMA_VERSION:
        raise ConfigError(
            f"the config declares schema version {version}, but this release understands "
            f"at most {SCHEMA_VERSION}. It was written by a newer release; roll forward "
            "rather than downgrading it."
        )

    _resolve_aliases(doc, result)

    for path, default in DEFAULTS.items():
        if not has_path(doc, path):
            set_path(doc, path, copy.deepcopy(default))
            if path not in SECRET_PATHS:
                result.changes.append(f"added {path!r} = {default!r}")
            else:
                result.changes.append(f"added {path!r} (empty; set it on this server)")

    if generate_secret_key and is_placeholder(get_path(doc, "secret_key")):
        set_path(doc, "secret_key", secrets.token_urlsafe(48))
        result.changes.append(
            "generated a stable 'secret_key' so admin sessions survive restarts "
            "and are shared by every worker"
        )

    # A placeholder is not a secret. Normalising it to "" here means every
    # later reader -- the portal, the status script, the health check -- asks
    # one question ("is it empty?") instead of each keeping its own list of
    # strings that look like secrets but are printed in the sample file.
    for path in ("secret_key", "security.admin_token", "security.admin_password_hash"):
        if has_path(doc, path) and is_placeholder(get_path(doc, path)):
            if get_path(doc, path) != "":
                result.changes.append(f"cleared the placeholder value in {path!r}")
            set_path(doc, path, "")

    _drop_empty_parents(doc)

    if version != SCHEMA_VERSION:
        result.changes.append(f"set {VERSION_KEY} from {version} to {SCHEMA_VERSION}")
    doc[VERSION_KEY] = SCHEMA_VERSION

    problems = validate(doc)
    result.errors.extend(problems.errors)
    result.warnings.extend(problems.warnings)
    return result


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
def validate(document: Dict[str, Any]) -> Result:
    """Report what is wrong with ``document``, separating fatal from merely odd."""
    result = Result(document=document)

    if not isinstance(document, dict):
        result.errors.append("the configuration file must contain a JSON object")
        return result

    try:
        version = detect_version(document)
    except ConfigError as exc:
        result.errors.append(str(exc))
        return result

    if version > SCHEMA_VERSION:
        result.errors.append(
            f"schema version {version} is newer than this release understands ({SCHEMA_VERSION})"
        )
    elif version < SCHEMA_VERSION:
        result.warnings.append(
            f"schema version {version} predates this release ({SCHEMA_VERSION}); migrate it"
        )

    for alias, canonical in ALIASES.items():
        if alias != canonical and has_path(document, alias):
            result.warnings.append(
                f"{alias!r} is a legacy spelling of {canonical!r} and is ignored by the portal"
            )

    for path, expected in _TYPES.items():
        if not has_path(document, path):
            continue
        value = get_path(document, path)
        if expected is bool and isinstance(value, bool):
            continue
        if expected is int and isinstance(value, bool):
            result.errors.append(f"{path!r} should be a number, not a true/false value")
            continue
        if not isinstance(value, expected):  # type: ignore[arg-type]
            name = getattr(expected, "__name__", str(expected))
            result.errors.append(f"{path!r} should be a {name}, but it is {type(value).__name__}")

    port = get_path(document, "port", 5000)
    if isinstance(port, int) and not 1 <= port <= 65535:
        result.errors.append(f"'port' is {port}, which is not a usable TCP port")

    months = get_path(document, "analytics.retention_months", 24)
    if isinstance(months, int) and months < 1:
        result.errors.append("'analytics.retention_months' must be at least 1")

    proxies = get_path(document, "security.trusted_proxy_count", 0)
    if isinstance(proxies, int) and proxies < 0:
        result.errors.append("'security.trusted_proxy_count' cannot be negative")

    if is_placeholder(get_path(document, "secret_key")):
        result.warnings.append(
            "'secret_key' is empty or a placeholder; the portal will derive a stable key from "
            "its state directory instead, but setting one here is better"
        )

    if is_placeholder(get_path(document, "security.admin_token")) and is_placeholder(
        get_path(document, "security.admin_password_hash")
    ):
        result.warnings.append(
            "no admin credential is configured; the operations console will refuse every login "
            "until 'security.admin_token' or 'security.admin_password_hash' is set"
        )

    if get_path(document, "security.csrf_enabled", True) is False:
        result.errors.append(
            "'security.csrf_enabled' is false. CSRF protection is not optional on the admin "
            "console; fix the cause of the failure rather than disabling the defence."
        )

    if get_path(document, "debug") is True:
        result.warnings.append("'debug' is true, which is not a setting for a shared server")

    return result


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------
def summarize(document: Dict[str, Any]) -> Dict[str, Any]:
    """A description of the configuration that contains no secret whatsoever.

    Every value here is either a boolean, a number, a fixed word, or a
    yes/no answer about whether a secret exists -- never the secret itself.
    """
    ssl_enabled = bool(get_path(document, "security.ssl_enabled", False))
    admin_configured = not is_placeholder(
        get_path(document, "security.admin_token")
    ) or not is_placeholder(get_path(document, "security.admin_password_hash"))
    return {
        "schema_version": get_path(document, VERSION_KEY, 1),
        "expected_schema_version": SCHEMA_VERSION,
        "scheme": "https" if ssl_enabled else "http",
        "ssl_enabled": ssl_enabled,
        "session_cookie_secure": ssl_enabled,
        "csrf_enabled": bool(get_path(document, "security.csrf_enabled", True)),
        "trusted_proxy_count": int(get_path(document, "security.trusted_proxy_count", 0) or 0),
        "admin_authentication_configured": admin_configured,
        "admin_credential_kind": (
            "password_hash"
            if not is_placeholder(get_path(document, "security.admin_password_hash"))
            else (
                "token"
                if not is_placeholder(get_path(document, "security.admin_token"))
                else "none"
            )
        ),
        "secret_key_configured": not is_placeholder(get_path(document, "secret_key")),
        "debug": bool(get_path(document, "debug", False)),
        "port": get_path(document, "port", 5000),
        "analytics_enabled": bool(get_path(document, "analytics.enabled", True)),
    }


# ---------------------------------------------------------------------------
# File-level operations, used by the CLI and by deploy/update.sh
# ---------------------------------------------------------------------------
def load_document(path: Path) -> Dict[str, Any]:
    """Read a config file, turning a parse failure into a legible error."""
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigError(f"cannot read {path}: {exc}") from exc
    try:
        document = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ConfigError(
            f"{path} is not valid JSON: {exc.msg} at line {exc.lineno}, column {exc.colno}"
        ) from exc
    if not isinstance(document, dict):
        raise ConfigError(f"{path} must contain a JSON object, not a {type(document).__name__}")
    return document


def backup_path(path: Path, stamp: str) -> Path:
    """Where the pre-migration copy of ``path`` is kept."""
    return Path(path).with_name(f"{Path(path).name}.bak-{stamp}")


def write_document(path: Path, document: Dict[str, Any]) -> None:
    """Write ``document`` atomically, so a crash cannot truncate a live config.

    The file is written with a trailing newline and LF line endings regardless
    of the platform that produced it, because the same file is edited on a
    Windows workstation and read on the Ubuntu server.
    """
    path = Path(path)
    text = json.dumps(document, indent=4, ensure_ascii=False) + "\n"
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(text, encoding="utf-8", newline="\n")
    temporary.replace(path)


def migrate_file(
    path: Path,
    *,
    apply: bool,
    stamp: str,
    generate_secret_key: bool = True,
) -> Result:
    """Validate and migrate the config at ``path``.

    With ``apply`` false nothing is written: the result describes what would
    change, which is what ``update.sh`` runs during preflight. With ``apply``
    true the original is copied to :func:`backup_path` *before* the new document
    replaces it, and the file is left untouched when nothing needed changing or
    when the outcome would not validate.
    """
    document = load_document(path)
    result = migrate(document, generate_secret_key=generate_secret_key)

    if not apply or not result.ok:
        return result
    if not result.changed:
        return result

    backup = backup_path(path, stamp)
    backup.write_text(Path(path).read_text(encoding="utf-8"), encoding="utf-8", newline="")
    write_document(path, result.document)
    result.changes.append(f"original kept at {backup.name}")
    return result


def format_report(path: Path, result: Result, *, applied: bool) -> Iterable[str]:
    """Human-readable lines for a terminal, containing no secret values."""
    yield f"config: {path}"
    summary = summarize(result.document)
    for key, value in summary.items():
        yield f"  {key}: {value}"
    if result.changes:
        yield "  changes:" if applied else "  changes that would be made:"
        for change in result.changes:
            yield f"    - {change}"
    for warning in result.warnings:
        yield f"  warning: {warning}"
    for error in result.errors:
        yield f"  ERROR: {error}"
