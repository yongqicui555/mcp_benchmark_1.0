"""Diagnostic prompts for guided troubleshooting workflows."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pcp_mcp.prompts.cpu import analyze_cpu_usage
from pcp_mcp.prompts.diagnose import diagnose_slow_system
from pcp_mcp.prompts.disk import find_io_bottleneck
from pcp_mcp.prompts.memory import investigate_memory_usage
from pcp_mcp.prompts.network import check_network_performance

if TYPE_CHECKING:
    from fastmcp import FastMCP

__all__ = [
    "diagnose_slow_system",
    "investigate_memory_usage",
    "find_io_bottleneck",
    "analyze_cpu_usage",
    "check_network_performance",
    "register_prompts",
]


def register_prompts(mcp: FastMCP) -> None:
    """Register all prompts with the MCP server.

    Args:
        mcp: The FastMCP server instance.
    """
    mcp.add_prompt(diagnose_slow_system)
    mcp.add_prompt(investigate_memory_usage)
    mcp.add_prompt(find_io_bottleneck)
    mcp.add_prompt(analyze_cpu_usage)
    mcp.add_prompt(check_network_performance)
