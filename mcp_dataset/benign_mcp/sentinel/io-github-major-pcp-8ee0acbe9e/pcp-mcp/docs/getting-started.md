# Getting Started

## Installation

### Quick Start (No Install)

Run immediately with [uvx](https://docs.astral.sh/uv/) — no installation required:

```bash
uvx pcp-mcp
```

Or install as a persistent global tool:

```bash
uvx tool install pcp-mcp
pcp-mcp
```

### Install from PyPI

```bash
pip install pcp-mcp
```

Or add to a project with [uv](https://docs.astral.sh/uv/):

```bash
uv add pcp-mcp
```

### Install Performance Co-Pilot

**Fedora/RHEL/CentOS:**

```bash
sudo dnf install pcp
sudo systemctl enable --now pmcd pmproxy
```

**Ubuntu/Debian:**

```bash
sudo apt install pcp
sudo systemctl enable --now pmcd pmproxy
```

**Verify PCP is running:**

```bash
# Check pmcd (metrics collector)
systemctl status pmcd

# Check pmproxy (REST API server)
systemctl status pmproxy

# Test REST API
curl http://localhost:44322/pmapi/context
```

## Configuration

Configure via environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `PCP_HOST` | pmproxy host | `localhost` |
| `PCP_PORT` | pmproxy port | `44322` |
| `PCP_TARGET_HOST` | Target pmcd host to monitor | `localhost` |
| `PCP_USE_TLS` | Use HTTPS for pmproxy | `false` |
| `PCP_TIMEOUT` | Request timeout (seconds) | `30` |
| `PCP_USERNAME` | HTTP basic auth user | (optional) |
| `PCP_PASSWORD` | HTTP basic auth password | (optional) |

### Example Configurations

**Default (monitor localhost):**

```bash
pcp-mcp
```

**Monitor a remote host:**

```bash
PCP_TARGET_HOST=webserver1.example.com pcp-mcp
```

Or use the CLI flag:

```bash
pcp-mcp --target-host webserver1.example.com
```

**Connect to remote pmproxy:**

```bash
PCP_HOST=metrics.example.com pcp-mcp
```

## MCP Client Setup

### Claude Desktop

Add to `~/.config/claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "pcp": {
      "command": "uvx",
      "args": ["pcp-mcp"]
    }
  }
}
```

For remote monitoring:

```json
{
  "mcpServers": {
    "pcp": {
      "command": "uvx",
      "args": ["pcp-mcp", "--target-host", "webserver1.example.com"]
    }
  }
}
```

!!! tip "Why uvx?"
    Using `uvx` means you don't need pcp-mcp installed — it runs directly from PyPI.
    This avoids PATH issues and keeps your system clean.

Restart Claude Desktop to load the server.

### Other MCP Clients

pcp-mcp supports both stdio (default) and SSE transports:

```bash
# stdio (default)
pcp-mcp

# SSE transport
pcp-mcp --transport sse
```

## Verify Setup

Once configured, ask your LLM:

```
"What's the current system load?"
```

If everything is working, you'll get CPU, memory, disk, and network metrics from PCP.

## Troubleshooting

### Process metrics return empty results

The `get_process_top` tool may return empty results due to limitations in how pmproxy's REST API handles dynamic instance domains like processes.

#### Known limitation

The pmproxy REST API does not enumerate instances for volatile instance domains (like `proc.*` metrics where processes come and go). While `pmprobe -I proc.psinfo.pid` works directly against pmcd, the equivalent REST API call returns empty instances. This is a limitation of the pmproxy REST API, not pcp-mcp.

#### Configuration (may help in some setups)

By default, pmproxy also excludes process metrics from discovery. Check `/etc/pcp/pmproxy/pmproxy.conf`:

```ini
[discover]
exclude.metrics = proc.*,acct.*
exclude.indoms = 3.9,3.40,79.7
```

To enable process metrics in discovery, change **both** lines:

1. Remove `proc.*` from `exclude.metrics`
2. Remove `3.9` from `exclude.indoms` (this is the process instance domain)

After editing:

```ini
[discover]
exclude.metrics = acct.*
exclude.indoms = 3.40,79.7
```

Then restart pmproxy:

```bash
sudo systemctl restart pmproxy
```

#### Alternative

For process monitoring, consider using PCP tools directly (`pmrep`, `pcp-htop`) which communicate with pmcd via the native protocol rather than the REST API.
