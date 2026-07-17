"""FastMCP server setup and lifespan management."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastmcp import FastMCP
from fastmcp.server.middleware.logging import StructuredLoggingMiddleware
from fastmcp.server.providers import FileSystemProvider

from pcp_mcp.client import PCPClient
from pcp_mcp.config import PCPMCPSettings
from pcp_mcp.middleware import MetricCacheMiddleware


@asynccontextmanager
async def lifespan(mcp: FastMCP) -> AsyncIterator[dict[str, Any]]:
    """Manage PCPClient lifecycle.

    Creates a PCPClient for the duration of the server's lifetime,
    making it available to all tools and resources via the context.

    Args:
        mcp: The FastMCP server instance.

    Yields:
        Context dict with client and settings.
    """
    settings = PCPMCPSettings()

    async with PCPClient(
        base_url=settings.base_url,
        target_host=settings.target_host,
        auth=settings.auth,
        timeout=settings.timeout,
        verify=settings.verify,
    ) as client:
        yield {
            "client": client,
            "settings": settings,
        }


def create_server() -> FastMCP:
    """Create and configure the MCP server.

    Returns:
        Configured FastMCP server instance.
    """
    settings = PCPMCPSettings()

    mcp = FastMCP(
        name="pcp",
        instructions=f"""PCP MCP Server - Performance Co-Pilot Metrics

Monitoring target: {settings.target_host}
pmproxy endpoint: {settings.base_url}

🎯 QUICK START GUIDE FOR LLMs

Common troubleshooting workflows:
- "System is slow" → get_system_snapshot(categories=["cpu", "load", "memory"])
- "High CPU usage" → get_process_top(sort_by="cpu") + query_metrics(["kernel.all.cpu.*"])
- "Memory pressure" → get_system_snapshot(categories=["memory"]) + search_metrics("mem.util")
- "Disk I/O issues" → get_system_snapshot(categories=["disk"]) + search_metrics("disk.dev")
- "Network saturation" → get_system_snapshot(categories=["network"]) +
  search_metrics("network.interface")

📊 METRIC NAMESPACE GUIDE

Key prefixes and what they measure:
- kernel.all.*    → System-wide aggregates (load, CPU totals, interrupts)
- mem.*           → Memory utilization (physmem, swap, buffers, cache)
- disk.*          → Disk I/O (disk.all.* for totals, disk.dev.* per-device)
- network.*       → Network I/O (network.interface.* per-interface)
- proc.*          → Per-process metrics (use get_process_top instead of raw queries)
- hinv.*          → Hardware inventory (ncpu, physmem, machine type)
- pmcd.*          → PCP daemon health (agent status, timeouts)
- cgroup.*        → Container/cgroup metrics (requires cgroups PMDA)

⚠️ COUNTER METRICS WARNING

These metrics are CUMULATIVE (values since boot):
- kernel.all.cpu.*
- disk.all.read_bytes, disk.all.write_bytes
- network.interface.in.bytes, network.interface.out.bytes
- proc.psinfo.utime, proc.psinfo.stime
- proc.io.read_bytes, proc.io.write_bytes

For meaningful rates, use:
- get_system_snapshot (handles rate calculation automatically)
- get_process_top (handles rate calculation automatically)

DO NOT query these directly with query_metrics expecting per-second rates!

🔍 DISCOVERY WORKFLOW

1. Start broad: get_system_snapshot() or get_process_top()
2. Drill down: search_metrics("prefix") to find specific metrics
3. Investigate: describe_metric("full.metric.name") for units/semantics
4. Query: query_metrics(["name1", "name2"]) for raw values (non-counters only)

Tools:
- query_metrics: Fetch specific metrics by name (use for instant/gauge metrics)
- search_metrics: Find metrics matching a pattern (e.g., 'kernel.all', 'mem')
- describe_metric: Get metadata for a metric (type, units, help text)
- get_system_snapshot: System overview (CPU, memory, disk, network) - USE THIS FIRST
- get_process_top: Top processes by resource consumption

Prompts (invoke for guided troubleshooting workflows):
- diagnose_slow_system: Complete slowness investigation
- investigate_memory_usage: Memory pressure analysis
- find_io_bottleneck: Disk I/O troubleshooting
- analyze_cpu_usage: CPU utilization analysis
- check_network_performance: Network saturation detection
""",
        lifespan=lifespan,
    )

    mcp.add_middleware(
        StructuredLoggingMiddleware(
            include_payload_length=True,
            estimate_payload_tokens=True,
        )
    )
    mcp.add_middleware(MetricCacheMiddleware())

    # Auto-discover tools and prompts from filesystem
    base_dir = Path(__file__).parent
    provider = FileSystemProvider(
        root=base_dir,
        reload=False,
    )
    mcp.add_provider(provider)

    return mcp
