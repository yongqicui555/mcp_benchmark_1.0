"""Find I/O bottleneck prompt."""

from __future__ import annotations

from fastmcp.prompts import prompt

from pcp_mcp.icons import ICON_DISK, TAGS_DISK


@prompt(icons=[ICON_DISK], tags=TAGS_DISK)
def find_io_bottleneck() -> str:
    """Find disk I/O bottlenecks and identify processes causing high I/O.

    Returns a workflow to diagnose disk performance issues, identify
    hot devices, and find I/O-intensive processes.
    """
    return """Disk I/O investigation:

1. Get system-wide I/O snapshot:
   - Run: get_system_snapshot(categories=["disk", "cpu"])
   - Check disk.assessment for read/write rates
   - Check cpu.assessment for iowait_percent

2. Interpret I/O metrics:
   - High iowait_percent (>20%) = CPU waiting for disk
   - Read vs write imbalance may indicate backup, logging, or database queries
   - Sustained high I/O (>100 MB/s on HDD, >500 MB/s on SSD) = saturated

3. Identify hot disks:
   - Run: search_metrics("disk.dev")
   - Run: query_metrics(["disk.dev.read_bytes", "disk.dev.write_bytes"])
   - Note: These are COUNTERS, use get_system_snapshot for rates
   - Look for specific devices with disproportionate activity

4. Find I/O-heavy processes:
   - Run: get_process_top(sort_by="io", limit=10, sample_interval=2.0)
   - Note: Longer sample_interval (2-5s) gives more accurate I/O rates
   - Identify processes with high io_read_bytes_sec or io_write_bytes_sec

5. Correlate with CPU iowait:
   - If cpu.iowait_percent is high AND disk I/O is high:
     → Confirmed disk bottleneck
   - If disk I/O is high BUT iowait is low:
     → Fast storage keeping up (SSD/NVMe)
   - If iowait is high BUT disk I/O is low:
     → May be network storage (NFS) or storage controller issue

6. Check for I/O patterns:
   - Bursty I/O: Scheduled jobs, backups, log rotation
   - Sustained I/O: Database, file server, streaming
   - Random I/O: Database seeks (slow on HDD, fast on SSD)
   - Sequential I/O: Backups, large file copies

7. Advanced: Check per-partition I/O (if needed):
   - Run: search_metrics("disk.partitions")
   - Useful for systems with multiple partitions on same disk

8. Report:
   - Busiest disks by name (e.g., sda, nvme0n1)
   - Read vs write breakdown (e.g., "80% reads, 20% writes")
   - Top 3-5 processes causing I/O with rates
   - I/O pattern: bursty vs sustained, random vs sequential
   - Bottleneck severity: iowait % and queue depth
   - Recommendations:
     * High random I/O on HDD → Migrate to SSD
     * Single process saturating disk → Optimize queries/access patterns
     * Multiple processes fighting for I/O → I/O scheduler tuning or workload separation
     * Backup/batch jobs during business hours → Reschedule
"""
