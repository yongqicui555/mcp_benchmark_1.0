"""Pluggable backends — each backend implements the CronBackend ABC.

Adding a new backend:
    1. Create `backends/<your_name>.py` with a class subclassing CronBackend
    2. Register it in BACKEND_REGISTRY below
    3. Add tests in `tests/test_backend_<your_name>.py`
"""
from __future__ import annotations

from silentwatch_mcp.backends.base import CronBackend
from silentwatch_mcp.backends.crontab import CrontabBackend
from silentwatch_mcp.backends.mock import MockBackend
from silentwatch_mcp.backends.openclaw_jsonl import OpenClawJsonlBackend
from silentwatch_mcp.backends.systemd import SystemdBackend

BACKEND_REGISTRY: dict[str, type[CronBackend]] = {
    "mock": MockBackend,
    "openclaw-jsonl": OpenClawJsonlBackend,
    "crontab": CrontabBackend,
    "systemd": SystemdBackend,
}


def get_backend(name: str) -> CronBackend:
    """Resolve a backend name to a constructed instance.

    Raises ValueError if the name isn't registered.
    """
    if name not in BACKEND_REGISTRY:
        available = ", ".join(BACKEND_REGISTRY.keys())
        raise ValueError(
            f"Unknown backend '{name}'. Available: {available}. "
            "See SPEC.md § Backend selection or open a GitHub issue to request one."
        )
    return BACKEND_REGISTRY[name]()


__all__ = ["BACKEND_REGISTRY", "CronBackend", "get_backend"]
