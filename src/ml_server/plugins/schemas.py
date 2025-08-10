from __future__ import annotations

"""Pydantic models for plugin API contracts."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ErrorV1(BaseModel):
    """Common error response."""

    code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    trace_id: Optional[str] = Field(default=None, alias="trace_id")


class HealthV1(BaseModel):
    """Health check response."""

    status: str
    version: Optional[str] = None
    uptime_s: Optional[int] = None


class InfoV1(BaseModel):
    """Tool information."""

    name: str
    version: str
    description: str
    homepage: Optional[str] = None
    authors: List[str] = []
    capabilities: List[str] = []
    api_version: str


class MetricsV1(BaseModel):
    """Metrics payload."""

    tool: str
    version: str
    uptime_s: int
    counters: Dict[str, int] = {}
    gauges: Dict[str, float | int] = {}
    timers: Dict[str, float | int] = {}


__all__ = ["ErrorV1", "HealthV1", "InfoV1", "MetricsV1"]
