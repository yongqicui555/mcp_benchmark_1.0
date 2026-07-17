"""Analyze CPU usage prompt."""

from __future__ import annotations

from fastmcp.prompts import prompt

from pcp_mcp.icons import ICON_CPU, TAGS_CPU


@prompt(icons=[ICON_CPU], tags=TAGS_CPU)
def analyze_cpu_usage() -> str:
    """Analyze CPU utilization patterns and identify CPU-bound processes.

    Returns a workflow to diagnose high CPU usage, distinguish between
    user-space and kernel CPU time, and identify optimization opportunities.
    """
    return """CPU usage analysis workflow:

1. Get CPU baseline:
   - Run: get_system_snapshot(categories=["cpu", "load"])
   - Read cpu.assessment for quick diagnosis
   - Note: ncpu value (number of CPUs/cores)

2. Interpret CPU metrics:
   - user_percent: Application code execution
   - system_percent: Kernel/syscall overhead
   - idle_percent: Unused CPU capacity
   - iowait_percent: CPU waiting for I/O (NOT CPU-bound if high)
   - Load average: Runnable + waiting processes (compare to ncpu)

3. CPU pattern classification:
   - High user + low system = CPU-intensive application (normal)
   - High system + low user = Kernel overhead (syscalls, context switches)
   - High iowait = NOT a CPU problem, it's disk/storage (see find_io_bottleneck)
   - Load > ncpu = More demand than capacity (may include I/O wait)

4. Find CPU hogs:
   - Run: get_process_top(sort_by="cpu", limit=15)
   - Note: cpu_percent > 100% means multi-core usage (e.g., 400% = 4 cores)
   - Identify unexpected high CPU consumers

5. Per-CPU breakdown (if needed):
   - Run: search_metrics("kernel.percpu.cpu")
   - Useful for: Thread affinity issues, interrupt handling imbalance
   - Look for: One CPU at 100% while others idle (poor parallelization)

6. Check for CPU saturation indicators:
   - Run: query_metrics(["kernel.all.runnable", "kernel.all.pswitch"])
   - High runnable count: More threads than cores (contention)
   - High pswitch (context switches): Thread thrashing

7. Distinguish workload types:
   - Compute-bound: High user%, low syscalls (scientific, encoding, crypto)
   - I/O-bound: High iowait%, moderate user% (databases, file processing)
   - System-bound: High system%, moderate user% (network servers, many syscalls)

8. Report:
   - CPU utilization breakdown: X% user, Y% system, Z% iowait, W% idle
   - Load average: 1/5/15 min values vs ncpu (e.g., "load 8.5 on 8-core = 106%")
   - Top 5 CPU consumers with cpu_percent and command names
   - CPU pattern: compute-bound / I/O-bound / system-bound
   - Saturation indicators: runnable queue, context switches
   - Recommendations:
     * Low idle + high load → Add CPU capacity or optimize hot processes
     * High iowait → Disk bottleneck, not CPU (see I/O investigation)
     * High system% → Profile syscalls, reduce I/O frequency, optimize locking
     * Single-threaded bottleneck → Parallelize if possible
     * Many small processes → Reduce process spawning overhead
"""
