## Finding: OBS-001 — Protocol vs. Execution Errors: korrekte Trennung

**Severity:** high
**Status:** open
**Server:** lobbywatch-mcp
**Check-Reference:** OBS-001

### Observed Behavior

ValueError/RuntimeError werden roh geraised statt FastMCP ToolError / McpError.

### Expected Behavior

Best-Practice-Katalog (OBS-001). Siehe checks/OBS-001.md für volle Pass-Criteria.

### Evidence

src/lobbywatch_mcp/server.py:292 raise ValueError(...)
src/lobbywatch_mcp/client.py:126,140,150 raise RuntimeError(...)

### Risk Description

Client kann nicht unterscheiden zwischen Protocol-Layer-Fehler (Server kaputt) und Tool-Execution-Fehler (User-Eingabe falsch). LLM erhält keine differenzierte Reaktion.

### Remediation

```
from mcp.shared.exceptions import McpError
from mcp.types import INVALID_PARAMS, INTERNAL_ERROR

raise McpError(ErrorData(code=INVALID_PARAMS, message=f'kriterium must be one of {sorted(allowed)}'))
```

### Effort Estimate

S (< 1d)
