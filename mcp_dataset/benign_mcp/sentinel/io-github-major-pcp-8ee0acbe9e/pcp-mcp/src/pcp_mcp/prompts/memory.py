"""Investigate memory usage prompt."""

from __future__ import annotations

from fastmcp.prompts import prompt

from pcp_mcp.icons import ICON_MEMORY, TAGS_MEMORY


@prompt(icons=[ICON_MEMORY], tags=TAGS_MEMORY)
def investigate_memory_usage() -> str:
    """Investigate memory consumption and identify memory pressure.

    Returns a workflow to analyze memory utilization, identify memory
    hogs, and distinguish between normal cache usage and actual pressure.
    """
    return """Memory investigation workflow:

1. Get memory overview:
   - Run: get_system_snapshot(categories=["memory"])
   - Read memory.assessment field for quick diagnosis

2. Interpret memory metrics:
   - mem.util.available is KEY metric (not "free"!)
   - Large cache is NORMAL (Linux uses free RAM for cache)
   - Swapping = BAD (indicates memory pressure)
   - Check used_percent vs swap usage

3. Assessment-based actions:
   - "Memory pressure" → Go to step 4
   - "Cache is large" → Normal, but check top consumers anyway (step 4)
   - "Swapping actively" → CRITICAL, go to step 4 immediately

4. Find memory consumers:
   - Run: get_process_top(sort_by="memory", limit=20)
   - Note processes with high rss_bytes
   - Calculate: rss_percent shows memory impact
   - Look for unexpected memory hogs (leaked memory, runaway processes)

5. Detailed memory breakdown:
   - Run: search_metrics("mem.util") for full breakdown
   - Check: mem.util.slab (kernel memory)
   - Check: mem.util.anonpages (process private memory)
   - Check: mem.util.swapCached (pages swapped but still in RAM)

6. NUMA systems (if applicable):
   - Run: search_metrics("mem.numa") to check per-node allocation
   - Look for imbalanced NUMA usage

7. Report:
   - Total memory: X GB
   - Used: Y% (Z GB used, W GB available)
   - Top 5 memory consumers with RSS sizes
   - Swap status: active/inactive, growth rate if swapping
   - Recommendation:
     * No pressure + large cache = Normal
     * High usage + no swap = Monitor but OK
     * Active swapping = Add RAM or reduce load
     * Single process consuming >50% = Investigate for memory leak
"""
