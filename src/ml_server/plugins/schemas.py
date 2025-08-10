"""Pydantic models for the plugin HTTP contract."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class HealthV1(BaseModel):
    """Health check response."""

    status: str
    version: Optional[str] = None
    uptime_s: Optional[int] = None


class InfoV1(BaseModel):
    """Information about a plugin."""

    name: str
    version: str
    description: Optional[str] = None
    homepage: Optional[str] = None
    authors: List[str] = Field(default_factory=list)
    capabilities: List[str] = Field(default_factory=list)
    api_version: str = "v1"


class MetricsV1(BaseModel):
    """Metrics schema v1."""

    tool: str
    version: str
    uptime_s: int
    counters: Dict[str, int] = Field(default_factory=dict)
    gauges: Dict[str, int] = Field(default_factory=dict)
    timers: Dict[str, int] = Field(default_factory=dict)


class ErrorV1(BaseModel):
    """Common error structure."""

    code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    trace_id: Optional[str] = None
