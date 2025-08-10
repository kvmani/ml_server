"""Plugin registry for remote services and embedded blueprints."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from importlib import import_module
from typing import Any, Callable, Dict, Optional

import requests
import yaml
from flask import Blueprint, Flask

from .schemas import HealthV1, InfoV1, MetricsV1

HTTP_TIMEOUT = 5


@dataclass
class RemotePlugin:
    """Represents a remotely hosted plugin accessible via HTTP."""

    name: str
    base_url: str

    def _get(self, endpoint: str) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        try:
            resp = requests.get(url, timeout=HTTP_TIMEOUT)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as exc:  # pragma: no cover - network errors
            return {"error": {"code": "network", "message": str(exc)}}

    def health(self) -> Optional[HealthV1]:
        data = self._get("/health")
        if "error" in data:
            return None
        return HealthV1(**data)

    def info(self) -> Optional[InfoV1]:
        data = self._get("/info")
        if "error" in data:
            return None
        return InfoV1(**data)

    def metrics(self) -> Optional[MetricsV1]:
        data = self._get("/metrics")
        if "error" in data:
            return None
        return MetricsV1(**data)


@dataclass
class EmbeddedPlugin:
    """Plugin running inside the Flask process as a blueprint."""

    name: str
    mount: str
    blueprint: Blueprint
    app: Flask

    def _get(self, path: str) -> Dict[str, Any]:
        with self.app.test_client() as client:
            resp = client.get(f"{self.mount}{path}")
            return resp.get_json() or {}

    def health(self) -> Optional[HealthV1]:
        data = self._get("/health")
        if "error" in data:
            return None
        return HealthV1(**data)

    def info(self) -> Optional[InfoV1]:
        data = self._get("/info")
        if "error" in data:
            return None
        return InfoV1(**data)

    def metrics(self) -> Optional[MetricsV1]:
        data = self._get("/metrics")
        if "error" in data:
            return None
        return MetricsV1(**data)


class PluginRegistry:
    """Registry for plugins with helper methods to query them."""

    def __init__(self, app: Optional[Flask] = None) -> None:
        self.app = app
        self._plugins: Dict[str, Any] = {}

    # Registration helpers
    def register_remote(self, name: str, base_url: str) -> None:
        self._plugins[name] = RemotePlugin(name=name, base_url=base_url)

    def register_embedded(
        self, name: str, import_path: str, mount: str, config: Optional[dict[str, Any]] = None
    ) -> None:
        if not self.app:
            raise RuntimeError("Embedded plugins require a Flask app instance")
        module_path, factory_name = import_path.split(":", 1)
        module = import_module(module_path)
        factory: Callable[[dict[str, Any]], Blueprint] = getattr(module, factory_name)
        blueprint = factory(config or {})
        self.app.register_blueprint(blueprint, url_prefix=mount)
        self._plugins[name] = EmbeddedPlugin(
            name=name, mount=mount, blueprint=blueprint, app=self.app
        )

    # Query helpers
    def list_tools(self) -> list[str]:
        return list(self._plugins.keys())

    def get_tool(self, name: str) -> Any:
        return self._plugins.get(name)

    def health(self, name: str) -> Optional[HealthV1]:
        plugin = self.get_tool(name)
        return plugin.health() if plugin else None

    def info(self, name: str) -> Optional[InfoV1]:
        plugin = self.get_tool(name)
        return plugin.info() if plugin else None

    def metrics(self, name: str) -> Optional[MetricsV1]:
        plugin = self.get_tool(name)
        return plugin.metrics() if plugin else None

    # Config loader
    @classmethod
    def from_file(cls, path: str, app: Optional[Flask] = None) -> "PluginRegistry":
        with open(path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
        registry = cls(app)
        for tool in cfg.get("tools", []):
            if tool.get("mode") == "remote":
                registry.register_remote(tool["name"], tool["base_url"])
            elif tool.get("mode") == "embedded":
                try:
                    registry.register_embedded(
                        tool["name"], tool["import"], tool.get("mount", f"/{tool['name']}")
                    )
                except (ImportError, RuntimeError) as exc:  # pragma: no cover - optional plugins
                    logging.getLogger(__name__).warning(
                        "Plugin %s not loaded: %s", tool["name"], exc
                    )
        return registry
