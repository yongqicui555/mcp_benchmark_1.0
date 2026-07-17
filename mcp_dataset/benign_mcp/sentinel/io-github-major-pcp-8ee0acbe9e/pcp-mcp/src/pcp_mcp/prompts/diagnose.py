"""Diagnose slow system prompt."""

from __future__ import annotations

from fastmcp.prompts import prompt

from pcp_mcp.icons import ICON_DIAGNOSE, TAGS_DIAGNOSE


@prompt(icons=[ICON_DIAGNOSE], tags=TAGS_DIAGNOSE)
def diagnose_slow_system() -> str:
    """Diagnose why a system is running slowly.

    Returns a structured investigation workflow to identify performance
    bottlenecks by examining CPU, memory, disk, and network metrics.
    """
    return """Investigate system slowness:

1. Get baseline: get_system_snapshot(categories=["cpu", "memory", "load", "disk", "network"])

2. Interpret the assessment fields:
   - If cpu.assessment mentions "I/O wait": Disk bottleneck (skip to step 4)
   - If cpu.assessment mentions "user/system": CPU bottleneck (go to step 3)
   - If memory.assessment mentions "swap": Memory pressure (go to step 5)
   - If load.assessment shows high load: Check load vs ncpu ratio

3. Find CPU hogs:
   - Run: get_process_top(sort_by="cpu", limit=10)
   - Identify processes with high cpu_percent
   - Note: cpu_percent > 100% means multi-threaded (e.g., 200% = 2 cores)

4. Check disk I/O bottleneck:
   - If disk.assessment shows high read/write rates
   - Run: search_metrics("disk.dev") to see per-device metrics
   - Run: get_process_top(sort_by="io", limit=10) to find I/O-heavy processes
   - Cross-check: Does kernel.all.cpu.wait.total correlate with disk activity?

5. Check memory pressure:
   - If memory.assessment indicates swapping
   - Run: get_process_top(sort_by="memory", limit=20)
   - Look for large rss_bytes processes
   - Check if swap usage is growing

6. Check network saturation:
   - If network.assessment shows high throughput
   - Run: search_metrics("network.interface") for per-interface breakdown
   - Look for interface errors or packet drops

7. Report findings:
   - Primary bottleneck (CPU/disk/memory/network)
   - Specific culprits (process names, PIDs)
   - Quantified impact (e.g., "process X using 45% CPU on 8-core system")
   - Recommendations (kill process, add RAM, optimize queries, etc.)
"""
