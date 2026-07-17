# Remote Monitoring

pcp-mcp can monitor any host running PCP's `pmcd` daemon. There are two architectures for remote monitoring:

## Architecture 1: Remote Target via Local pmproxy

```
┌─────────┐         ┌─────────┐          ┌─────────┐         ┌─────────┐
│   LLM   │ ◄─MCP─► │ pcp-mcp │ ◄─HTTP─► │ pmproxy │ ◄─────► │  pmcd   │
└─────────┘         └─────────┘          │ (local) │         │ (remote)│
                                         └─────────┘         └─────────┘
```

**Use case**: Monitor remote hosts through your local pmproxy.

**Setup**:

```bash
# Set target host to the remote system
pcp-mcp --target-host webserver1.example.com
```

Or via environment:

```bash
export PCP_TARGET_HOST=webserver1.example.com
pcp-mcp
```

**Requirements**:
- Local pmproxy must have network access to remote pmcd (port 44321)
- Remote pmcd must allow connections from pmproxy's host

## Architecture 2: Remote pmproxy

```
┌─────────┐         ┌─────────┐          ┌─────────┐         ┌─────────┐
│   LLM   │ ◄─MCP─► │ pcp-mcp │ ◄─HTTP─► │ pmproxy │ ◄─────► │  pmcd   │
└─────────┘         └─────────┘          │ (remote)│         │ (remote)│
                                         └─────────┘         └─────────┘
```

**Use case**: Connect directly to a remote pmproxy server (e.g., centralized metrics gateway).

**Setup**:

```bash
# Connect to remote pmproxy
export PCP_HOST=metrics.example.com
pcp-mcp
```

**Requirements**:
- Network access to remote pmproxy (port 44322)
- Optional: TLS if pmproxy is configured with HTTPS

## Configuration Examples

### Monitor Multiple Hosts

Create different MCP server configurations:

```json
{
  "mcpServers": {
    "pcp-web1": {
      "command": "pcp-mcp",
      "args": ["--target-host", "web1.example.com"]
    },
    "pcp-db1": {
      "command": "pcp-mcp",
      "args": ["--target-host", "db1.example.com"]
    }
  }
}
```

### Secure Connection (TLS)

If pmproxy is configured with HTTPS:

```bash
export PCP_HOST=metrics.example.com
export PCP_USE_TLS=true
export PCP_PORT=44322
pcp-mcp
```

### Authentication

If pmproxy requires HTTP basic auth:

```bash
export PCP_USERNAME=metrics_user
export PCP_PASSWORD=secure_password
export PCP_HOST=metrics.example.com
pcp-mcp
```

## Firewall Configuration

### pmcd (port 44321)

If using Architecture 1, ensure pmproxy can reach pmcd:

```bash
# On the remote host
sudo firewall-cmd --add-port=44321/tcp --permanent
sudo firewall-cmd --reload
```

### pmproxy (port 44322)

If using Architecture 2, ensure pcp-mcp can reach pmproxy:

```bash
# On the pmproxy host
sudo firewall-cmd --add-port=44322/tcp --permanent
sudo firewall-cmd --reload
```

## Troubleshooting

### Connection Refused

```
Error: Connection refused to localhost:44322
```

**Solution**: Ensure pmproxy is running:

```bash
sudo systemctl status pmproxy
sudo systemctl start pmproxy
```

### Target Host Unreachable

```
Error: Unable to connect to target host
```

**Solution**: Check network connectivity and firewall rules:

```bash
# Test from pmproxy host
telnet webserver1.example.com 44321
```

### Timeout Errors

**Solution**: Increase timeout for slow networks:

```bash
export PCP_TIMEOUT=60
pcp-mcp
```
