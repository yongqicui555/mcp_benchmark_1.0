# Finding — SDK-001 / Lifespan & shared HTTP client

**Check:** SDK-001 — FastMCP Lifespan Management
**Status:** FAIL
**Severity:** high
**File:** `src/swiss_cultural_heritage_mcp/server.py:54-57`

## Evidence

```python
async def _http_get(url: str, params: dict | None = None) -> httpx.Response:
    """Wiederverwendbare HTTP-GET-Funktion mit einheitlichem Timeout."""
    async with httpx.AsyncClient(follow_redirects=True) as client:
        return await client.get(url, params=params, timeout=HTTP_TIMEOUT)
```

A new `httpx.AsyncClient` is instantiated per HTTP call. The FastMCP instance (`mcp = FastMCP("swiss_cultural_heritage_mcp")`, line 27) is created without a `lifespan` argument, so there is no startup/shutdown hook to own a shared client.

The anti-pattern is amplified by `heritage_cross_search`, which fans out three concurrent requests via `asyncio.gather` — each creating, TLS-handshaking, and tearing down its own client.

## Impact

- No HTTP connection pooling or keep-alive across calls → unnecessary TLS handshakes per request, higher latency for `heritage_cross_search` and OAI-PMH harvests
- Resource leak risk if `httpx` raises during `__aexit__` is masked by the surrounding `try/except`
- Bypasses the recommended FastMCP lifespan idiom; future cross-cutting concerns (caching, retry, allow-list — see SEC-021) have no obvious place to attach

## Remediation

1. Define an `@asynccontextmanager` lifespan that creates a single `httpx.AsyncClient` (with `timeout=HTTP_TIMEOUT`, `follow_redirects=False`) and yields it on the server context.
2. Construct the server as `FastMCP("swiss_cultural_heritage_mcp", lifespan=lifespan)`.
3. Replace `_http_get` callers with the shared client retrieved from the context.
4. Add a unit test that asserts the same client instance is reused across two tool invocations.

**Effort:** S (≤ 1 day)
