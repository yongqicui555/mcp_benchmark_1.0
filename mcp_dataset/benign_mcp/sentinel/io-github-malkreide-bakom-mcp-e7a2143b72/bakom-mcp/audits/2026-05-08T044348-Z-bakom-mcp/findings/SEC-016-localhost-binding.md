# Finding: SEC-016 — `host` nicht explizit gesetzt (Default-Verhalten)

| Feld | Wert |
|---|---|
| **Severity** | critical |
| **Status** | open |
| **Server** | `bakom-mcp` |
| **Check-Reference** | `SEC-016` |
| **Audit-Datum** | 2026-05-08 |

### Observed Behavior

```python
# server.py:1750-1753
port = 8050
if transport == "streamable-http":
    print(f"BAKOM MCP Server läuft auf http://localhost:{port}/mcp")
    mcp.run(transport=transport, port=port)
```

Kein `host=`-Parameter. Default kommt aus FastMCP/uvicorn-Config — typisch `127.0.0.1`, aber nicht durch Code garantiert.

### Expected Behavior

`mcp.run(host="127.0.0.1", ...)` explizit. Opt-in für `0.0.0.0` nur via Env-Var mit Warnung.

### Evidence

- `grep "0\\.0\\.0\\.0|host=" src/bakom_mcp/server.py`: keine relevanten Treffer

### Risk Description

NeighborJack: bei `0.0.0.0`-Bind hört der Server auf allen Interfaces. Auf einem geteilten Netzwerk (Coworking-WLAN, Cafés, Conference-Network) kann jeder im selben Subnet das `/mcp`-Endpoint ansprechen — ohne Auth (auth_model=none).

Aktuelles Risiko hängt vom FastMCP-Default ab. Bei künftigem SDK-Update könnte sich der Default ändern.

### Remediation

```python
import os
import sys

if transport == "streamable-http":
    host = os.environ.get("BAKOM_MCP_HOST", "127.0.0.1")
    if host == "0.0.0.0":
        print(
            "WARNUNG: Server bindet auf 0.0.0.0 (alle Interfaces). "
            "Ohne Auth ist das nur in vertrauenswürdigen Netzen sicher.",
            file=sys.stderr,
        )
    print(f"BAKOM MCP Server läuft auf http://{host}:{port}/mcp", file=sys.stderr)
    mcp.run(transport=transport, host=host, port=port)
```

### Effort Estimate

**S** — 5 Zeilen.

### Verification After Fix

```bash
ss -tlnp | grep 8050
# Expected: 127.0.0.1:8050, NICHT 0.0.0.0:8050
```
