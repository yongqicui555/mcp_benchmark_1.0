"""Check network performance prompt."""

from __future__ import annotations

from fastmcp.prompts import prompt

from pcp_mcp.icons import ICON_NETWORK, TAGS_NETWORK


@prompt(icons=[ICON_NETWORK], tags=TAGS_NETWORK)
def check_network_performance() -> str:
    """Check network performance and identify bandwidth/error issues.

    Returns a workflow to analyze network throughput, identify saturated
    interfaces, and detect packet loss or errors.
    """
    return """Network performance investigation:

1. Get network overview:
   - Run: get_system_snapshot(categories=["network"])
   - Read network.assessment for quick diagnosis
   - Note: Rates are per-second (bytes/sec, packets/sec)

2. Interpret network metrics:
   - in_bytes_sec / out_bytes_sec: Throughput (compare to link speed)
   - in_packets_sec / out_packets_sec: Packet rate
   - Assessment field indicates saturation or errors

3. Per-interface breakdown:
   - Run: search_metrics("network.interface")
   - Run: query_metrics(["network.interface.in.bytes", "network.interface.out.bytes"])
   - Note: These are COUNTERS, use get_system_snapshot for rates
   - Identify busy interfaces vs idle interfaces (e.g., eth0 busy, lo idle)

4. Check for errors, drops, and protocol health:
   - Run: get_network_stats() for TCP/UDP stats and interface errors in one call
   - TCP retransmits > 0 = Packet loss or congestion
   - TCP attempt_fails > 0 = Services unreachable or firewall blocks
   - TCP estab_resets > 0 = Peers crashing or rejecting connections
   - TCP current_established = Connection count (high values may indicate leaks)
   - UDP in_errors > 0 = Receive errors, possible data loss
   - Interface in_errors/out_errors = Hardware, driver, or cable issues
   - Interface in_drops = Buffer overflow (traffic exceeds processing capacity)

5. Calculate interface saturation:
   - Compare throughput to link speed (e.g., 950 Mbps on 1 Gbps link = 95%)
   - Sustained >80% = Approaching saturation
   - Bursts >95% = Temporarily saturated

6. Find network-heavy processes (indirect):
   - PCP proc.* namespace doesn't have per-process network metrics
   - Use system tools: netstat, ss, iftop (outside PCP)
   - Or correlate: High network I/O often correlates with high CPU/disk I/O

7. Drill into specific protocol issues (if needed):
   - Run: search_metrics("network.tcp") for all available TCP metrics
   - Run: search_metrics("network.udp") for all available UDP metrics
   - Use query_metrics() for raw counter values when deeper analysis is needed

8. Report:
   - Per-interface throughput (e.g., "eth0: 850 Mbps in, 120 Mbps out")
   - Link utilization % (if link speed known)
   - Errors/drops: Count and affected interfaces
   - Traffic pattern: Symmetric (similar in/out) vs asymmetric (download/upload heavy)
   - Packet rate: Normal vs abnormal (tiny packets = inefficient, possible attack)
   - Recommendations:
     * High utilization + no errors → Upgrade link or load balance
     * Errors/drops present → Check cables, NIC drivers, switch ports
     * Asymmetric traffic → Normal for client (download heavy) or server (upload heavy)
     * High packet rate + low byte rate → Small packets (check for SYN flood, fragmentation)
"""
