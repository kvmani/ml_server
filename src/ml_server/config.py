import json
import logging
import os
import secrets
import stat
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv

from . import config_schema

#: Where a generated signing key is kept when the config file supplies none.
#: It sits beside the configuration -- under ``shared/config/`` in the office
#: deployment -- so every gunicorn worker reads the same key and a restart or an
#: upgrade does not sign every administrator out. See docs/ADMIN_DASHBOARD.md.
SECRET_KEY_FILENAME = ".session_secret_key"


class Config:
    """Singleton configuration loader with environment variable overrides."""

    _instance = None
    _ENV_PREFIX = "APP_"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self) -> None:
        package_root = Path(__file__).resolve().parent
        checkout_root = package_root.parents[1]
        load_dotenv(Path.cwd() / ".env", override=False)
        load_dotenv(checkout_root / ".env", override=False)
        explicit_path = os.getenv("ML_SERVER_CONFIG")
        candidates = [
            Path(explicit_path).expanduser() if explicit_path else None,
            Path.cwd() / "config" / "config.intranet.json",
            Path.cwd() / "config.intranet.json",
            checkout_root / "config.intranet.json",
            package_root / "default_config.json",
        ]
        config_path = next(
            (candidate for candidate in candidates if candidate and candidate.is_file()),
            None,
        )
        if config_path is None:
            raise FileNotFoundError(
                "No portal configuration found; set ML_SERVER_CONFIG to a readable JSON file."
            )
        with config_path.open("r", encoding="utf-8") as f:
            self.config: Dict[str, Any] = json.load(f)
        self.config_path = config_path
        self._apply_env_overrides()
        self._normalize()
        self._setup_logging()

    def _normalize(self) -> None:
        """Put the loaded document into canonical form, in memory only.

        The file on disk is migrated by the updater before the release is
        activated (``deploy/update.sh``), but a portal started by hand, in a
        test, or from a hand-edited file must not behave differently from one
        the updater prepared. Normalising here means every accessor below reads
        exactly one spelling of every setting, and a legacy ``adminToken`` works
        rather than raising ``KeyError`` somewhere far from its cause.

        Nothing is written back: the file belongs to the operator.
        """
        try:
            result = config_schema.migrate(self.config, generate_secret_key=False)
        except config_schema.ConfigError as exc:
            raise ValueError(f"{self.config_path}: {exc}") from exc
        self.config = result.document
        self.config_problems = result
        logger = logging.getLogger(__name__)
        for message in result.warnings:
            logger.warning("configuration: %s", message)
        for message in result.errors:
            logger.error("configuration: %s", message)

    def _apply_env_overrides(self) -> None:
        prefix_len = len(self._ENV_PREFIX)
        for key, value in os.environ.items():
            if not key.startswith(self._ENV_PREFIX):
                continue
            path = key[prefix_len:].lower().split("__")
            self._set_nested_value(self.config, path, value)

    def _set_nested_value(
        self, data: Dict[str, Any], path: list[str], value: str
    ) -> None:  # noqa: E501
        for part in path[:-1]:
            if part not in data or not isinstance(data[part], dict):
                data[part] = {}
            data = data[part]
        try:
            data[path[-1]] = json.loads(value)
        except Exception:
            data[path[-1]] = value

    def _setup_logging(self) -> None:
        log_level = logging.DEBUG if self.debug else logging.INFO
        log_dir = self.logging_settings.get("log_dir", "logs")
        os.makedirs(log_dir, exist_ok=True)
        logging.basicConfig(
            level=log_level,
            format=self.logging_settings.get(
                "format",
                "%(asctime)s [%(levelname)s] %(message)s",
            ),
            filename=os.path.join(
                log_dir,
                self.logging_settings.get("log_file", "app.log"),
            ),
        )

    # === Accessors ===
    @property
    def host(self) -> str:
        return self.config.get("host", "127.0.0.1")

    @property
    def port(self) -> int:
        return int(self.config.get("port", 5000))

    @property
    def debug(self) -> bool:
        return bool(self.config.get("debug", False))

    @property
    def secret_key(self) -> str:
        """The signing key the operator configured, or "" when they set none."""
        value = str(self.config.get("secret_key", ""))
        return "" if config_schema.is_placeholder(value) else value

    @property
    def schema_version(self) -> int:
        return int(self.config.get(config_schema.VERSION_KEY, 1))

    @property
    def state_dir(self) -> Path:
        """Where the portal may keep small files it owns, such as a signing key.

        ``ML_SERVER_STATE_DIR`` wins when it is set. Otherwise the directory
        holding the configuration file is used: in the office deployment that is
        ``shared/config/``, which is outside every release directory and so
        survives upgrades, rollbacks and pruning.
        """
        override = os.getenv("ML_SERVER_STATE_DIR")
        if override:
            return Path(override).expanduser()
        return Path(self.config_path).resolve().parent

    def resolved_secret_key(self) -> str:
        """The key used to sign sessions -- configured, or persisted-and-reused.

        Flask signs the admin session cookie with this. Generating a fresh one
        per process, which is what this code used to do, breaks the admin login
        outright under ``gunicorn --workers 2``: the worker handling the login
        POST cannot verify the cookie the worker that rendered the form signed,
        so the CSRF token appears to have vanished and the form reports that it
        expired. A key on disk is read by every worker and survives restarts.
        """
        configured = self.secret_key
        if configured:
            return configured
        return self._persisted_secret_key()

    def _persisted_secret_key(self) -> str:
        """Read the generated signing key, creating it once if it is absent."""
        logger = logging.getLogger(__name__)
        directory = self.state_dir
        path = directory / SECRET_KEY_FILENAME
        try:
            directory.mkdir(parents=True, exist_ok=True)
            existing = path.read_text(encoding="utf-8").strip() if path.is_file() else ""
            if existing:
                return existing
            # O_EXCL, so two workers starting at the same instant cannot each
            # write a key and disagree about which one signed the cookie.
            candidate = secrets.token_urlsafe(48)
            try:
                descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            except FileExistsError:
                return path.read_text(encoding="utf-8").strip()
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                handle.write(candidate)
            os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
            logger.warning(
                "No secret_key in %s; generated one at %s. Every worker and every "
                "restart now share it, but setting 'secret_key' in the config is better.",
                self.config_path,
                path,
            )
            return candidate
        except OSError as exc:
            # A read-only state directory is a misconfiguration worth shouting
            # about, but refusing to start would take the whole portal down over
            # the admin console. Sessions simply will not outlive the process.
            logger.error(
                "Could not persist a signing key in %s (%s); admin sessions will not "
                "survive a restart and may fail with a multi-worker server. Set "
                "'secret_key' in %s.",
                directory,
                exc,
                self.config_path,
            )
            return secrets.token_urlsafe(48)

    @property
    def ssl_enabled(self) -> bool:
        """Whether this portal is served over HTTPS.

        Everything that must differ between an HTTP intranet deployment and an
        HTTPS one hangs off this single answer: the Secure flag on the session
        cookie, the HTTPS redirect, and HSTS.
        """
        return bool(self.security_settings.get("ssl_enabled", False))

    @property
    def csrf_enabled(self) -> bool:
        return bool(self.security_settings.get("csrf_enabled", True))

    @property
    def trusted_proxy_count(self) -> int:
        """How many reverse proxies sit in front of the portal; 0 in the office.

        With 0, ``X-Forwarded-For`` and ``X-Forwarded-Proto`` are not believed,
        so a client on the intranet cannot forge its address past the admin
        login lockout or claim a scheme the connection does not have.
        """
        try:
            return max(0, int(self.security_settings.get("trusted_proxy_count", 0)))
        except (TypeError, ValueError):
            return 0

    def summary(self) -> Dict[str, Any]:
        """A secret-free description of this configuration, for status output."""
        report = config_schema.summarize(self.config)
        report["config_path"] = str(self.config_path)
        return report

    @property
    def celery_settings(self) -> Dict[str, Any]:
        return self.config.get("celery", {})

    @property
    def download_settings(self) -> Dict[str, Any]:
        return self.config.get("download", {})

    @property
    def processed_data_path(self) -> str:
        return self.download_settings.get("processed_data_path", "tmp/processed_data.bin")

    @property
    def feedback_settings(self) -> Dict[str, Any]:
        return self.config.get("feedback", {})

    @property
    def analytics_settings(self) -> Dict[str, Any]:
        return self.config.get("analytics", {})

    @property
    def email_settings(self) -> Dict[str, Any]:
        return self.config.get("email", {})

    @property
    def logging_settings(self) -> Dict[str, Any]:
        return self.config.get("logging", {})

    @property
    def security_settings(self) -> Dict[str, Any]:
        return self.config.get("security", {})

    @property
    def admin_token(self) -> str:
        value = str(self.security_settings.get("admin_token", ""))
        return "" if config_schema.is_placeholder(value) else value

    @property
    def admin_password(self) -> str:
        """The admin dashboard password, if one is set in configuration.

        Deployments should prefer the environment (``ML_SERVER_ADMIN_PASSWORD``)
        or, better, a hash, so no secret is ever committed. ``admin_token`` is
        accepted as a fallback so an existing installation keeps working.
        """
        value = str(self.security_settings.get("admin_password", ""))
        if value.startswith("__SET_"):
            return ""
        return value or self.admin_token

    @property
    def admin_password_hash(self) -> str:
        """A PBKDF2 hash of the admin password, preferred over the password."""
        value = str(self.security_settings.get("admin_password_hash", ""))
        return "" if value.startswith("__SET_") else value

    @property
    def main_icon_size(self) -> list[int]:
        """Return (width, height) for the main site icon."""
        return self.config.get("mainIconSize", [100, 100])

    @property
    def tools_icons_size(self) -> list[int]:
        """Return (width, height) for tool icons."""
        return self.config.get("toolsIconsSize", [75, 75])


def load_config() -> Config:
    return Config()
