"""Network protocol statistics tools for TCP/UDP health analysis."""

from datetime import datetime, timezone
from typing import Annotated, Optional

from fastmcp import Context
from fastmcp.tools import ToolResult, tool
from mcp.types import ToolAnnotations
from pydantic import Field

from pcp_mcp.context import get_client_for_host
from pcp_mcp.icons import ICON_NETWORK, TAGS_NETWORK_STATS
from pcp_mcp.models import NetworkStatsSnapshot
from pcp_mcp.utils.builders import (
    build_interface_errors,
    build_tcp_stats,
    build_udp_stats,
)

__all__ = ["get_network_stats"]

TOOL_ANNOTATIONS = ToolAnnotations(readOnlyHint=True, openWorldHint=True)

TCP_METRICS = [
    "network.tcp.activeopens",
    "network.tcp.passiveopens",
    "network.tcp.attemptfails",
    "network.tcp.estabresets",
    "network.tcp.currestab",
    "network.tcp.retranssegs",
    "network.tcp.inerrs",
    "network.tcp.outrsts",
]

UDP_METRICS = [
    "network.udp.indatagrams",
    "network.udp.outdatagrams",
    "network.udp.inerrors",
    "network.udp.noports",
]

INTERFACE_ERROR_METRICS = [
    "network.interface.in.errors",
    "network.interface.out.errors",
    "network.interface.in.drops",
]

# All TCP/UDP metrics are counters except currestab (instant gauge)
COUNTER_METRICS = {
    "network.tcp.activeopens",
    "network.tcp.passiveopens",
    "network.tcp.attemptfails",
    "network.tcp.estabresets",
    "network.tcp.retranssegs",
    "network.tcp.inerrs",
    "network.tcp.outrsts",
    "network.udp.indatagrams",
    "network.udp.outdatagrams",
    "network.udp.inerrors",
    "network.udp.noports",
    "network.interface.in.errors",
    "network.interface.out.errors",
    "network.interface.in.drops",
}


@tool(
    annotations=TOOL_ANNOTATIONS,
    icons=[ICON_NETWORK],
    tags=TAGS_NETWORK_STATS,
    timeout=30.0,
)
async def get_network_stats(
    ctx: Context,
    sample_interval: Annotated[
        float,
        Field(
            default=1.0,
            ge=0.1,
            le=10.0,
            description="Seconds between samples for rate calculation",
        ),
    ] = 1.0,
    host: Annotated[
        Optional[str],
        Field(description="Target pmcd host to query (default: server's configured target)"),
    ] = None,
) -> ToolResult:
    """Get TCP/UDP protocol statistics and interface error rates.

    Returns protocol-level network health metrics that go deeper than
    interface throughput. Use this to diagnose connection failures,
    packet loss, retransmissions, and network errors.

    Key indicators:
    - TCP retransmits: Packet loss or network congestion
    - TCP connection failures: Unreachable services or firewall blocks
    - TCP connection resets: Peers crashing or rejecting connections
    - TCP current established: Connection count (detect leaks)
    - UDP errors: Data loss on UDP flows
    - Interface errors/drops: Hardware, driver, or buffer issues

    Use get_system_snapshot(categories=["network"]) for throughput.
    Use this tool for protocol health and error diagnosis.

    Examples:
        get_network_stats() - Full protocol stats on default host
        get_network_stats(sample_interval=2.0) - Longer sample for accuracy
        get_network_stats(host="web1.example.com") - Query remote host
    """
    from pcp_mcp.errors import handle_pcp_error

    all_metrics = TCP_METRICS + UDP_METRICS + INTERFACE_ERROR_METRICS

    async def report_progress(current: float, total: float, message: str) -> None:
        await ctx.report_progress(current, total, message)

    async with get_client_for_host(ctx, host) as client:
        try:
            data = await client.fetch_with_rates(
                all_metrics,
                COUNTER_METRICS,
                sample_interval,
                progress_callback=report_progress,
            )
        except Exception as e:
            raise handle_pcp_error(e, "fetching network stats") from e

        await ctx.report_progress(92, 100, "Building network stats...")

        tcp = build_tcp_stats(data)
        udp = build_udp_stats(data)
        iface_errors = build_interface_errors(data)

        # Build overall assessment
        assessment = _assess_network_stats(tcp, udp, iface_errors)

        await ctx.report_progress(100, 100, "Complete")

        result = NetworkStatsSnapshot(
            timestamp=datetime.now(timezone.utc).isoformat(),
            hostname=client.target_host,
            tcp=tcp,
            udp=udp,
            interface_errors=iface_errors,
            assessment=assessment,
        )
        return ToolResult(
            content=result.model_dump_json(),
            structured_content=result.model_dump(),
        )


def _assess_network_stats(tcp, udp, iface_errors) -> str:
    """Generate overall network health assessment."""
    issues = []

    if tcp.retransmits_per_sec > 100:
        issues.append(f"heavy TCP retransmissions ({tcp.retransmits_per_sec:.0f}/s)")
    elif tcp.retransmits_per_sec > 10:
        issues.append(f"moderate TCP retransmissions ({tcp.retransmits_per_sec:.0f}/s)")

    if tcp.attempt_fails_per_sec > 10:
        issues.append(f"high TCP connection failures ({tcp.attempt_fails_per_sec:.0f}/s)")

    if tcp.estab_resets_per_sec > 10:
        issues.append(f"frequent TCP resets ({tcp.estab_resets_per_sec:.0f}/s)")

    if udp.in_errors_per_sec > 10:
        issues.append(f"UDP receive errors ({udp.in_errors_per_sec:.0f}/s)")

    error_ifaces = [
        ie.interface
        for ie in iface_errors
        if ie.in_errors_per_sec > 0 or ie.out_errors_per_sec > 0 or ie.in_drops_per_sec > 0
    ]
    if error_ifaces:
        issues.append(f"interface errors on {', '.join(error_ifaces)}")

    if not issues:
        return "Network protocol health is normal"
    return "Issues detected: " + "; ".join(issues)
