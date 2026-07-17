"""Smoke tests for server startup and tool registration.

These tests verify that the server can start and tools register correctly,
catching registration-time failures like missing imports or type errors.
Uses FastMCP's public Client API with a mock lifespan to avoid pmproxy dependency.
"""

from __future__ import annotations

import pytest
from fastmcp import Client, FastMCP

from pcp_mcp.server import create_server


class TestServerSmoke:
    """Smoke tests for server initialization and tool discovery."""

    def test_server_creates_successfully(self) -> None:
        """Server creation should not raise any exceptions."""
        server = create_server()
        assert server is not None
        assert server.name == "pcp"

    @pytest.mark.asyncio
    async def test_tools_are_registered(self, smoke_test_server: FastMCP) -> None:
        """All expected tools should be registered."""
        async with Client(smoke_test_server) as client:
            tools = await client.list_tools()
            tool_names = {t.name for t in tools}

        expected_tools = {
            "query_metrics",
            "search_metrics",
            "describe_metric",
            "get_system_snapshot",
            "get_process_top",
            "quick_health",
            "smart_diagnose",
        }

        missing = expected_tools - tool_names
        assert not missing, f"Missing tools: {missing}"

    @pytest.mark.asyncio
    async def test_prompts_are_registered(self, smoke_test_server: FastMCP) -> None:
        """All expected prompts should be registered."""
        async with Client(smoke_test_server) as client:
            prompts = await client.list_prompts()
            prompt_names = {p.name for p in prompts}

        expected_prompts = {
            "diagnose_slow_system",
            "investigate_memory_usage",
            "find_io_bottleneck",
            "analyze_cpu_usage",
            "check_network_performance",
        }

        missing = expected_prompts - prompt_names
        assert not missing, f"Missing prompts: {missing}"

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "tool_name",
        [
            "query_metrics",
            "search_metrics",
            "describe_metric",
            "get_system_snapshot",
            "get_process_top",
            "quick_health",
            "smart_diagnose",
        ],
    )
    async def test_tool_has_valid_schema(self, smoke_test_server: FastMCP, tool_name: str) -> None:
        """Each tool should have a valid input schema."""
        async with Client(smoke_test_server) as client:
            tools = await client.list_tools()
            tools_dict = {t.name: t for t in tools}

        tool = tools_dict.get(tool_name)
        assert tool is not None, f"Tool {tool_name} not found"
        assert tool.inputSchema is not None, f"Tool {tool_name} has no input schema"
