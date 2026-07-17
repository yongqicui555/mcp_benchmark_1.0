## Finding: ARCH-004 — Inversion of Control: Transport-agnostische Server-Logik

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Check-Status** | partial |
| **Server** | `swiss-electricity-mcp` |
| **Check-Reference** | `ARCH-004` |
| **PDF-Reference** | Sec 2.1 |
| **Audit-Datum** | 2026-06-03 |
| **Auditor** | mcp-audit-skill v1.0.0 (Katalog v0.5.0) |

### Observed Behavior

- ENV-basierte Transport-Selektion stdio + streamable-http (__main__.py:16-24)
- Identische Tool-Outputs unabhaengig vom Transport

### Gaps / Abweichung vom Pass-Kriterium

- Konfiguration ueber Module-Globals (_dashboard/_elcom/_ckan, server.py:70-72) statt Pydantic-Settings
- Kein gemeinsamer Lifespan/Setup-Code (siehe SDK-001)
- Tool-Handler nutzen keinen ctx: Context (siehe SDK-003)

### Risk Description

Die MCP-Spezifikation trennt strikt zwischen Data Layer (JSON-RPC 2.0, Tools/Resources/Prompts) und Transport Layer (stdio / Streamable HTTP / SSE). Der Best-Practice-Standard verlangt, dass die Geschäftslogik des Servers diese Trennung respektiert: Tool-Handler müssen **transport-agnostisch** sein. Derselbe `searchData()`-Tool-Handler muss identisch funktionieren, egal ob er via stdio (Claude Desktop) oder SSE (Cloud-Deployment) aufgerufen wird.

### Remediation

Migrationsweg von monolithischem Setup zu IoC:

```diff
+ from pydantic_settings import BaseSettings
+ from contextlib import asynccontextmanager
+
+ class Settings(BaseSettings):
+     transport: str = "stdio"
+     host: str = "127.0.0.1"
+     port: int = 8000
+
+ @asynccontextmanager
+ async def lifespan(server):
+     # Shared setup für alle Transports
+     server.state.http_client = httpx.AsyncClient(timeout=30)
+     try:
+         yield
+     finally:
+         await server.state.http_client.aclose()
+
- mcp = FastMCP("server")
+ settings = Settings()
+ mcp = FastMCP("server", lifespan=lifespan)

  @mcp.tool()
- async def search(query: str, request: Request):
-     ua = request.headers["User-Agent"]
-     ...
+ async def search(query: str, ctx: Context):
+     client_name = ctx.client_info.name
+     ...

  if __name__ == "__main__":
-     mcp.run(transport="stdio")
+     if settings.transport == "sse":
+         mcp.settings.host = settings.host
+         mcp.settings.port = settings.port
+     mcp.run(transport=settings.transport)
```

### Effort Estimate

M — 1–3 Tage. Refactoring der Transport-Auswahl, Migration aller `request`-Zugriffe auf `ctx`, Testing in beiden Modi.

### Verification After Fix

- Re-Audit von `ARCH-004` via `/audit-mcp`
- Pytest-/grep-Guard gegen das Anti-Pattern (wo automatisierbar)
