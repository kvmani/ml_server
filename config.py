from __future__ import annotations

import json
import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Any, Dict

from pydantic import Field
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    """Application settings loaded from config.json and environment."""

    debug: bool = False
    secret_key: str = ""
    host: str = "127.0.0.1"
    port: int = 5000
    super_resolution: Dict[str, Any] = Field(default_factory=dict)
    ebsd_cleanup: Dict[str, Any] = Field(default_factory=dict)
    hydride_segmentation: Dict[str, Any] = Field(default_factory=dict)
    feedback: Dict[str, Any] = Field(default_factory=dict)
    logging: Dict[str, Any] = Field(default_factory=dict)
    security: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        env_prefix = "APP_"
        env_nested_delimiter = "__"

        @classmethod
        def customise_sources(cls, init_settings, env_settings, file_secret_settings):
            return (
                init_settings,
                cls.json_config_settings_source,
                env_settings,
                file_secret_settings,
            )

        @staticmethod
        def json_config_settings_source(_: BaseSettings) -> Dict[str, Any]:
            path = os.path.join(os.path.dirname(__file__), "config.json")
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)

    @property
    def super_resolution_settings(self) -> Dict[str, Any]:
        return self.super_resolution

    @property
    def ebsd_cleanup_settings(self) -> Dict[str, Any]:
        return self.ebsd_cleanup

    @property
    def logging_settings(self) -> Dict[str, Any]:
        return self.logging

    def setup_logging(self) -> None:
        log_dir = self.logging_settings.get("log_dir", "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, self.logging_settings.get("log_file", "app.log"))
        handler = RotatingFileHandler(
            log_path,
            maxBytes=self.logging_settings.get("max_size", 10 * 1024 * 1024),
            backupCount=self.logging_settings.get("backup_count", 5),
        )
        fmt = logging.Formatter(
            self.logging_settings.get("format", "%(asctime)s [%(levelname)s] %(message)s")
        )
        handler.setFormatter(fmt)
        root = logging.getLogger()
        root.setLevel(logging.DEBUG if self.debug else logging.INFO)
        root.handlers.clear()
        root.addHandler(handler)


def load_config() -> Config:
    cfg = Config()
    cfg.setup_logging()
    return cfg
