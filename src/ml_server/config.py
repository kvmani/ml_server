import json
import logging
import os
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv


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
        self._setup_logging()

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
        value = str(self.config.get("secret_key", ""))
        return "" if value.startswith("__SET_") else value

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
