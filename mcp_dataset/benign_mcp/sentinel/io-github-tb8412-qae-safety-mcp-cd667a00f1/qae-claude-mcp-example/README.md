# QAE Safety Certification — Claude MCP Server

<!-- mcp-name: io.github.tb8412/qae-safety-mcp -->

An MCP (Model Context Protocol) server that gives Claude access to deterministic safety certification for autonomous actions. Built on the QAE safety kernel, this server enables Claude to evaluate the safety profile of proposed actions across multiple constraint dimensions (scope, reversibility, sensitivity) before execution.

[![QAE-Claude-mcp-example MCP server](https://glama.ai/mcp/servers/tb8412/qae-claude-mcp-example/badges/card.svg)](https://glama.ai/mcp/servers/tb8412/qae-claude-mcp-example)

## Architecture

```
Claude Desktop / IDE
         ↓
    MCP Client
         ↓
    MCP Protocol
         ↓
QAE-Claude-MCP-Server
         ↓
    Python MCP SDK
         ↓
  qae_safety Package (PyO3 bindings to Rust kernel)
         ↓
QAE Safety Certification Engine
         ↓
SafetyCertificate (Certified / Warning / Escalate / Blocked)
```

## Quick Start

### 1. Install the Package

```bash
pip install -e .
```

This installs the MCP server and its dependencies (`qae-safety`, `mcp`). The `qae-safety` package is the production PyO3 binding to the Rust QAE safety kernel, available on PyPI. Requires Python 3.9+.

### 2. Configure Claude Desktop

Add the MCP server to your Claude Desktop configuration:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
**Linux:** `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "qae-safety": {
      "command": "python",
      "args": ["-m", "qae_mcp_server"],
      "env": {}
    }
  }
}
```

### 3. Restart Claude Desktop

The MCP server will start automatically. You can see available tools in the tool menu.

### 4. Use QAE Safety Certification

In Claude, you can now use the following tools:

- **`certify_action`** — Evaluate the safety of a proposed action
  ```
  Action: "Deploy new recommendation algorithm to 10% of users"
  Scope: 0.7 (affects moderate user segment)
  Reversibility: 0.4 (difficult to rollback)
  Sensitivity: 0.8 (high impact on user experience)
  ```

- **`check_budget`** — View your current safety budget utilization

- **`get_certification_history`** — Retrieve recent certification decisions

## Features

- **Deterministic Certification**: No randomness. Same inputs → Same decision every time.
- **Constraint-Based Safety**: Evaluates scope, reversibility, and sensitivity independently.
- **Safety Zones**:
  - **Safe (Certified)**: margin > 0.6 — Safe to proceed
  - **Caution (CertifiedWithWarning)**: margin 0.3–0.6 — Proceed with caution
  - **Danger (EscalateToHuman)**: margin 0.1–0.3 — Human review required
  - **Danger (Blocked)**: margin ≤ 0.1 — Action blocked
- **Budget Tracking**: Certifications consume a safety budget; budget resets on schedule.
- **Audit Trail**: Every certification is logged with full details for review.

## Certification Workflow

1. **Claude proposes an action** with scope, reversibility, and sensitivity scores.
2. **MCP server instantiates a `SafetyCertifier`** with the `AgenticAdapter`.
3. **QAE kernel evaluates** across three constraint channels.
4. **Margin is computed** as normalized headroom in [0, 1].
5. **Decision is mapped** to zone and returned to Claude.
6. **Certificate is logged** with ID and deterministic hash.

Example flow:
```python
from qae_safety import AgenticAdapter, SafetyCertifier, SimpleAction, StateDelta

# Create adapter and certifier
adapter = AgenticAdapter(budget_limit=100.0, rate_limit=50.0)
certifier = SafetyCertifier(adapter)

# Define action with state deltas
action = SimpleAction(
    action_id="act_123",
    agent_id="claude_v3",
    state_deltas=[
        StateDelta(dimension="scope_score", from_value=0.0, to_value=0.7),
        StateDelta(dimension="reversibility_score", from_value=1.0, to_value=0.4),
        StateDelta(dimension="sensitivity_score", from_value=0.0, to_value=0.8),
    ]
)

# Certify
cert = certifier.certify(action)

# Check decision
print(f"Decision: {cert.decision}")  # "Certified", "CertifiedWithWarning", etc.
print(f"Zone: {cert.zone}")          # "Safe", "Caution", "Danger"
print(f"Margins: {cert.margins}")    # {"scope": 0.6, "reversibility": 0.5, ...}
```

## API Reference

### `certify_action`

Evaluate the safety of an action.

**Input:**
- `action_id` (str): Unique action identifier
- `agent_id` (str): Agent performing the action
- `scope` (float): Scope dimension score [0, 1]
- `reversibility` (float): Reversibility dimension score [0, 1]
- `sensitivity` (float): Sensitivity dimension score [0, 1]

**Output:**
```json
{
  "decision": "Certified" | "CertifiedWithWarning" | "EscalateToHuman" | "Blocked",
  "zone": "Safe" | "Caution" | "Danger",
  "margins": {
    "scope": 0.75,
    "reversibility": 0.45,
    "sensitivity": 0.60
  },
  "binding_constraint": "reversibility" | null,
  "drift_budget": 25.5,
  "certificate_id": "cert_abc123",
  "deterministic_hash": "sha256:0x...",
  "timestamp": "2025-03-15T14:23:45Z"
}
```

### `check_budget`

Check current budget utilization.

**Output:**
```json
{
  "budget_limit": 100.0,
  "budget_used": 34.5,
  "budget_remaining": 65.5,
  "budget_utilization": 0.345,
  "rate_limit": 50.0,
  "certifications_this_period": 5,
  "utilization_percent": 34.5,
  "timestamp": "2025-03-15T14:23:45Z"
}
```

### `get_certification_history`

Retrieve recent certifications (limit: 50).

**Output:**
```json
{
  "certifications": [
    {
      "certificate_id": "cert_xyz789",
      "action_id": "act_456",
      "decision": "CertifiedWithWarning",
      "timestamp": "2025-03-15T14:15:32Z"
    }
  ]
}
```

## Configuration

The MCP server uses the built-in `AgenticAdapter` with default thresholds:

- **Safe Threshold**: margin > 0.6
- **Caution Threshold**: margin 0.3–0.6
- **Block Threshold**: margin ≤ 0.1

To customize, edit `src/qae_mcp_server/server.py` and modify the `AgenticAdapter` initialization.

## References

- **QAE Research**: https://doi.org/10.6084/m9.figshare.31742857
- **QAE Platform**: https://qaesubstrate.com
- **PyPI Package**: https://pypi.org/project/qae-safety/
- **Model Context Protocol**: https://modelcontextprotocol.io

## License

This example is part of the QAE fintech risk certification platform. See the main repository for license details.