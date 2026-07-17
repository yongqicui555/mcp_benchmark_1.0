# get_process_top

Get top processes by resource consumption.

## Overview

`get_process_top` returns the most resource-intensive processes sorted by CPU, memory, or I/O usage. Use this to identify which processes are consuming resources.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `sort_by` | `str` | `"cpu"` | Sort by: `cpu`, `memory`, or `io` |
| `limit` | `int` | `10` | Number of processes to return (1-50) |
| `sample_interval` | `float` | `1.0` | Seconds between samples for CPU/IO rates (0.5-5.0) |

## Return Type

Returns a `ProcessTop` with:

```python
class ProcessTop:
    processes: list[ProcessInfo]  # Top processes
    sort_by: str                  # Sort criteria used
    timestamp: str                # ISO 8601 timestamp
```

Each `ProcessInfo` contains:

```python
class ProcessInfo:
    pid: int                      # Process ID
    name: str                     # Process name
    cmdline: str | None           # Command line
    cpu_percent: float | None     # CPU usage (%)
    mem_bytes: int | None         # Memory usage (bytes)
    mem_percent: float | None     # Memory usage (%)
    io_bytes_per_sec: float | None # I/O rate (bytes/sec)
```

## Example Queries

### Top CPU Consumers

```
"Which processes are using the most CPU?"
```

Uses default `sort_by="cpu"`.

### Top Memory Consumers

```
"Show me the top 5 processes by memory usage"
```

Uses `sort_by="memory"` and `limit=5`.

### Top I/O Consumers

```
"What processes are doing the most disk I/O?"
```

Uses `sort_by="io"`.

## Metric Details

### CPU Usage

- Calculated over `sample_interval` seconds
- Represents % of one CPU core
- Multi-threaded processes can exceed 100% on multi-core systems

**Example**: 250% CPU = process using 2.5 CPU cores

### Memory Usage

- **mem_bytes**: RSS (Resident Set Size) in bytes
- **mem_percent**: RSS / Total RAM × 100

**Note**: Memory is instantaneous (not rate-calculated).

### I/O Rate

- Sum of read + write bytes per second
- Calculated over `sample_interval` seconds
- Only includes processes with I/O activity during sampling period

## Best Practices

### Sort by CPU

**Use case**: Find runaway processes, CPU hogs

**Sample interval**: 1-2 seconds for most cases, 3-5 seconds for very busy systems

```python
top = await get_process_top(
    ctx,
    sort_by="cpu",
    limit=10,
    sample_interval=2.0
)
```

### Sort by Memory

**Use case**: Memory leak investigation, capacity planning

**Sample interval**: N/A (memory is instantaneous, but parameter still required for API consistency)

```python
top = await get_process_top(
    ctx,
    sort_by="memory",
    limit=20
)
```

### Sort by I/O

**Use case**: Disk thrashing, slow I/O investigation

**Sample interval**: 2-5 seconds to capture bursty I/O patterns

```python
top = await get_process_top(
    ctx,
    sort_by="io",
    limit=10,
    sample_interval=5.0
)
```

## Interpreting Results

### High CPU + Low I/O

**Likely cause**: CPU-bound computation (compilation, video encoding, crypto)

**Action**: Consider CPU upgrade or optimization

### High CPU + High I/O

**Likely cause**: I/O wait (disk bottleneck)

**Action**: Investigate disk performance, consider SSD upgrade

### High Memory

**Likely cause**: Memory leak, large dataset, cache

**Action**: Check if memory usage grows over time

### High I/O + Low CPU

**Likely cause**: I/O-bound workload (database, file copying)

**Action**: Investigate disk performance, RAID configuration

## Limitations

### Short-lived Processes

Processes that start and exit within `sample_interval` may be missed.

**Workaround**: Use a shorter `sample_interval` (0.5-1.0s).

### Process Name Truncation

Some process names may be truncated by PCP.

**Workaround**: Use `cmdline` field for full command line.

### I/O Attribution

I/O is attributed to the process that issued it, not necessarily the process that triggered it (e.g., kernel writeback).

## Troubleshooting

### "No processes found"

**Cause**: PCP's process metrics not available or pmcd not running.

**Solution**: Check `pminfo proc` to verify process metrics are available.

### Zero CPU for All Processes

**Cause**: Sample interval too short, or pmcd was restarted.

**Solution**: Use `sample_interval >= 1.0`.
