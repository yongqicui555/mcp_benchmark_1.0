"""Metric transformation and builder functions.

Consolidated metric builders extracted from tools/system.py to follow DRY principles.
"""

from __future__ import annotations

from pcp_mcp.models import (
    CPUMetrics,
    DiskMetrics,
    InterfaceErrors,
    LoadMetrics,
    MemoryMetrics,
    NetworkMetrics,
    ProcessInfo,
    TCPStats,
    UDPStats,
)
from pcp_mcp.utils.extractors import get_first_value, sum_instances


def build_cpu_metrics(data: dict) -> CPUMetrics:
    """Build CPU metrics from fetched data."""
    user = get_first_value(data, "kernel.all.cpu.user")
    sys = get_first_value(data, "kernel.all.cpu.sys")
    idle = get_first_value(data, "kernel.all.cpu.idle")
    iowait = get_first_value(data, "kernel.all.cpu.wait.total")
    ncpu = int(get_first_value(data, "hinv.ncpu", 1))

    total = user + sys + idle + iowait
    if total > 0:
        user_pct = (user / total) * 100
        sys_pct = (sys / total) * 100
        idle_pct = (idle / total) * 100
        iowait_pct = (iowait / total) * 100
    else:
        user_pct = sys_pct = idle_pct = iowait_pct = 0.0

    if iowait_pct > 20:
        assessment = "High I/O wait - system is disk bound"
    elif idle_pct < 10:
        assessment = "CPU is saturated"
    elif user_pct > 70:
        assessment = "CPU bound on user processes"
    elif sys_pct > 30:
        assessment = "High system/kernel CPU usage"
    else:
        assessment = "CPU utilization is normal"

    return CPUMetrics(
        user_percent=round(user_pct, 1),
        system_percent=round(sys_pct, 1),
        idle_percent=round(idle_pct, 1),
        iowait_percent=round(iowait_pct, 1),
        ncpu=ncpu,
        assessment=assessment,
    )


def build_memory_metrics(data: dict) -> MemoryMetrics:
    """Build memory metrics from fetched data."""
    total = int(get_first_value(data, "mem.physmem")) * 1024
    available = int(get_first_value(data, "mem.util.available")) * 1024
    free = int(get_first_value(data, "mem.util.free")) * 1024
    cached = int(get_first_value(data, "mem.util.cached")) * 1024
    buffers = int(get_first_value(data, "mem.util.bufmem")) * 1024
    swap_total = int(get_first_value(data, "mem.util.swapTotal")) * 1024
    swap_free = int(get_first_value(data, "mem.util.swapFree")) * 1024
    swap_used = swap_total - swap_free

    used = total - available
    used_pct = (used / total * 100) if total > 0 else 0.0

    if swap_used > swap_total * 0.5:
        assessment = "Heavy swap usage - memory pressure"
    elif used_pct > 90:
        assessment = "Memory usage is critical"
    elif used_pct > 75:
        assessment = "Memory usage is elevated"
    else:
        assessment = "Memory utilization is normal"

    return MemoryMetrics(
        total_bytes=total,
        used_bytes=used,
        free_bytes=free,
        available_bytes=available,
        cached_bytes=cached,
        buffers_bytes=buffers,
        swap_used_bytes=swap_used,
        swap_total_bytes=swap_total,
        used_percent=round(used_pct, 1),
        assessment=assessment,
    )


def build_load_metrics(data: dict) -> LoadMetrics:
    """Build load metrics from fetched data."""
    load_data = data.get("kernel.all.load", {}).get("instances", {})

    load_1m = float(load_data.get(1, 0.0))
    load_5m = float(load_data.get(5, 0.0))
    load_15m = float(load_data.get(15, 0.0))

    runnable = int(get_first_value(data, "kernel.all.runnable"))
    nprocs = int(get_first_value(data, "kernel.all.nprocs"))
    ncpu = int(get_first_value(data, "hinv.ncpu", 1))

    if load_1m > ncpu * 2:
        assessment = f"Load is very high ({load_1m:.1f} vs {ncpu} CPUs)"
    elif load_1m > ncpu:
        assessment = f"Load is elevated ({load_1m:.1f} > {ncpu} CPUs)"
    else:
        assessment = "Load is normal"

    return LoadMetrics(
        load_1m=round(load_1m, 2),
        load_5m=round(load_5m, 2),
        load_15m=round(load_15m, 2),
        runnable=runnable,
        nprocs=nprocs,
        assessment=assessment,
    )


def build_disk_metrics(data: dict) -> DiskMetrics:
    """Build disk I/O metrics from fetched data."""
    read_bytes = get_first_value(data, "disk.all.read_bytes")
    write_bytes = get_first_value(data, "disk.all.write_bytes")
    reads = get_first_value(data, "disk.all.read")
    writes = get_first_value(data, "disk.all.write")

    if read_bytes > 100_000_000 or write_bytes > 100_000_000:
        assessment = (
            f"Heavy disk I/O ({read_bytes / 1e6:.0f} MB/s read, {write_bytes / 1e6:.0f} MB/s write)"
        )
    elif read_bytes > 10_000_000 or write_bytes > 10_000_000:
        assessment = "Moderate disk activity"
    else:
        assessment = "Disk I/O is low"

    return DiskMetrics(
        read_bytes_per_sec=round(read_bytes, 1),
        write_bytes_per_sec=round(write_bytes, 1),
        reads_per_sec=round(reads, 1),
        writes_per_sec=round(writes, 1),
        assessment=assessment,
    )


