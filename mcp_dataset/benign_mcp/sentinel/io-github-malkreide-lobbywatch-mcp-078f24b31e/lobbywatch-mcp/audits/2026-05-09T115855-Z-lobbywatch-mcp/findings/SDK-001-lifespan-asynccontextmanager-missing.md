## Finding: SDK-001 — FastMCP Lifespan via @asynccontextmanager + AsyncExitStack

**Severity:** high
**Status:** open
**Server:** lobbywatch-mcp
**Check-Reference:** SDK-001

### Observed Behavior

FastMCP wird ohne lifespan= konstruiert. LobbywatchClient.aclose() wird in Produktion nie aufgerufen.

### Expected Behavior

Best-Practice-Katalog (SDK-001). Siehe checks/SDK-001.md für volle Pass-Criteria.

### Evidence

src/lobbywatch_mcp/server.py:134 FastMCP(name=..., instructions=...) - kein lifespan
src/lobbywatch_mcp/client.py:64 aclose() existiert aber ungenutzt
grep asynccontextmanager|AsyncExitStack|lifespan src/ → 0 hits

### Risk Description

httpx.AsyncClient leakt Connections beim Shutdown. Bei Cloud-Deployments (HTTP-Transport) führt das zu File-Descriptor-Leaks und unsauberem TCP-Teardown.

### Remediation

```
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(server):
    client = LobbywatchClient()
    try:
        yield {'client': client}
    finally:
        await client.aclose()

mcp = FastMCP(name='lobbywatch-mcp', lifespan=lifespan, ...)
```

### Effort Estimate

M (1-3d)
