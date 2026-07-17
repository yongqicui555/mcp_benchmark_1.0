# Tools Overview

pcp-mcp provides five MCP tools for querying PCP metrics:

## High-Level Tools

These tools provide curated, interpreted data:

- **[get_system_snapshot](system-snapshot.md)** - Point-in-time system overview (CPU, memory, disk, network, load)
- **[get_process_top](processes.md)** - Top processes by CPU, memory, or I/O usage

## Low-Level Tools

These tools provide raw access to PCP's metric database:

- **[query_metrics](metrics.md#query_metrics)** - Fetch current values for specific metrics
- **[search_metrics](metrics.md#search_metrics)** - Discover available metrics by name pattern
- **[describe_metric](metrics.md#describe_metric)** - Get detailed metadata about a metric

## When to Use Which Tool

| Goal | Recommended Tool |
|------|------------------|
| System health check | `get_system_snapshot` |
| Find heavy processes | `get_process_top` |
| Specific known metric | `query_metrics` |
| Explore available metrics | `search_metrics` |
| Understand a metric | `describe_metric` |

## Tool Design Philosophy

### Clumped vs Atomic

pcp-mcp uses **clumped tools** (like `get_system_snapshot`) instead of creating hundreds of individual tools (one per metric). This reduces tool sprawl and makes the MCP server more efficient.

**Why clumped?**
- Single call gets all related metrics (CPU, memory, disk, network)
- Reduces LLM token usage and API calls
- Provides assessed/interpreted data (not just raw numbers)
- Better context for the LLM

**When to use low-level tools?**
- You need a specific metric not in the high-level tools
- You're exploring the metric namespace
- You need raw metric values without interpretation

## Example Queries

```
"What's the current system performance?"
→ Uses get_system_snapshot

"Show me the top 5 processes by memory"
→ Uses get_process_top(sort_by="memory", limit=5)

"What's the value of kernel.all.load?"
→ Uses query_metrics(names=["kernel.all.load"])

"What metrics are available for network traffic?"
→ Uses search_metrics(pattern="network")

"Tell me more about the disk.dev.read metric"
→ Uses describe_metric(name="disk.dev.read")
```
