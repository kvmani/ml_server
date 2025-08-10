from __future__ import annotations

"""Plugin registry for remote and embedded tools."""

from dataclasses import dataclass
from importlib import import_module
from typing import Callable, Dict, List, Optional

import requests
from flask import Flask
from requests import RequestException

from .schemas import ErrorV1, HealthV1, InfoV1, MetricsV1


@dataclass
class _Tool:
    name: str
    mode: str  # "remote" or "embedded"
    base_url: str
    blueprint_factory: Optional[Callable[[dict | None], object]] = None
    mount: Optional[str] = None


class PluginRegistry:
    """Registry of configured tools."""

    def __init__(self, app: Flask | None = None) -> None:
        self.app = app
        self._tools: Dict[str, _Tool] = {}

    # registration -------------------------------------------------
    def register_remote(self, name: str, base_url: str) -> None:
        self._tools[name] = _Tool(name=name, mode="remote", base_url=base_url)

    def register_embedded(
        self,
        name: str,
        import_path: str | Callable[[dict | None], object],
        mount: str,
        config: dict | None = None,
    ) -> None:
        if callable(import_path):
            factory = import_path
        else:
            module_name, func_name = import_path.split(":")
            module = import_module(module_name)
            factory = getattr(module, func_name)
        blueprint = factory(config or {})
        if not self.app:
            raise RuntimeError("App required for embedded plugins")
        self.app.register_blueprint(blueprint, url_prefix=mount)
        self._tools[name] = _Tool(
            name=name,
            mode="embedded",
            base_url=mount,
            blueprint_factory=factory,
            mount=mount,
        )

    def list_tools(self) -> List[_Tool]:
        return list(self._tools.values())

    def get_tool(self, name: str) -> _Tool | None:
        return self._tools.get(name)

    # helpers ------------------------------------------------------
    def _request(self, url: str) -> dict | ErrorV1:
        try:
            resp = requests.get(url, timeout=5)
            resp.raise_for_status()
            return resp.json()
        except RequestException as exc:  # pragma: no cover - network failure path
            return ErrorV1(code="request_error", message=str(exc))

    def _embedded_request(self, path: str) -> dict | ErrorV1:
        if not self.app:
            return ErrorV1(code="app_missing", message="Flask app not set")
        with self.app.test_client() as client:
            resp = client.get(path)
            if resp.status_code != 200:
                return ErrorV1(code="http_error", message=str(resp.status))
            return resp.get_json() or {}

    # public API ---------------------------------------------------
    def health(self, name: str) -> HealthV1 | ErrorV1:
        tool = self._tools[name]
        url = f"{tool.base_url}/health"
        data = self._embedded_request(url) if tool.mode == "embedded" else self._request(url)
        return HealthV1.model_validate(data) if isinstance(data, dict) else data

    def info(self, name: str) -> InfoV1 | ErrorV1:
        tool = self._tools[name]
        url = f"{tool.base_url}/info"
        data = self._embedded_request(url) if tool.mode == "embedded" else self._request(url)
        return InfoV1.model_validate(data) if isinstance(data, dict) else data

    def metrics(self, name: str) -> MetricsV1 | ErrorV1:
        tool = self._tools[name]
        url = f"{tool.base_url}/metrics"
        data = self._embedded_request(url) if tool.mode == "embedded" else self._request(url)
        return MetricsV1.model_validate(data) if isinstance(data, dict) else data

    # configuration ------------------------------------------------
    def load_from_file(self, path: str) -> None:
        import yaml

        with open(path) as f:
            cfg = yaml.safe_load(f) or {}
        for tool_cfg in cfg.get("tools", []):
            name = tool_cfg["name"]
            mode = tool_cfg["mode"]
            if mode == "remote":
                self.register_remote(name, tool_cfg["base_url"])
            elif mode == "embedded":
                self.register_embedded(
                    name,
                    tool_cfg["import"],
                    tool_cfg.get("mount", f"/{name}"),
                    tool_cfg.get("config"),
                )


__all__ = ["PluginRegistry"]
