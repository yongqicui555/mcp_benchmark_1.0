# Finding: SDK-004 — CORS / Mcp-Session-Id-Exposure ungeprüft

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Server** | `bakom-mcp` |
| **Check-Reference** | `SDK-004` |
| **Audit-Datum** | 2026-05-08 |

### Observed Behavior

Im --http-Modus startet FastMCP einen HTTP-Server. `grep -rE "CORS|allow_origins|expose_headers|Mcp-Session-Id"` im Code: **0 Treffer.**

### Expected Behavior

Bei Streamable-HTTP / SSE muss der Server den Header `Mcp-Session-Id` für Browser-Clients explizit über `expose_headers` freigeben. Sonst kann der Client nach Reconnect die Session-ID nicht lesen.

### Evidence

- File: `src/bakom_mcp/server.py:1746-1755` — startet `mcp.run(transport="streamable-http", port=port)` ohne CORS-Konfig

### Risk Description

- **Funktionalitätsbug:** Browser-Clients können nach Reconnect nicht resumieren
- **Audit-Trail-Lücke:** Falls FastMCP-Default unsicher (z.B. `allow_origins=*`), wäre das ein CORS-Problem

Aktueller Audit ist auf Code-Ebene; Runtime-Verifikation per `curl` gegen den `--http`-Endpoint nötig.

### Remediation

Falls FastMCP's Streamable-HTTP-Default keinen Mcp-Session-Id-Expose-Header setzt, muss explizit konfiguriert werden:

```python
# Option 1: Falls FastMCP das anbietet
mcp = FastMCP(
    "bakom_mcp",
    cors_origins=["https://example.com"],   # explizit, kein "*"
    cors_expose_headers=["Mcp-Session-Id"],
)

# Option 2: Custom-ASGI-Middleware
from starlette.middleware.cors import CORSMiddleware
app = mcp.streamable_http_app()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://trusted-host.example"],
    expose_headers=["Mcp-Session-Id"],
)
```

Plus Runtime-Test:

```bash
curl -i http://localhost:8050/mcp -H "Origin: https://example.com" \
  | grep -i "Access-Control-Expose-Headers"
```

### Effort Estimate

**S** — Doku-Check + 5 Zeilen Konfig.

### Verification After Fix

`curl`-Output enthält `Access-Control-Expose-Headers: Mcp-Session-Id`.
