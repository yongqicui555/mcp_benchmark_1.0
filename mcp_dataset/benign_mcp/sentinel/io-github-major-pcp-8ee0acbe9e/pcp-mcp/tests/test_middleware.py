"""Tests for custom middleware."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from pcp_mcp.middleware import CACHEABLE_TOOLS, MetricCacheMiddleware


@pytest.fixture
def middleware() -> MetricCacheMiddleware:
    return MetricCacheMiddleware(ttl_seconds=60)


@pytest.fixture
def mock_context() -> MagicMock:
    ctx = MagicMock()
    ctx.message = MagicMock()
    ctx.message.name = "describe_metric"
    ctx.message.arguments = {"name": "kernel.all.load"}
    return ctx


@pytest.fixture
def mock_call_next() -> AsyncMock:
    call_next = AsyncMock()
    call_next.return_value = MagicMock(content="cached result")
    return call_next


class TestMetricCacheMiddleware:
    async def test_caches_describe_metric(
        self,
        middleware: MetricCacheMiddleware,
        mock_context: MagicMock,
        mock_call_next: AsyncMock,
    ) -> None:
        result1 = await middleware.on_call_tool(mock_context, mock_call_next)
        result2 = await middleware.on_call_tool(mock_context, mock_call_next)

        assert mock_call_next.call_count == 1
        assert result1 == result2
        assert middleware.cache_size == 1

    async def test_caches_search_metrics(
        self,
        middleware: MetricCacheMiddleware,
        mock_context: MagicMock,
        mock_call_next: AsyncMock,
    ) -> None:
        mock_context.message.name = "search_metrics"
        mock_context.message.arguments = {"pattern": "kernel"}

        await middleware.on_call_tool(mock_context, mock_call_next)
        await middleware.on_call_tool(mock_context, mock_call_next)

        assert mock_call_next.call_count == 1

    async def test_skips_non_cacheable_tools(
        self,
        middleware: MetricCacheMiddleware,
        mock_context: MagicMock,
        mock_call_next: AsyncMock,
    ) -> None:
        mock_context.message.name = "get_system_snapshot"

        await middleware.on_call_tool(mock_context, mock_call_next)
        await middleware.on_call_tool(mock_context, mock_call_next)

        assert mock_call_next.call_count == 2
        assert middleware.cache_size == 0

    async def test_skips_cache_with_host_param(
        self,
        middleware: MetricCacheMiddleware,
        mock_context: MagicMock,
        mock_call_next: AsyncMock,
    ) -> None:
        mock_context.message.arguments = {"name": "kernel.all.load", "host": "remote.example.com"}

        await middleware.on_call_tool(mock_context, mock_call_next)
        await middleware.on_call_tool(mock_context, mock_call_next)

        assert mock_call_next.call_count == 2
        assert middleware.cache_size == 0

    async def test_expires_old_entries(
        self,
        mock_context: MagicMock,
        mock_call_next: AsyncMock,
    ) -> None:
        middleware = MetricCacheMiddleware(ttl_seconds=0)

        await middleware.on_call_tool(mock_context, mock_call_next)

        await asyncio.sleep(0.01)

        await middleware.on_call_tool(mock_context, mock_call_next)

        assert mock_call_next.call_count == 2

    async def test_different_args_have_different_cache_keys(
        self,
        middleware: MetricCacheMiddleware,
        mock_context: MagicMock,
        mock_call_next: AsyncMock,
    ) -> None:
        mock_context.message.arguments = {"name": "kernel.all.load"}
        await middleware.on_call_tool(mock_context, mock_call_next)

        mock_context.message.arguments = {"name": "mem.physmem"}
        await middleware.on_call_tool(mock_context, mock_call_next)

        assert mock_call_next.call_count == 2
        assert middleware.cache_size == 2

    def test_clear_cache(self, middleware: MetricCacheMiddleware) -> None:
        middleware._cache["key1"] = MagicMock()
        middleware._cache["key2"] = MagicMock()

        assert middleware.cache_size == 2
        middleware.clear_cache()
        assert middleware.cache_size == 0

    @pytest.mark.parametrize("tool_name", list(CACHEABLE_TOOLS))
    async def test_all_cacheable_tools_are_cached(
        self,
        middleware: MetricCacheMiddleware,
        mock_context: MagicMock,
        mock_call_next: AsyncMock,
        tool_name: str,
    ) -> None:
        mock_context.message.name = tool_name

        await middleware.on_call_tool(mock_context, mock_call_next)
        await middleware.on_call_tool(mock_context, mock_call_next)

        assert mock_call_next.call_count == 1

    async def test_evicts_lru_when_maxsize_reached(
        self,
        mock_context: MagicMock,
        mock_call_next: AsyncMock,
    ) -> None:
        middleware = MetricCacheMiddleware(ttl_seconds=60, maxsize=2)

        mock_context.message.arguments = {"name": "metric1"}
        await middleware.on_call_tool(mock_context, mock_call_next)

        mock_context.message.arguments = {"name": "metric2"}
        await middleware.on_call_tool(mock_context, mock_call_next)

        mock_context.message.arguments = {"name": "metric3"}
        await middleware.on_call_tool(mock_context, mock_call_next)

        assert middleware.cache_size == 2
        assert mock_call_next.call_count == 3
