# Finding: OBS-004 — print()-Statement im --http-Pfad geht nach stdout

| Feld | Wert |
|---|---|
| **Severity** | critical |
| **Status** | open |
| **Server** | `bakom-mcp` |
| **Check-Reference** | `OBS-004` |
| **Audit-Datum** | 2026-05-08 |

### Observed Behavior

```python
# server.py:1752
print(f"BAKOM MCP Server läuft auf http://localhost:{port}/mcp")
```

Der Print landet auf **stdout**. Im aktuellen Code-Pfad nur bei `--http`-Flag aktiv — der stdio-Default (Z. 1755 `mcp.run()`) druckt nichts.

### Expected Behavior

Bei stdio-Servern ist **stdout reserviert für das MCP-JSON-RPC-Protokoll**. Jeder versehentliche stdout-Write bricht das Protokoll. Konvention: alle Diagnose-Outputs nach **stderr**.

### Evidence

- File: `src/bakom_mcp/server.py:1752`
- `grep "file=sys.stderr" src/bakom_mcp/server.py`: 0 Treffer

### Risk Description

Aktuell **kein direkter Bug**, weil der Print nur im `--http`-Pfad ausgeführt wird. **Risiko**: wenn ein künftiger Contributor ein Startup-Banner / Config-Dump / Debug-Info hinzufügt und dabei stdout statt stderr nutzt, bricht der stdio-Default. Konvention prophylaktisch durchsetzen.

### Remediation

```python
import sys

# server.py:1752
print(f"BAKOM MCP Server läuft auf http://localhost:{port}/mcp", file=sys.stderr)
```

Plus: Pre-Commit-Hook oder Ruff-Custom-Rule, die `print(...)` ohne `file=sys.stderr` in `src/` verbietet.

### Effort Estimate

**S** — Einzeiler-Edit + optionale Lint-Regel.

### Verification After Fix

`grep -nE "^\s*print\(" src/bakom_mcp/server.py | grep -v "file=sys.stderr"` liefert 0 Treffer.
