"""Error handling: maps DRF HTTP errors to MCP isError responses."""

from __future__ import annotations

import json
from typing import Any

import httpx


class MissingAPIKeyError(Exception):
    """Raised when no API key is available for the current request.

    In HTTP transport, this means the client did not send a valid
    `Authorization: Bearer <key>` header. In stdio transport, it means
    the `YOUFILIATE_API_KEY` env var is unset.
    """


# Status code -> (message template, suggestion)
ERROR_MAP: dict[int, tuple[str, str]] = {
    401: (
        "Authentication failed",
        "Your API key may be invalid or revoked. Generate a new key at youfiliate.com/settings.",
    ),
    403: (
        "Permission denied",
        "You don't have permission to perform this action. Check your plan limits.",
    ),
    404: (
        "Resource not found",
        "Check the ID and try `youfiliate_list_smart_links` to see available links.",
    ),
    409: (
        "Conflict",
        "This resource already exists or is in a conflicting state.",
    ),
    429: (
        "Rate limit exceeded",
        "Wait a moment before retrying.",
    ),
}


def parse_drf_errors(response: httpx.Response) -> str:
    """Extract a human-readable error message from a DRF error response."""
    try:
        data = response.json()
    except (json.JSONDecodeError, ValueError):
        return response.text[:500] if response.text else "Unknown error"

    if isinstance(data, dict):
        # DRF returns {"field": ["error1", "error2"]} or {"detail": "..."}
        if "detail" in data:
            return str(data["detail"])
        parts: list[str] = []
        for field, errors in data.items():
            if isinstance(errors, list):
                parts.append(f"{field}: {', '.join(str(e) for e in errors)}")
            else:
                parts.append(f"{field}: {errors}")
        return "; ".join(parts) if parts else str(data)

    if isinstance(data, list):
        return "; ".join(str(e) for e in data)

    return str(data)


def format_error(
    status_code: int,
    detail: str = "",
    retry_after: int | None = None,
) -> str:
    """Build a user-facing error string from status code and optional detail.

    Returns a string suitable for MCP TextContent with isError=True.
    """
    if status_code in ERROR_MAP:
        message, suggestion = ERROR_MAP[status_code]
        parts = [f"Error: {message}."]
        if detail:
            parts.append(detail)
        if status_code == 429 and retry_after is not None:
            parts.append(f"Wait {retry_after} seconds before retrying.")
        else:
            parts.append(suggestion)
        return " ".join(parts)

    if 400 <= status_code < 500:
        base = f"Error: Invalid request (HTTP {status_code})."
        if detail:
            base += f" {detail}"
        return base

    if status_code >= 500:
        return "Error: Youfiliate service is temporarily unavailable. Try again in a few minutes."

    return f"Error: Unexpected response (HTTP {status_code}). {detail}"


def handle_http_error(exc: httpx.HTTPStatusError) -> str:
    """Handle an httpx HTTPStatusError and return a formatted error string."""
    detail = parse_drf_errors(exc.response)
    retry_after = None
    if exc.response.status_code == 429:
        ra = exc.response.headers.get("Retry-After")
        if ra and ra.isdigit():
            retry_after = int(ra)
    return format_error(exc.response.status_code, detail, retry_after)


def handle_request_error(exc: Exception) -> str:
    """Handle non-HTTP errors (timeout, connection, etc.)."""
    if isinstance(exc, MissingAPIKeyError):
        return (
            "Error: Authentication required. Send your Youfiliate API key via "
            "the `Authorization: Bearer <key>` header. Generate a key at "
            "youfiliate.com/settings."
        )
    if isinstance(exc, httpx.TimeoutException):
        return "Error: Request timed out. The Youfiliate API may be slow — try again."
    if isinstance(exc, httpx.ConnectError):
        return "Error: Could not connect to the Youfiliate API. Check that the service is running."
    return f"Error: Unexpected error: {type(exc).__name__}: {exc}"
