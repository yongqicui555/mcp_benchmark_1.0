## Finding: SEC-016 — 0.0.0.0-Binding-Prevention (NeighborJack)

**Severity:** critical
**Status:** open
**Server:** lobbywatch-mcp
**Check-Reference:** SEC-016
**PDF-Reference:** Sec 4 / Anhang B

### Observed Behavior

`src/lobbywatch_mcp/__main__.py:19,25` defaults the HTTP/SSE bind host to `0.0.0.0`:

```python
host = os.getenv("LOBBYWATCH_MCP_HOST", "0.0.0.0")
```

`README.md:124` documents this default to operators. With no auth (`auth_model=none`), any device on the LAN can issue MCP calls when a developer runs `LOBBYWATCH_MCP_TRANSPORT=http lobbywatch-mcp`.

### Expected Behavior

Default to `127.0.0.1` (loopback). Operators wanting LAN/cloud exposure must set `LOBBYWATCH_MCP_HOST=0.0.0.0` explicitly and acknowledge they have placed an auth-gateway in front.

### Evidence

- File: `src/lobbywatch_mcp/__main__.py:19`
- File: `src/lobbywatch_mcp/__main__.py:25`
- Doc: `README.md:124` lists default as `0.0.0.0`

### Risk Description

Coffee-shop / corporate-LAN attack: a colleague's laptop on the same Wi-Fi can curl the server, exfiltrate the (admittedly public) data, and abuse the local cache; in production this is the canonical NeighborJack configuration.

### Remediation

```diff
-        host = os.getenv("LOBBYWATCH_MCP_HOST", "0.0.0.0")
+        host = os.getenv("LOBBYWATCH_MCP_HOST", "127.0.0.1")
```

Update README config table accordingly. Consider emitting a `logger.warning` at startup when host == "0.0.0.0" and auth_model == "none".

### Effort Estimate

S (< 1d)
