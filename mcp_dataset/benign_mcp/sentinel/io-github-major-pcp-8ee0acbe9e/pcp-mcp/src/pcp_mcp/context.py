"""Context helpers for safe lifespan context access."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from fastmcp import Context
from fastmcp.exceptions import ToolError

from pcp_mcp.client import PCPClient

if TYPE_CHECKING:
    from pcp_mcp.config import PCPMCPSettings


def _validate_context(ctx: Context) -> None:
    """Validate context has lifespan_context available.

    Args:
        ctx: MCP context.

    Raises:
        ToolError: If context is not available.
    """
    if ctx.request_context is None or ctx.request_context.lifespan_context is None:
        raise ToolError("Server context not available")


def get_client(ctx: Context) -> PCPClient:
    """Get PCPClient from context.

    Args:
        ctx: MCP context.

    Returns:
        The PCPClient instance.

    Raises:
        ToolError: If context is not available.
    """
    _validate_context(ctx)
    assert ctx.request_context is not None
    assert ctx.request_context.lifespan_context is not None
    return ctx.request_context.lifespan_context["client"]


def get_settings(ctx: Context) -> PCPMCPSettings:
    """Get settings from context.

    Args:
        ctx: MCP context.

    Returns:
        The PCPMCPSettings instance.

    Raises:
        ToolError: If context is not available.
    """
    _validate_context(ctx)
    assert ctx.request_context is not None
    assert ctx.request_context.lifespan_context is not None
    return ctx.request_context.lifespan_context["settings"]


@asynccontextmanager
async def get_client_for_host(ctx: Context, host: str | None = None) -> AsyncIterator[PCPClient]:
    """Get a PCPClient for the specified host.

    If host is None or matches the configured target_host, yields the existing
    lifespan client. Otherwise, creates a new ad-hoc client for the specified
    hostspec and cleans it up on exit.

    Args:
        ctx: MCP context.
        host: Target pmcd hostspec to query. None uses the default.

    Yields:
        PCPClient connected to the specified host.

    Raises:
        ToolError: If context is not available, host is not allowed, or host is unreachable.
    """
    settings = get_settings(ctx)

    if host is None or host == settings.target_host:
        yield get_client(ctx)
        return

    if not settings.is_host_allowed(host):
        raise ToolError(
            f"Host '{host}' is not in the allowed hosts list. "
            f"Configure PCP_ALLOWED_HOSTS to permit additional hosts."
        )

    async with PCPClient(
        base_url=settings.base_url,
        target_host=host,
        auth=settings.auth,
        timeout=settings.timeout,
        verify=settings.verify,
    ) as client:
        yield client
