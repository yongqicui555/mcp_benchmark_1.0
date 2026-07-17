# Finding: SDK-001 — Kein FastMCP-Lifespan, httpx-Client pro Tool-Call

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Server** | `bakom-mcp` |
| **Check-Reference** | `SDK-001` |
| **Audit-Datum** | 2026-05-08 |

### Observed Behavior

```python
# server.py:391
mcp = FastMCP("bakom_mcp", instructions="...")
# kein lifespan-Argument

# 10x in tools:
async with httpx.AsyncClient() as client:
    ...
```

`grep "asynccontextmanager|AsyncExitStack|lifespan"`: 0 Treffer.

### Expected Behavior

FastMCP unterstützt `lifespan` als `@asynccontextmanager`. Best Practice: einen einzigen `httpx.AsyncClient` zur Server-Startup-Zeit erstellen, im Context speichern, in jedem Tool wiederverwenden.

### Evidence

- File: `src/bakom_mcp/server.py:391` — kein lifespan-Param
- File: `src/bakom_mcp/server.py:456`, 524, 600, 725, 799, 929, 1043, ... — 10 separate `async with httpx.AsyncClient()`-Blöcke

### Risk Description

- **Performance:** TLS-Handshake pro Tool-Call (~50–200ms). Bei `bakom_multi_standort_konnektivitaet` mit 20 Standorten × 2 Calls = 40 neue Connections.
- **Connection-Pool-Effekt entgeht** — httpx.AsyncClient würde HTTP/2-Connection-Reuse erlauben.
- **Lifecycle-Management:** Bei Shutdown-Signal kein graceful close.

### Remediation

```python
from contextlib import asynccontextmanager
from dataclasses import dataclass
import httpx
from mcp.server.fastmcp import FastMCP, Context

@dataclass
class AppContext:
    http: httpx.AsyncClient

@asynccontextmanager
async def lifespan(server):
    async with httpx.AsyncClient(
        timeout=15.0,
        headers={"User-Agent": "bakom-mcp/1.0"},
        http2=True,
    ) as client:
        yield AppContext(http=client)

mcp = FastMCP("bakom_mcp", instructions="...", lifespan=lifespan)

@mcp.tool(...)
async def bakom_broadband_coverage(params: BroadbandCoverageInput, ctx: Context) -> str:
    client = ctx.request_context.lifespan_context.http
    # ... statt async with httpx.AsyncClient() as client:
```

### Effort Estimate

**M** — 1–2 Tage: lifespan + Refactor von 10 Tool-Funktionen + Test-Anpassung.

### Verification After Fix

`grep -c "async with httpx.AsyncClient" src/bakom_mcp/server.py` = 0. `grep "lifespan"` ≥ 1.
