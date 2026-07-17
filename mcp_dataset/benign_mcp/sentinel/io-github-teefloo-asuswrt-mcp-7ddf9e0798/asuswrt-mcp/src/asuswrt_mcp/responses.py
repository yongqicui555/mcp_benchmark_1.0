"""Structured tool response helpers."""

from __future__ import annotations

from typing import Any

from .errors import AsusWrtMcpError
from .serialization import safe_data


def tool_ok(
    operation: str,
    *,
    changed: bool = False,
    dry_run: bool = False,
    data: Any | None = None,
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "ok": True,
        "operation": operation,
        "changed": changed,
        "dry_run": dry_run,
        "data": safe_data({} if data is None else data),
        "warnings": warnings or [],
        "error": None,
    }


def tool_error(
    operation: str,
    error: Exception,
    *,
    dry_run: bool = False,
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    if isinstance(error, AsusWrtMcpError):
        public_error = {
            "code": error.code,
            "message": error.message,
            "details": safe_data(error.details),
        }
    else:
        public_error = {
            "code": "unexpected_error",
            "message": str(error),
            "details": {},
        }

    return {
        "ok": False,
        "operation": operation,
        "changed": False,
        "dry_run": dry_run,
        "data": {},
        "warnings": warnings or [],
        "error": public_error,
    }
