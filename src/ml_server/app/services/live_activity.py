from __future__ import annotations

"""Who is using the portal *right now*, held only in memory.

Operations support needs to answer "which machine is hammering which service?"
while an incident is happening. That question is about the present moment, so
this registry keeps a short, bounded, in-process view of recent client activity
and never writes any of it to disk.

Privacy contract
----------------
Client IP addresses appear here and nowhere else. They live in process memory
for :attr:`LiveActivityRegistry.ttl_seconds` (five minutes by default), are
visible only to an authenticated administrator, and disappear when a client
goes idle or when the service restarts. The durable analytics database still
stores no address: it keeps an irreversible per-client digest instead, which is
enough to count distinct visitors but not to name one. See
:mod:`ml_server.app.services.engagement`.
"""

import threading
import time
from dataclasses import dataclass, field
from typing import Any

# Five minutes matches the window the Prometheus active-user gauge already uses,
# so the dashboard and the metrics endpoint never disagree about who is active.
DEFAULT_TTL_SECONDS = 300

# A hard ceiling keeps a scan or a misbehaving client from growing the registry
# without bound. The office intranet has far fewer clients than this.
DEFAULT_MAX_CLIENTS = 5000


@dataclass
class _ServiceUse:
    requests: int = 0
    errors: int = 0
    total_ms: float = 0.0
    last_seen: float = 0.0


@dataclass
class _Client:
    ip: str
    first_seen: float
    last_seen: float
    browser: str = "Unknown"
    requests: int = 0
    errors: int = 0
    total_ms: float = 0.0
    last_path: str = ""
    last_status: int = 0
    services: dict[str, _ServiceUse] = field(default_factory=dict)


class LiveActivityRegistry:
    """A thread-safe, expiring map of client address to current activity."""

    def __init__(
        self,
        ttl_seconds: int = DEFAULT_TTL_SECONDS,
        max_clients: int = DEFAULT_MAX_CLIENTS,
    ) -> None:
        self.ttl_seconds = ttl_seconds
        self.max_clients = max_clients
        self._clients: dict[str, _Client] = {}
        self._lock = threading.Lock()

    # -- recording ---------------------------------------------------------
    def record(
        self,
        *,
        ip: str | None,
        service_name: str,
        path: str = "",
        status_code: int = 200,
        duration_ms: float = 0.0,
        browser: str | None = None,
        now: float | None = None,
    ) -> None:
        """Note one request from ``ip`` against ``service_name``."""
        address = (ip or "unknown").strip() or "unknown"
        moment = time.time() if now is None else now
        with self._lock:
            client = self._clients.get(address)
            if client is None:
                client = _Client(ip=address, first_seen=moment, last_seen=moment)
                self._clients[address] = client
            client.last_seen = moment
            client.requests += 1
            client.total_ms += max(0.0, float(duration_ms))
            client.last_path = path[:200]
            client.last_status = int(status_code)
            if browser and browser != "Unknown":
                client.browser = browser
            if status_code >= 400:
                client.errors += 1

            use = client.services.get(service_name)
            if use is None:
                use = _ServiceUse()
                client.services[service_name] = use
            use.requests += 1
            use.total_ms += max(0.0, float(duration_ms))
            use.last_seen = moment
            if status_code >= 400:
                use.errors += 1

            self._expire(moment)

    # -- reading -----------------------------------------------------------
    def _expire(self, now: float) -> None:
        """Drop idle clients. Callers must already hold the lock."""
        cutoff = now - self.ttl_seconds
        for address, client in list(self._clients.items()):
            if client.last_seen < cutoff:
                del self._clients[address]
        overflow = len(self._clients) - self.max_clients
        if overflow > 0:
            oldest = sorted(self._clients.items(), key=lambda item: item[1].last_seen)
            for address, _ in oldest[:overflow]:
                del self._clients[address]

    def active_client_count(self, now: float | None = None) -> int:
        moment = time.time() if now is None else now
        with self._lock:
            self._expire(moment)
            return len(self._clients)

    def snapshot(self, now: float | None = None) -> dict[str, Any]:
        """Return the current activity view, least idle client first."""
        moment = time.time() if now is None else now
        with self._lock:
            self._expire(moment)
            clients = [self._client_view(client, moment) for client in self._clients.values()]
            services = self._service_view(moment)
        clients.sort(key=lambda item: item["idle_seconds"])
        services.sort(key=lambda item: (-item["clients"], item["service"]))
        return {
            "generated_at": moment,
            "window_seconds": self.ttl_seconds,
            "active_clients": len(clients),
            "active_requests": sum(item["requests"] for item in clients),
            "clients": clients,
            "services": services,
        }

    def _client_view(self, client: _Client, now: float) -> dict[str, Any]:
        services = sorted(
            client.services.items(), key=lambda item: item[1].last_seen, reverse=True
        )
        return {
            "ip": client.ip,
            "browser": client.browser,
            "requests": client.requests,
            "errors": client.errors,
            "average_ms": round(client.total_ms / client.requests, 1) if client.requests else 0.0,
            "last_path": client.last_path,
            "last_status": client.last_status,
            "idle_seconds": round(max(0.0, now - client.last_seen), 1),
            "session_seconds": round(max(0.0, client.last_seen - client.first_seen), 1),
            "current_service": services[0][0] if services else "Portal",
            "services": [
                {
                    "service": name,
                    "requests": use.requests,
                    "errors": use.errors,
                    "idle_seconds": round(max(0.0, now - use.last_seen), 1),
                }
                for name, use in services
            ],
        }

    def _service_view(self, now: float) -> list[dict[str, Any]]:
        """Aggregate the per-client map into a per-service one."""
        totals: dict[str, dict[str, Any]] = {}
        for client in self._clients.values():
            for name, use in client.services.items():
                entry = totals.setdefault(
                    name,
                    {
                        "service": name,
                        "clients": 0,
                        "requests": 0,
                        "errors": 0,
                        "total_ms": 0.0,
                        "last_seen": 0.0,
                        "addresses": [],
                    },
                )
                entry["clients"] += 1
                entry["requests"] += use.requests
                entry["errors"] += use.errors
                entry["total_ms"] += use.total_ms
                entry["last_seen"] = max(entry["last_seen"], use.last_seen)
                entry["addresses"].append(client.ip)
        views = []
        for entry in totals.values():
            requests = entry["requests"]
            views.append(
                {
                    "service": entry["service"],
                    "clients": entry["clients"],
                    "requests": requests,
                    "errors": entry["errors"],
                    "average_ms": round(entry["total_ms"] / requests, 1) if requests else 0.0,
                    "idle_seconds": round(max(0.0, now - entry["last_seen"]), 1),
                    "addresses": sorted(entry["addresses"])[:25],
                }
            )
        return views

    def reset(self) -> None:
        with self._lock:
            self._clients.clear()


#: Process-wide registry used by the request hooks and the admin dashboard.
live_activity = LiveActivityRegistry()
