# get_system_snapshot

Get a point-in-time system health overview.

## Overview

`get_system_snapshot` returns CPU, memory, disk I/O, network I/O, and load metrics in a single call. This is the **primary tool** for system health checks and performance troubleshooting.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `categories` | `list[str]` (optional) | All categories | Which metrics to include: `cpu`, `memory`, `disk`, `network`, `load` |
| `sample_interval` | `float` | `1.0` | Seconds between samples for rate calculation (0.1 - 10.0) |

## Return Type

Returns a `SystemSnapshot` with these fields:

```python
class SystemSnapshot:
    cpu: CPUMetrics | None          # CPU usage percentages
    memory: MemoryMetrics | None    # Memory utilization
    disk: DiskMetrics | None        # Disk I/O rates
    network: NetworkMetrics | None  # Network I/O rates
    load: LoadMetrics | None        # Load averages
    timestamp: str                  # ISO 8601 timestamp
```

## Example Queries

### Full System Snapshot

```
"What's the current system performance?"
```

Returns all categories.

### CPU Only

```
"What's the CPU usage?"
```

Uses `categories=["cpu"]` to fetch only CPU metrics.

### Custom Sample Interval

For more accurate rate calculations on busy systems, increase the sample interval:

```
"Show me disk I/O with a 5-second sample"
```

Uses `sample_interval=5.0`.

## Metric Details

### CPU Metrics

- **user** - CPU time in user space (%)
- **sys** - CPU time in kernel space (%)
- **idle** - CPU idle time (%)
- **iowait** - CPU waiting for I/O (%)
- **steal** - CPU stolen by hypervisor (%)
- **assessment** - Interpretation (e.g., "High CPU usage")

### Memory Metrics

- **total** - Total physical RAM (bytes)
- **used** - Used memory (bytes)
- **free** - Free memory (bytes)
- **cached** - Page cache (bytes)
- **buffers** - Kernel buffers (bytes)
- **available** - Available for applications (bytes)
- **utilization** - Used / Total (%)
- **assessment** - Interpretation

### Disk Metrics

- **read_bytes_per_sec** - Read throughput (bytes/sec)
- **write_bytes_per_sec** - Write throughput (bytes/sec)
- **read_iops** - Read operations per second
- **write_iops** - Write operations per second
- **assessment** - Interpretation

### Network Metrics

- **rx_bytes_per_sec** - Receive throughput (bytes/sec)
- **tx_bytes_per_sec** - Transmit throughput (bytes/sec)
- **rx_packets_per_sec** - Receive packets per second
- **tx_packets_per_sec** - Transmit packets per second
- **assessment** - Interpretation

### Load Metrics

- **one_minute** - 1-minute load average
- **five_minute** - 5-minute load average
- **fifteen_minute** - 15-minute load average
- **cpu_count** - Number of CPUs
- **assessment** - Interpretation (compared to CPU count)

## How It Works

1. **First sample**: Fetch counter values (disk I/O, network I/O, CPU time)
2. **Wait**: Sleep for `sample_interval` seconds
3. **Second sample**: Fetch counters again
4. **Calculate rates**: (sample2 - sample1) / elapsed_time
5. **Assess**: Provide human-readable interpretations

## Best Practices

### Sample Interval

- **Short bursts** (< 1s): May miss transient spikes
- **Default** (1s): Good balance for most use cases
- **Busy systems** (2-5s): More stable rates, reduces noise

### Category Filtering

Use `categories` to reduce response size and latency:

```python
# Only need CPU and memory
snapshot = await get_system_snapshot(
    ctx,
    categories=["cpu", "memory"]
)
```

## Troubleshooting

### "Rate calculation failed"

If you see this error, PCP couldn't calculate rates (usually counter metrics).

**Causes**:
- pmcd was restarted between samples (counters reset)
- Sample interval too short (< 0.1s)

**Solution**: Retry with a longer `sample_interval`.

### High variance in rates

**Cause**: Sample interval too short for bursty workloads.

**Solution**: Increase `sample_interval` to 2-5 seconds.
