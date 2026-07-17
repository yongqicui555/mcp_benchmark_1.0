"""System health tools for clumped metric queries."""

from datetime import datetime, timezone
from typing import Annotated, Any, Literal, Optional

from fastmcp import Context
from fastmcp.tools import ToolResult, tool
from mcp.types import ToolAnnotations
from pydantic import Field

from pcp_mcp.context import get_client_for_host
from pcp_mcp.icons import (
    ICON_DIAGNOSE,
    ICON_FILESYSTEM,
    ICON_HEALTH,
    ICON_PROCESS,
    ICON_SYSTEM,
    TAGS_DIAGNOSE,
    TAGS_FILESYSTEM,
    TAGS_HEALTH,
    TAGS_PROCESS,
    TAGS_SYSTEM,
)
from pcp_mcp.models import (
    DiagnosisResult,
    FilesystemInfo,
    FilesystemSnapshot,
    ProcessTopResult,
    SystemSnapshot,
)
from pcp_mcp.utils.builders import (
    assess_processes,
    build_cpu_metrics,
    build_disk_metrics,
    build_load_metrics,
    build_memory_metrics,
    build_network_metrics,
    build_process_list,
    get_sort_key,
)
from pcp_mcp.utils.extractors import get_scalar_value

__all__ = [
    "get_system_snapshot",
    "quick_health",
    "get_process_top",
    "smart_diagnose",
    "get_filesystem_usage",
]

TOOL_ANNOTATIONS = ToolAnnotations(readOnlyHint=True, openWorldHint=True)

SNAPSHOT_METRICS = {
    "cpu": [
        "kernel.all.cpu.user",
        "kernel.all.cpu.sys",
        "kernel.all.cpu.idle",
        "kernel.all.cpu.wait.total",
        "hinv.ncpu",
    ],
    "memory": [
        "mem.physmem",
        "mem.util.used",
        "mem.util.free",
        "mem.util.available",
        "mem.util.cached",
        "mem.util.bufmem",
        "mem.util.swapTotal",
        "mem.util.swapFree",
    ],
    "load": [
        "kernel.all.load",
        "kernel.all.runnable",
        "kernel.all.nprocs",
        "hinv.ncpu",
    ],
    "disk": [
        "disk.all.read_bytes",
        "disk.all.write_bytes",
        "disk.all.read",
        "disk.all.write",
    ],
    "network": [
        "network.interface.in.bytes",
        "network.interface.out.bytes",
        "network.interface.in.packets",
        "network.interface.out.packets",
    ],
}

COUNTER_METRICS = {
    "kernel.all.cpu.user",
    "kernel.all.cpu.sys",
    "kernel.all.cpu.idle",
    "kernel.all.cpu.wait.total",
    "disk.all.read_bytes",
    "disk.all.write_bytes",
    "disk.all.read",
    "disk.all.write",
    "network.interface.in.bytes",
    "network.interface.out.bytes",
    "network.interface.in.packets",
    "network.interface.out.packets",
}

PROCESS_METRICS = {
    "cpu": ["proc.psinfo.utime", "proc.psinfo.stime"],
    "memory": ["proc.memory.rss"],
    "io": ["proc.io.read_bytes", "proc.io.write_bytes"],
    "info": ["proc.psinfo.pid", "proc.psinfo.cmd", "proc.psinfo.psargs"],
}

FILESYSTEM_METRICS = [
    "filesys.mountdir",
    "filesys.capacity",
    "filesys.used",
    "filesys.avail",
    "filesys.full",
    "filesys.type",
]


