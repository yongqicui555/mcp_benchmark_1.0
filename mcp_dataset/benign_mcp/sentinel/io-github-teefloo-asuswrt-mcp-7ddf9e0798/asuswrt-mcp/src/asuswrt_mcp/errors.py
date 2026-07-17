"""Domain errors converted to MCP tool responses."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class AsusWrtMcpError(Exception):
    """Base error with a stable public error code."""

    code: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return self.message


class ConfigurationError(AsusWrtMcpError):
    """Raised when required router configuration is missing."""


class MutationBlockedError(AsusWrtMcpError):
    """Raised when a mutating tool is not explicitly allowed."""


class UnsupportedOperationError(AsusWrtMcpError):
    """Raised when a router/library capability is unavailable."""


class RouterOperationError(AsusWrtMcpError):
    """Raised when a router operation fails."""

