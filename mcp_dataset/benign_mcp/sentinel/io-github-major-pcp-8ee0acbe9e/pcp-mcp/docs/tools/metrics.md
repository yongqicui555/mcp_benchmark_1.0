# Metrics Tools

Low-level tools for direct access to PCP's metric database.

## query_metrics

Fetch current values for specific PCP metrics.

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `names` | `list[str]` | List of PCP metric names to fetch |

### Example

```python
metrics = await query_metrics(
    ctx,
    names=["kernel.all.load", "mem.util.used"]
)
```

### Return Type

Returns a list of `MetricValue`:

```python
class MetricValue:
    name: str              # Metric name
    instances: dict[str, float | int | str] | None  # Instance values
    value: float | int | str | None                # Singular value
    unit: str | None       # Unit (e.g., "millisec", "Kbyte")
```

### Metrics with Instances

Some metrics have multiple instances (e.g., per-CPU, per-disk):

```python
# CPU metrics (one per CPU)
cpu_metrics = await query_metrics(ctx, names=["kernel.percpu.cpu.user"])
# Returns: instances={"cpu0": 25.5, "cpu1": 30.2, ...}

# Disk metrics (one per disk)
disk_metrics = await query_metrics(ctx, names=["disk.dev.read"])
# Returns: instances={"sda": 1024, "sdb": 2048, ...}
```

### Singular Metrics

Metrics without instances return a single value:

```python
load = await query_metrics(ctx, names=["kernel.all.load"])
# Returns: value=1.5
```

---

## search_metrics

Discover available metrics by name pattern.

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `pattern` | `str` | Metric name prefix to search for |

### Example

```python
# Find all network metrics
network_metrics = await search_metrics(ctx, pattern="network")

# Find all kernel metrics
kernel_metrics = await search_metrics(ctx, pattern="kernel")

# Find specific subsystem
disk_metrics = await search_metrics(ctx, pattern="disk.dev")
```

### Return Type

Returns a list of `MetricSearchResult`:

```python
class MetricSearchResult:
    name: str              # Full metric name
    description: str       # Brief description
```

### Common Metric Prefixes

| Prefix | Description |
|--------|-------------|
| `kernel.all.*` | System-wide kernel metrics |
| `kernel.percpu.*` | Per-CPU metrics |
| `mem.*` | Memory metrics |
| `disk.dev.*` | Per-disk metrics |
| `disk.all.*` | Aggregate disk metrics |
| `network.interface.*` | Per-interface network metrics |
| `proc.*` | Process metrics |
| `hinv.*` | Hardware inventory |

### Example Workflow

1. **Explore**: `search_metrics(pattern="disk")` - See what's available
2. **Describe**: `describe_metric(name="disk.dev.read")` - Understand the metric
3. **Query**: `query_metrics(names=["disk.dev.read"])` - Get current values

---

## describe_metric

Get detailed metadata about a PCP metric.

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | `str` | Full PCP metric name |

### Example

```python
info = await describe_metric(ctx, name="kernel.all.load")
```

### Return Type

Returns a `MetricDescription`:

```python
class MetricDescription:
    name: str              # Metric name
    type: str              # Data type (e.g., "float", "u64")
    semantics: str         # Semantic type (e.g., "instant", "counter")
    units: str             # Units (e.g., "millisec", "Kbyte")
    help_text: str         # Detailed description
```

### Semantic Types

| Semantics | Description | Example |
|-----------|-------------|---------|
| `instant` | Point-in-time value | CPU %, memory used |
| `counter` | Monotonically increasing | Bytes read, packets sent |
| `discrete` | Discrete events | Process count |

**Important**: Counter metrics require **rate calculation** (two samples) to be meaningful. High-level tools like `get_system_snapshot` handle this automatically.

### Units

PCP uses a standardized unit system:

| Unit | Description |
|------|-------------|
| `millisec` | Time (milliseconds) |
| `Kbyte`, `Mbyte`, `Gbyte` | Data size |
| `count` | Dimensionless count |
| `none` | No units |