def build_network_metrics(data: dict) -> NetworkMetrics:
    """Build network I/O metrics from fetched data."""
    in_bytes = sum_instances(data, "network.interface.in.bytes")
    out_bytes = sum_instances(data, "network.interface.out.bytes")
    in_packets = sum_instances(data, "network.interface.in.packets")
    out_packets = sum_instances(data, "network.interface.out.packets")

    total_throughput = in_bytes + out_bytes
    if total_throughput > 100_000_000:
        assessment = f"High network throughput ({total_throughput / 1e6:.0f} MB/s)"
    elif total_throughput > 10_000_000:
        assessment = "Moderate network activity"
    else:
        assessment = "Network I/O is low"

    return NetworkMetrics(
        in_bytes_per_sec=round(in_bytes, 1),
        out_bytes_per_sec=round(out_bytes, 1),
        in_packets_per_sec=round(in_packets, 1),
        out_packets_per_sec=round(out_packets, 1),
        assessment=assessment,
    )


def _extract_process_data_sources(data: dict) -> dict[str, dict]:
    """Extract all process data sources from raw PCP data."""
    return {
        "pid": data.get("proc.psinfo.pid", {}).get("instances", {}),
        "cmd": data.get("proc.psinfo.cmd", {}).get("instances", {}),
        "args": data.get("proc.psinfo.psargs", {}).get("instances", {}),
        "rss": data.get("proc.memory.rss", {}).get("instances", {}),
        "utime": data.get("proc.psinfo.utime", {}).get("instances", {}),
        "stime": data.get("proc.psinfo.stime", {}).get("instances", {}),
        "io_read": data.get("proc.io.read_bytes", {}).get("instances", {}),
        "io_write": data.get("proc.io.write_bytes", {}).get("instances", {}),
    }


def _calculate_cpu_percent(
    inst_id: str, utime_data: dict, stime_data: dict, include_cpu: bool
) -> float | None:
    """Calculate CPU percentage for a process instance."""
    if not include_cpu and not utime_data:
        return None
    utime = float(utime_data.get(inst_id, 0))
    stime = float(stime_data.get(inst_id, 0))
    return (utime + stime) / 10.0


def _calculate_io_metrics(
    inst_id: str, io_read_data: dict, io_write_data: dict, include_io: bool
) -> tuple[float | None, float | None]:
    """Calculate I/O read/write metrics for a process instance."""
    if not include_io and not io_read_data:
        return None, None
    io_read = float(io_read_data.get(inst_id, 0))
    io_write = float(io_write_data.get(inst_id, 0))
    return io_read, io_write


def _build_process_info(
    inst_id: str, sources: dict[str, dict], sort_by: str, total_mem: float
) -> ProcessInfo | None:
    """Build a single ProcessInfo from instance data."""
    pid = int(sources["pid"].get(inst_id, 0))
    if pid <= 0:
        return None

    cmd = str(sources["cmd"].get(inst_id, "unknown"))
    cmdline = str(sources["args"].get(inst_id, cmd))[:200]
    rss = int(sources["rss"].get(inst_id, 0)) * 1024
    rss_pct = (rss / total_mem * 100) if total_mem > 0 else 0.0

    cpu_pct = _calculate_cpu_percent(inst_id, sources["utime"], sources["stime"], sort_by == "cpu")

    io_read, io_write = _calculate_io_metrics(
        inst_id, sources["io_read"], sources["io_write"], sort_by == "io"
    )

    return ProcessInfo(
        pid=pid,
        command=cmd,
        cmdline=cmdline,
        cpu_percent=round(cpu_pct, 1) if cpu_pct is not None else None,
        rss_bytes=rss,
        rss_percent=round(rss_pct, 1),
        io_read_bytes_per_sec=round(io_read, 1) if io_read is not None else None,
        io_write_bytes_per_sec=round(io_write, 1) if io_write is not None else None,
    )


def build_process_list(data: dict, sort_by: str, total_mem: float, ncpu: int) -> list[ProcessInfo]:
    """Build list of ProcessInfo from fetched data."""
    sources = _extract_process_data_sources(data)
    processes: list[ProcessInfo] = []

    for inst_id in sources["pid"]:
        process = _build_process_info(inst_id, sources, sort_by, total_mem)
        if process is not None:
            processes.append(process)

    return processes


