## Finding: ARCH-004 — Inversion of Control: Settings-Objekt statt globale Module-Vars

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Server** | `swiss-cultural-heritage-mcp` |
| **Check-Reference** | `ARCH-004` |
| **PDF-Reference** | Sec 2.x |
| **Audit-Datum** | 2026-06-02 |
| **Auditor** | Claude (mcp-audit-skill) |

### Observed Behavior

- Tool handlers are transport-agnostic; none read the raw request object
- Single shared lifespan covers both transports (server.py:75-89)
- dual transport selectable at entrypoint (server.py:1318-1326)

### Gaps vs. Pass Criteria

- Configuration uses module-level constants (CKAN_API, HTTP_TIMEOUT, ALLOWED_HOSTS, server.py:30-48), not a Pydantic-Settings object — criterion explicitly requires a settings object over global module vars
- Transport selected via sys.argv flag rather than ENV var

### Expected Behavior

Configuration (endpoints, timeouts, allow-list, host/port) should come from a Pydantic-Settings object loaded once, not from module-level constants; transport selectable via ENV.

### Risk Description

Module-global config cannot be overridden per environment without editing code; tests and multi-env deploys monkeypatch globals, which is brittle.

### Remediation

Introduce a `Settings(BaseSettings)` with fields for CKAN base URL, timeout, allow-list, transport, host, port (env-prefixed). Instantiate once at startup and inject. Replace the `sys.argv` flag parsing with `MCP_TRANSPORT`/`MCP_HOST`/`MCP_PORT` env vars.

### Effort Estimate

**M**  (S < 1d · M 1–3d · L 1–2w · XL > 2w)

### Verification After Fix

Re-run check `ARCH-004` from the mcp-audit-skill catalog; add/adjust the pytest case noted in the remediation where applicable.