async def _fetch_system_snapshot(
    ctx: Context,
    categories: list[str],
    sample_interval: float,
    host: str | None,
) -> SystemSnapshot:
    """Core logic for fetching a system snapshot."""
    from pcp_mcp.errors import handle_pcp_error

    all_metrics: list[str] = []
    for cat in categories:
        if cat in SNAPSHOT_METRICS:
            all_metrics.extend(SNAPSHOT_METRICS[cat])

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
            raise handle_pcp_error(e, "fetching system snapshot") from e

        await ctx.report_progress(95, 100, "Building snapshot...")

        snapshot = SystemSnapshot(
            timestamp=datetime.now(timezone.utc).isoformat(),
            hostname=client.target_host,
        )

        if "cpu" in categories:
            snapshot.cpu = build_cpu_metrics(data)
        if "memory" in categories:
            snapshot.memory = build_memory_metrics(data)
        if "load" in categories:
            snapshot.load = build_load_metrics(data)
        if "disk" in categories:
            snapshot.disk = build_disk_metrics(data)
        if "network" in categories:
            snapshot.network = build_network_metrics(data)

        await ctx.report_progress(100, 100, "Complete")
        return snapshot


@tool(
    annotations=TOOL_ANNOTATIONS,
    icons=[ICON_SYSTEM],
    tags=TAGS_SYSTEM,
    timeout=30.0,
)
async def get_system_snapshot(
    ctx: Context,
    categories: Annotated[
        Optional[list[str]],
        Field(
            default=None,
            description=(
                "Categories to include: cpu, memory, disk, network, load. "
                "Defaults to all five if not specified."
            ),
        ),
    ] = None,
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
    """Get a point-in-time system health overview.

    Returns CPU, memory, disk I/O, network I/O, and load metrics in a single
    call. For rate metrics (CPU %, disk I/O, network throughput), takes two
    samples to calculate per-second rates.

    Use this tool FIRST for system troubleshooting. It automatically handles
    counter-to-rate conversion. Do NOT use query_metrics() for CPU, disk, or
    network counters - those return raw cumulative values since boot.

    Examples:
        get_system_snapshot() - Quick health check (all categories)
        get_system_snapshot(categories=["cpu", "memory"]) - CPU and memory only
        get_system_snapshot(categories=["cpu", "load"]) - CPU and load averages
        get_system_snapshot(categories=["disk", "network"]) - I/O analysis
        get_system_snapshot(host="web1.example.com") - Query remote host
    """
    if categories is None:
        categories = ["cpu", "memory", "disk", "network", "load"]
    result = await _fetch_system_snapshot(ctx, categories, sample_interval, host)
    return ToolResult(
        content=result.model_dump_json(),
        structured_content=result.model_dump(),
    )


@tool(
    annotations=TOOL_ANNOTATIONS,
    icons=[ICON_HEALTH],
    tags=TAGS_HEALTH,
    timeout=30.0,
)
async def quick_health(
    ctx: Context,
    host: Annotated[
        Optional[str],
        Field(description="Target pmcd host to query (default: server's configured target)"),
    ] = None,
) -> ToolResult:
    """Fast system health check returning only CPU and memory metrics.

    Use this for rapid status checks when you don't need disk/network/load
    details. Uses a shorter sample interval (0.5s) for faster results.

    Examples:
        quick_health() - Fast health check on default host
        quick_health(host="web1.example.com") - Fast check on remote host
    """
    result = await _fetch_system_snapshot(ctx, ["cpu", "memory"], 0.5, host)
    return ToolResult(
        content=result.model_dump_json(),
        structured_content=result.model_dump(),
    )


@tool(
    annotations=TOOL_ANNOTATIONS,
    icons=[ICON_PROCESS],
    tags=TAGS_PROCESS,
    timeout=30.0,
)
async def get_process_top(
    ctx: Context,
    sort_by: Annotated[
        Literal["cpu", "memory", "io"],
        Field(description="Resource to sort by"),
    ] = "cpu",
    limit: Annotated[
        int,
        Field(default=10, ge=1, le=50, description="Number of processes to return"),
    ] = 10,
    sample_interval: Annotated[
        float,
        Field(
            default=1.0,
            ge=0.5,
            le=5.0,
            description="Seconds to sample for CPU/IO rates",
        ),
    ] = 1.0,
    host: Annotated[
        Optional[str],
        Field(description="Target pmcd host to query (default: server's configured target)"),
    ] = None,
) -> ToolResult:
    """Get top processes by resource consumption.

    For CPU and I/O, takes two samples to calculate rates. Memory is instantaneous.
    Returns the top N processes sorted by the requested resource.

    Examples:
        get_process_top() - Top 10 by CPU (default)
        get_process_top(sort_by="memory", limit=20) - Top 20 memory consumers
        get_process_top(sort_by="io", sample_interval=2.0) - Top I/O with longer sample
        get_process_top(host="db1.example.com") - Query remote host
    """
    all_metrics = (
        PROCESS_METRICS["info"] + PROCESS_METRICS["memory"] + PROCESS_METRICS.get(sort_by, [])
    )
    if sort_by == "cpu":
        all_metrics.extend(PROCESS_METRICS["cpu"])
    elif sort_by == "io":
        all_metrics.extend(PROCESS_METRICS["io"])

    all_metrics = list(set(all_metrics))
    system_metrics = ["hinv.ncpu", "mem.physmem"]

    counter_metrics = {
        "proc.psinfo.utime",
        "proc.psinfo.stime",
        "proc.io.read_bytes",
        "proc.io.write_bytes",
    }

    from pcp_mcp.errors import handle_pcp_error

    async def report_progress(current: float, total: float, message: str) -> None:
        await ctx.report_progress(current, total, message)

    async with get_client_for_host(ctx, host) as client:
        try:
            proc_data = await client.fetch_with_rates(
                all_metrics, counter_metrics, sample_interval, progress_callback=report_progress
            )
            sys_data = await client.fetch(system_metrics)
        except Exception as e:
            raise handle_pcp_error(e, "fetching process data") from e

        await ctx.report_progress(92, 100, "Processing results...")

        ncpu = get_scalar_value(sys_data, "hinv.ncpu", 1)
        total_mem = get_scalar_value(sys_data, "mem.physmem", 1) * 1024

        processes = build_process_list(proc_data, sort_by, total_mem, ncpu)
        processes.sort(key=lambda p: get_sort_key(p, sort_by), reverse=True)
        processes = processes[:limit]

        assessment = assess_processes(processes, sort_by, ncpu)

        await ctx.report_progress(100, 100, "Complete")
        result = ProcessTopResult(
            timestamp=datetime.now(timezone.utc).isoformat(),
            hostname=client.target_host,
            sort_by=sort_by,
            sample_interval=sample_interval,
            processes=processes,
            total_memory_bytes=int(total_mem),
            ncpu=ncpu,
            assessment=assessment,
        )
        return ToolResult(
            content=result.model_dump_json(),
            structured_content=result.model_dump(),
        )


@tool(
    annotations=TOOL_ANNOTATIONS,
    icons=[ICON_DIAGNOSE],
    tags=TAGS_DIAGNOSE,
    timeout=30.0,
)
async def smart_diagnose(
    ctx: Context,
    host: Annotated[
        Optional[str],
        Field(description="Target pmcd host to query (default: server's configured target)"),
    ] = None,
) -> ToolResult:
    """Use LLM to analyze system metrics and provide diagnosis.

    Collects a quick system snapshot (CPU, memory, load) and asks the
    connected LLM to analyze the metrics and provide actionable insights.

    This tool demonstrates FastMCP's LLM sampling capability, where the
    MCP server can request LLM assistance for complex analysis tasks.

    Examples:
        smart_diagnose() - Analyze default host
        smart_diagnose(host="db1.example.com") - Analyze remote host
    """
    from pcp_mcp.errors import handle_pcp_error

    try:
        snapshot = await _fetch_system_snapshot(ctx, ["cpu", "memory", "load"], 0.5, host)
    except Exception as e:
        raise handle_pcp_error(e, "fetching metrics for diagnosis") from e

    metrics_summary = _format_snapshot_for_llm(snapshot)

    system_prompt = (
        "You are a system performance analyst. Analyze the metrics and provide:\n"
        "1. A brief diagnosis (2-3 sentences)\n"
        "2. A severity level: 'healthy', 'warning', or 'critical'\n"
        "3. Up to 3 actionable recommendations\n\n"
        "Be concise and focus on actionable insights."
    )

    try:
        sampling_result = await ctx.sample(
            messages=f"Analyze these system metrics:\n\n{metrics_summary}",
            system_prompt=system_prompt,
            max_tokens=500,
            result_type=DiagnosisResult,
        )
        result = sampling_result.result
        result.timestamp = snapshot.timestamp
        result.hostname = snapshot.hostname
        return ToolResult(
            content=result.model_dump_json(),
            structured_content=result.model_dump(),
        )
    except Exception:
        result = _build_fallback_diagnosis(snapshot)
        return ToolResult(
            content=result.model_dump_json(),
            structured_content=result.model_dump(),
        )


@tool(
    annotations=TOOL_ANNOTATIONS,
    icons=[ICON_FILESYSTEM],
    tags=TAGS_FILESYSTEM,
    timeout=30.0,
)
async def get_filesystem_usage(
    ctx: Context,
    host: Annotated[
        Optional[str],
        Field(description="Target pmcd host to query (default: server's configured target)"),
    ] = None,
) -> ToolResult:
    """Get mounted filesystem usage (similar to df command).

    Returns capacity, used, available, and percent full for each mounted
    filesystem. Useful for monitoring disk space and identifying filesystems
    that may need attention.

    Examples:
        get_filesystem_usage() - Check all filesystems on default host
        get_filesystem_usage(host="db1.example.com") - Check remote host
    """
    from pcp_mcp.errors import handle_pcp_error

    async with get_client_for_host(ctx, host) as client:
        try:
            response = await client.fetch(FILESYSTEM_METRICS)
        except Exception as e:
            raise handle_pcp_error(e, "fetching filesystem metrics") from e

        filesystems = _build_filesystem_list(response)
        assessment = _assess_filesystems(filesystems)

        result = FilesystemSnapshot(
            timestamp=datetime.now(timezone.utc).isoformat(),
            hostname=client.target_host,
            filesystems=filesystems,
            assessment=assessment,
        )
        return ToolResult(
            content=result.model_dump_json(),
            structured_content=result.model_dump(),
        )


def _build_filesystem_list(response: dict) -> list[FilesystemInfo]:
    """Build list of FilesystemInfo from pmproxy response."""
    values = response.get("values", [])

    metrics_by_name: dict[str, dict[int, Any]] = {}
    for metric in values:
        name = metric.get("name", "")
        instances = metric.get("instances", [])
        metrics_by_name[name] = {inst.get("instance", -1): inst.get("value") for inst in instances}

    mountdir_instances = metrics_by_name.get("filesys.mountdir", {})

    filesystems: list[FilesystemInfo] = []
    for instance_id, mount_point in mountdir_instances.items():
        if mount_point is None:
            continue

        capacity_kb = metrics_by_name.get("filesys.capacity", {}).get(instance_id, 0) or 0
        used_kb = metrics_by_name.get("filesys.used", {}).get(instance_id, 0) or 0
        avail_kb = metrics_by_name.get("filesys.avail", {}).get(instance_id, 0) or 0
        percent_full = metrics_by_name.get("filesys.full", {}).get(instance_id, 0.0) or 0.0
        fs_type = metrics_by_name.get("filesys.type", {}).get(instance_id, "unknown") or "unknown"

        filesystems.append(
            FilesystemInfo(
                mount_point=mount_point,
                fs_type=fs_type,
                capacity_bytes=int(capacity_kb) * 1024,
                used_bytes=int(used_kb) * 1024,
                available_bytes=int(avail_kb) * 1024,
                percent_full=float(percent_full),
            )
        )

    filesystems.sort(key=lambda fs: fs.mount_point)
    return filesystems


def _assess_filesystems(filesystems: list[FilesystemInfo]) -> str:
    """Generate assessment string for filesystem state."""
    if not filesystems:
        return "No filesystems found"

    critical = [fs for fs in filesystems if fs.percent_full >= 90]
    warning = [fs for fs in filesystems if 80 <= fs.percent_full < 90]

    if critical:
        mounts = ", ".join(fs.mount_point for fs in critical)
        return f"🔴 Critical: {mounts} at 90%+ capacity"
    if warning:
        mounts = ", ".join(fs.mount_point for fs in warning)
        return f"🟡 Warning: {mounts} at 80%+ capacity"
    return "🟢 All filesystems healthy"


def _format_snapshot_for_llm(snapshot: SystemSnapshot) -> str:
    """Format a system snapshot as text for LLM analysis."""
    lines = [f"Host: {snapshot.hostname}", f"Time: {snapshot.timestamp}", ""]

    if snapshot.cpu:
        lines.extend(
            [
                "CPU:",
                f"  User: {snapshot.cpu.user_percent:.1f}%",
                f"  System: {snapshot.cpu.system_percent:.1f}%",
                f"  Idle: {snapshot.cpu.idle_percent:.1f}%",
                f"  I/O Wait: {snapshot.cpu.iowait_percent:.1f}%",
                f"  CPUs: {snapshot.cpu.ncpu}",
                "",
            ]
        )

    if snapshot.memory:
        total_gb = snapshot.memory.total_bytes / (1024**3)
        avail_gb = snapshot.memory.available_bytes / (1024**3)
        lines.extend(
            [
                "Memory:",
                f"  Total: {total_gb:.1f} GB",
                f"  Available: {avail_gb:.1f} GB",
                f"  Used: {snapshot.memory.used_percent:.1f}%",
                f"  Swap Used: {snapshot.memory.swap_used_bytes / (1024**3):.1f} GB",
                "",
            ]
        )

    if snapshot.load:
        lines.extend(
            [
                "Load:",
                f"  1m/5m/15m: {snapshot.load.load_1m:.2f} / "
                f"{snapshot.load.load_5m:.2f} / {snapshot.load.load_15m:.2f}",
                f"  Runnable: {snapshot.load.runnable}",
                f"  Total procs: {snapshot.load.nprocs}",
            ]
        )

    return "\n".join(lines)


def _build_fallback_diagnosis(snapshot: SystemSnapshot) -> DiagnosisResult:
    """Build a basic diagnosis when LLM sampling isn't available."""
    issues: list[str] = []
    recommendations: list[str] = []
    severity = "healthy"

    if snapshot.cpu:
        cpu_busy = 100 - snapshot.cpu.idle_percent
        if cpu_busy > 90:
            issues.append(f"CPU is heavily loaded ({cpu_busy:.0f}% busy)")
            recommendations.append("Identify high-CPU processes with get_process_top")
            severity = "critical"
        elif cpu_busy > 70:
            issues.append(f"CPU moderately busy ({cpu_busy:.0f}%)")
            severity = "warning" if severity == "healthy" else severity

    if snapshot.memory:
        if snapshot.memory.used_percent > 90:
            issues.append(f"Memory pressure high ({snapshot.memory.used_percent:.0f}% used)")
            recommendations.append("Check for memory leaks or increase RAM")
            severity = "critical"
        elif snapshot.memory.used_percent > 75:
            issues.append(f"Memory usage elevated ({snapshot.memory.used_percent:.0f}%)")
            severity = "warning" if severity == "healthy" else severity

    if snapshot.load and snapshot.cpu:
        load_per_cpu = snapshot.load.load_1m / snapshot.cpu.ncpu
        if load_per_cpu > 2.0:
            issues.append(
                f"Load very high ({snapshot.load.load_1m:.1f} for {snapshot.cpu.ncpu} CPUs)"
            )
            recommendations.append("Reduce concurrent workload or add capacity")
            severity = "critical"
        elif load_per_cpu > 1.0:
            issues.append(f"Load elevated ({snapshot.load.load_1m:.1f})")
            severity = "warning" if severity == "healthy" else severity

    if not issues:
        diagnosis = "System is operating normally. No issues detected."
    else:
        diagnosis = " ".join(issues)

    if not recommendations:
        recommendations = ["Continue monitoring"]

    return DiagnosisResult(
        timestamp=snapshot.timestamp,
        hostname=snapshot.hostname,
        diagnosis=diagnosis,
        severity=severity,
        recommendations=recommendations,
    )
