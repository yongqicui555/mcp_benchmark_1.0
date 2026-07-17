"""Error mapping from httpx to MCP ToolErrors."""

from __future__ import annotations

import httpx
from fastmcp.exceptions import ToolError


class PCPError(Exception):
    """Base PCP error."""


class PCPConnectionError(PCPError):
    """Cannot connect to pmproxy."""


class PCPMetricNotFoundError(PCPError):
    """Metric does not exist."""


def handle_pcp_error(e: Exception, operation: str) -> ToolError:
    """Convert PCP/httpx exceptions to MCP ToolErrors.

    Uses isinstance() checks instead of match/case class patterns for resilience
    against module reloading (e.g., FastMCP's FileSystemProvider), which can
    create different class identities that break structural pattern matching.

    Args:
        e: The exception to convert.
        operation: Description of the operation that failed.

    Returns:
        A ToolError with an appropriate message.
    """
    if isinstance(e, httpx.ConnectError):
        return ToolError("Cannot connect to pmproxy. Is it running? (systemctl start pmproxy)")

    if isinstance(e, httpx.HTTPStatusError):
        if e.response.status_code == 400:
            return ToolError(f"Bad request during {operation}: {e.response.text}")
        if e.response.status_code == 404:
            return ToolError(f"Metric not found during {operation}")
        return ToolError(f"pmproxy error ({e.response.status_code}): {e.response.text}")

    if isinstance(e, httpx.TimeoutException):
        return ToolError(f"Request timed out during {operation}")

    if isinstance(e, PCPMetricNotFoundError):
        return ToolError(f"Metric not found: {e}")

    if isinstance(e, PCPConnectionError):
        return ToolError(str(e))

    return ToolError(f"Error during {operation}: {e}")
