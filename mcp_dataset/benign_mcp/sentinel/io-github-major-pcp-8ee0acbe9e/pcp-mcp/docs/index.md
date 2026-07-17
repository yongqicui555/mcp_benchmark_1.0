# pcp-mcp

MCP server for [Performance Co-Pilot (PCP)](https://pcp.io/) metrics.

Query system performance metrics via the Model Context Protocol - CPU, memory, disk I/O, network, processes, and more.

## Features

- **System Monitoring** - CPU, memory, disk I/O, network, load averages
- **Process Monitoring** - Top processes by CPU, memory, or I/O usage
- **Metric Discovery** - Search and explore 1000+ PCP metrics
- **Remote Monitoring** - Monitor any host running pmcd
- **Real-time Data** - Direct access to PCP's high-resolution metrics

## Architecture

```
┌─────────┐         ┌─────────┐          ┌─────────┐         ┌─────────┐
│   LLM   │ ◄─MCP─► │ pcp-mcp │ ◄─HTTP─► │ pmproxy │ ◄─────► │  pmcd   │
└─────────┘         └─────────┘          └─────────┘         └─────────┘
                                         (REST API)          (metrics)
```

**pcp-mcp** is a FastMCP server that exposes Performance Co-Pilot metrics through the Model Context Protocol. It connects to PCP's REST API server (pmproxy) to fetch real-time system metrics.

## Quick Start

```bash
# Install
pip install pcp-mcp

# Install PCP (if not already installed)
sudo dnf install pcp
sudo systemctl enable --now pmproxy

# Run the MCP server
pcp-mcp
```

Configure Claude Desktop (`~/.config/claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "pcp": {
      "command": "pcp-mcp"
    }
  }
}
```

## Use Cases

### 🔍 Performance Troubleshooting

Ask your LLM:
- "Analyze current system performance and identify bottlenecks"
- "Why is my disk I/O so high?"
- "Which processes are consuming the most CPU?"

### 📊 System Monitoring

- "Give me a health check of the production server"
- "Compare CPU usage over the last minute"
- "Monitor network traffic on eth0"

### 📈 Capacity Planning

- "What's the memory utilization trend?"
- "Show me disk usage across all filesystems"
- "Analyze process resource consumption patterns"

## Requirements

- **Python**: 3.10+
- **PCP**: Performance Co-Pilot with `pmproxy` running
