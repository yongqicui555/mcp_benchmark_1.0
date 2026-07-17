"""Custom middleware for pcp-mcp server."""

from __future__ import annotations

from typing import TYPE_CHECKING

from cachetools import TTLCache
from fastmcp.server.middleware import Middleware
from fastmcp.tools import ToolResult

if TYPE_CHECKING:
    from fastmcp.server.middleware.middleware import CallNext, MiddlewareContext
    from mcp import types as mt


CACHEABLE_TOOLS = frozenset({"describe_metric", "search_metrics"})
DEFAULT_TTL_SECONDS = 300
DEFAULT_MAX_SIZE = 100


class MetricCacheMiddleware(Middleware):
    """Cache responses for describe_metric and search_metrics tools.

    These tools query PCP metric metadata which changes infrequently.
    Caching reduces pmproxy load and improves LLM response times.
    """

    def __init__(
        self, ttl_seconds: int = DEFAULT_TTL_SECONDS, maxsize: int = DEFAULT_MAX_SIZE
    ) -> None:
        """Initialize the cache middleware.

        Args:
            ttl_seconds: Time-to-live for cached entries in seconds.
            maxsize: Maximum number of entries in the cache.
        """
        self._cache: TTLCache[str, ToolResult] = TTLCache(maxsize=maxsize, ttl=ttl_seconds)

    def _make_cache_key(self, tool_name: str, arguments: dict | None) -> str:
        args_str = str(sorted((arguments or {}).items()))
        return f"{tool_name}:{args_str}"

    async def on_call_tool(
        self,
        context: MiddlewareContext[mt.CallToolRequestParams],
        call_next: CallNext[mt.CallToolRequestParams, ToolResult],
    ) -> ToolResult:
        """Intercept tool calls and cache describe_metric/search_metrics responses."""
        tool_name = context.message.name
        arguments = context.message.arguments

        if tool_name not in CACHEABLE_TOOLS:
            return await call_next(context)

        if arguments and arguments.get("host"):
            return await call_next(context)

        cache_key = self._make_cache_key(tool_name, arguments)

        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        result = await call_next(context)
        self._cache[cache_key] = result
        return result

    @property
    def cache_size(self) -> int:
        """Number of entries in the cache."""
        return len(self._cache)

    def clear_cache(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()