def get_sort_key(proc: ProcessInfo, sort_by: str) -> float:
    """Get sort key value for a process."""
    if sort_by == "cpu":
        return proc.cpu_percent or 0.0
    elif sort_by == "memory":
        return float(proc.rss_bytes)
    elif sort_by == "io":
        return (proc.io_read_bytes_per_sec or 0.0) + (proc.io_write_bytes_per_sec or 0.0)
    return 0.0


def assess_processes(processes: list[ProcessInfo], sort_by: str, ncpu: int) -> str:
    """Generate assessment string for top processes."""
    if not processes:
        return "No processes found"

    top = processes[0]
    if sort_by == "cpu":
        if top.cpu_percent and top.cpu_percent > ncpu * 100 * 0.5:
            return f"{top.command} is CPU-bound ({top.cpu_percent:.0f}%)"
        return f"Top CPU: {top.command} ({top.cpu_percent:.0f}%)"
    elif sort_by == "memory":
        return f"Top memory: {top.command} ({top.rss_percent:.1f}%)"
    elif sort_by == "io":
        total_io = (top.io_read_bytes_per_sec or 0) + (top.io_write_bytes_per_sec or 0)
        return f"Top I/O: {top.command} ({total_io / 1e6:.1f} MB/s)"
    return f"Top process: {top.command}"


def build_tcp_stats(data: dict) -> TCPStats:
    """Build TCP protocol statistics from fetched data."""
    active_opens = get_first_value(data, "network.tcp.activeopens")
    passive_opens = get_first_value(data, "network.tcp.passiveopens")
    attempt_fails = get_first_value(data, "network.tcp.attemptfails")
    estab_resets = get_first_value(data, "network.tcp.estabresets")
    current_estab = int(get_first_value(data, "network.tcp.currestab"))
    retrans = get_first_value(data, "network.tcp.retranssegs")
    in_errs = get_first_value(data, "network.tcp.inerrs")
    out_rsts = get_first_value(data, "network.tcp.outrsts")

    # Assess TCP health
    if retrans > 100:
        assessment = "Heavy retransmissions - significant packet loss or congestion"
    elif retrans > 10:
        assessment = "Moderate retransmissions - some packet loss"
    elif attempt_fails > 10:
        assessment = "High connection failure rate"
    elif estab_resets > 10:
        assessment = "Frequent connection resets - peers may be crashing or rejecting"
    elif in_errs > 0:
        assessment = "Receiving malformed TCP segments"
    else:
        assessment = "TCP health is normal"

    return TCPStats(
        active_opens_per_sec=round(active_opens, 2),
        passive_opens_per_sec=round(passive_opens, 2),
        attempt_fails_per_sec=round(attempt_fails, 2),
        estab_resets_per_sec=round(estab_resets, 2),
        current_established=current_estab,
        retransmits_per_sec=round(retrans, 2),
        in_errors_per_sec=round(in_errs, 2),
        out_resets_per_sec=round(out_rsts, 2),
        assessment=assessment,
    )


def build_udp_stats(data: dict) -> UDPStats:
    """Build UDP protocol statistics from fetched data."""
    in_dgrams = get_first_value(data, "network.udp.indatagrams")
    out_dgrams = get_first_value(data, "network.udp.outdatagrams")
    in_errs = get_first_value(data, "network.udp.inerrors")
    no_ports = get_first_value(data, "network.udp.noports")

    if in_errs > 10:
        assessment = "High UDP receive error rate - possible data loss"
    elif no_ports > 100:
        assessment = "Many datagrams to closed ports - possible scan or misconfiguration"
    elif in_errs > 0:
        assessment = "Some UDP receive errors"
    else:
        assessment = "UDP health is normal"

    return UDPStats(
        in_datagrams_per_sec=round(in_dgrams, 2),
        out_datagrams_per_sec=round(out_dgrams, 2),
        in_errors_per_sec=round(in_errs, 2),
        no_ports_per_sec=round(no_ports, 2),
        assessment=assessment,
    )


def build_interface_errors(data: dict) -> list[InterfaceErrors]:
    """Build per-interface error/drop rates from fetched data."""
    in_errors = data.get("network.interface.in.errors", {}).get("instances", {})
    out_errors = data.get("network.interface.out.errors", {}).get("instances", {})
    in_drops = data.get("network.interface.in.drops", {}).get("instances", {})

    all_ifaces = set(in_errors.keys()) | set(out_errors.keys()) | set(in_drops.keys())

    results: list[InterfaceErrors] = []
    for iface in sorted(all_ifaces):
        results.append(
            InterfaceErrors(
                interface=str(iface),
                in_errors_per_sec=round(float(in_errors.get(iface, 0)), 2),
                out_errors_per_sec=round(float(out_errors.get(iface, 0)), 2),
                in_drops_per_sec=round(float(in_drops.get(iface, 0)), 2),
            )
        )

    return results


__all__ = [
    "build_cpu_metrics",
    "build_memory_metrics",
    "build_load_metrics",
    "build_disk_metrics",
    "build_network_metrics",
    "build_tcp_stats",
    "build_udp_stats",
    "build_interface_errors",
    "build_process_list",
    "get_sort_key",
    "assess_processes",
]