### Example: Understanding a Metric

```
Query: "What does disk.dev.read measure?"
```

```python
desc = await describe_metric(ctx, name="disk.dev.read")
# Returns:
# - type: "u64"
# - semantics: "counter"
# - units: "Kbyte"
# - help_text: "Cumulative kilobytes read from disk devices"
```

**Interpretation**: This is a counter metric (cumulative), so you need to sample it twice and calculate the rate to get "KB/s read".

---

## Working with Metrics

### Finding the Right Metric

1. **Start broad**: `search_metrics(pattern="disk")`
2. **Narrow down**: `search_metrics(pattern="disk.dev")`
3. **Describe**: `describe_metric(name="disk.dev.read")`
4. **Query**: `query_metrics(names=["disk.dev.read"])`

### Counter vs Instant Metrics

**Instant metrics** (semantics="instant"):
- Single query is sufficient
- Example: `mem.util.used`, `kernel.all.load`

**Counter metrics** (semantics="counter"):
- Need two samples to calculate rate
- Example: `disk.dev.read`, `network.interface.in.bytes`
- Use high-level tools (`get_system_snapshot`) or implement rate calculation

### Instance Metrics

Metrics with instances return one value per instance:

```python
# Per-CPU user time
cpu_user = await query_metrics(ctx, names=["kernel.percpu.cpu.user"])
# Returns: {"cpu0": 1500, "cpu1": 2000, "cpu2": 1800, ...}

# Per-disk read bytes
disk_read = await query_metrics(ctx, names=["disk.dev.read"])
# Returns: {"sda": 102400, "sdb": 204800, ...}
```

To get **total across all instances**, use the `.all` variant if available:

```python
total_disk_read = await query_metrics(ctx, names=["disk.all.read"])
# Returns: value=307200
```

---

## Example Queries

### System Load

```
"What's the current system load?"
```

```python
load = await query_metrics(ctx, names=[
    "kernel.all.load[1 minute]",
    "kernel.all.load[5 minute]",
    "kernel.all.load[15 minute]"
])
```

### Memory Usage

```
"How much memory is being used?"
```

```python
mem = await query_metrics(ctx, names=[
    "mem.util.used",
    "mem.util.free",
    "mem.util.cached"
])
```

### Network Traffic (requires rate calculation)

```
"What's the network traffic on eth0?"
```

**Recommended**: Use `get_system_snapshot(categories=["network"])` instead.

**Manual approach**:
1. Query `network.interface.in.bytes["eth0"]` → value1
2. Wait 1 second
3. Query again → value2
4. Rate = (value2 - value1) / 1.0 seconds

---

## Best Practices

### Use High-Level Tools When Possible

**Avoid**:
```python
# Don't manually calculate rates
cpu1 = await query_metrics(ctx, names=["kernel.all.cpu.user"])
await asyncio.sleep(1)
cpu2 = await query_metrics(ctx, names=["kernel.all.cpu.user"])
rate = (cpu2 - cpu1) / 1.0
```

**Prefer**:
```python
# Let the tool handle rate calculation
snapshot = await get_system_snapshot(ctx, categories=["cpu"])
cpu_percent = snapshot.cpu.user
```

### Batch Queries

Fetch multiple metrics in one call:

```python
# Good: Single call
metrics = await query_metrics(ctx, names=[
    "kernel.all.load",
    "mem.util.used",
    "disk.dev.read"
])

# Bad: Multiple calls
load = await query_metrics(ctx, names=["kernel.all.load"])
mem = await query_metrics(ctx, names=["mem.util.used"])
disk = await query_metrics(ctx, names=["disk.dev.read"])
```

### Check Semantics Before Use

Always `describe_metric` first to understand:
- Is it a counter? (needs rate calculation)
- What units? (bytes, milliseconds, etc.)
- Does it have instances? (per-CPU, per-disk, etc.)
