"""Shared utility modules for PCP-MCP.

This package contains reusable utilities extracted to follow DRY principles:
- extractors: Metric data extraction helpers
- builders: Metric transformation and builder functions
"""

from pcp_mcp.utils.builders import (
    build_cpu_metrics,
    build_disk_metrics,
    build_load_metrics,
    build_memory_metrics,
    build_network_metrics,
    build_process_list,
)
from pcp_mcp.utils.extractors import (
    extract_help_text,
    extract_timestamp,
    get_first_value,
    get_scalar_value,
    sum_instances,
)

__all__ = [
    # Extractors
    "get_first_value",
    "get_scalar_value",
    "sum_instances",
    "extract_help_text",
    "extract_timestamp",
    # Builders
    "build_cpu_metrics",
    "build_memory_metrics",
    "build_load_metrics",
    "build_disk_metrics",
    "build_network_metrics",
    "build_process_list",
]
