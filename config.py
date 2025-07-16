import os
import json
import logging
from typing import Any, Dict


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
        config_path = os.path.join(os.path.dirname(__file__), "config.json")
        with open(config_path, "r") as f:
            self.config: Dict[str, Any] = json.load(f)
        self._apply_env_overrides()
        self._setup_logging()

    def _apply_env_overrides(self) -> None:
        prefix_len = len(self._ENV_PREFIX)
        for key, value in os.environ.items():
            if not key.startswith(self._ENV_PREFIX):
                continue
            path = key[prefix_len:].lower().split("__")
            self._set_nested_value(self.config, path, value)

    def _set_nested_value(self, data: Dict[str, Any], path: list[str], value: str) -> None:
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
            format=self.logging_settings.get("format", "%(asctime)s [%(levelname)s] %(message)s"),
            filename=os.path.join(log_dir, self.logging_settings.get("log_file", "app.log")),
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
        return self.config.get("secret_key", "")

    @property
    def super_resolution_settings(self) -> Dict[str, Any]:
        return self.config.get("super_resolution", {})

    @property
    def ebsd_cleanup_settings(self) -> Dict[str, Any]:
        return self.config.get("ebsd_cleanup", {})

    @property
    def feedback_settings(self) -> Dict[str, Any]:
        return self.config.get("feedback", {})

    @property
    def logging_settings(self) -> Dict[str, Any]:
        return self.config.get("logging", {})

    @property
    def security_settings(self) -> Dict[str, Any]:
        return self.config.get("security", {})

    # Backwards compatibility helpers
    @property
    def super_resolution_extensions(self) -> set:
        return set(self.super_resolution_settings.get("allowed_extensions", []))

    @property
    def ebsd_extensions(self) -> set:
        return set(self.ebsd_cleanup_settings.get("allowed_extensions", []))

    @property
    def ml_model_url(self) -> str:
        return self.super_resolution_settings.get("ml_model", {}).get("url", "")

    @property
    def ml_model_health_url(self) -> str:
        return self.super_resolution_settings.get("ml_model", {}).get("health_url", "")

    # Dummy service starters for tests
    def start_ml_model_service(self) -> bool:  # pragma: no cover - placeholder
        return False

    def start_ebsd_model_service(self) -> bool:  # pragma: no cover - placeholder
        return False
