# Finding: SEC-002 — Streamable-HTTP-Transport ohne Auth, ohne Bind-Restriktion

| Feld | Wert |
|---|---|
| **Severity** | **high** |
| **Status** | closed (re-audit 2026-05-12) |
| **Server** | `hn-tech-signal-mcp` |
| **Check-Reference** | `SEC-005` (Transport Hardening) |
| **Audit-Datum** | 2026-05-12 |
| **Auditor** | Claude (mcp-audit-skill) |

### Observed Behavior

`main()` in `src/hn_tech_signal_mcp/server.py:734-740` startet bei
`MCP_TRANSPORT=streamable_http` einen HTTP-Server auf konfigurierbarem Port:

```python
def main() -> None:
    transport = os.environ.get("MCP_TRANSPORT", "stdio")
    if transport == "streamable_http":
        port = int(os.environ.get("MCP_PORT", "8000"))
        mcp.run(transport="streamable_http", port=port)
    else:
        mcp.run()
```

Es gibt:
- kein explizites `host="127.0.0.1"` → FastMCP bindet per Default `0.0.0.0`
- keine Auth (kein Bearer/OAuth, kein Origin-Check)
- keine Rate-Limit-Middleware
- keinen Hinweis im README, dass HTTP-Mode authentisiert werden muss

README listet HTTP-Transport explizit als Cloud-Option (`Dual transport — stdio
for Claude Desktop, Streamable HTTP for cloud deployment`).

### Expected Behavior

Der Streamable-HTTP-Mode sollte:
1. Standardmässig auf `127.0.0.1` binden, Wechsel auf `0.0.0.0` muss explizit
   per `MCP_HOST` aktiviert werden.
2. Im Public-Internet-Mode mindestens einen Bearer-Token oder OAuth-Resource-
   Server-Check erzwingen.
3. Im README einen «Hardening»-Abschnitt für Cloud-Deployments enthalten.

### Evidence

- `src/hn_tech_signal_mcp/server.py:734-740` — keine Auth-Middleware, kein Bind-Param
- `README.md:60-65` — empfiehlt Cloud-Deployment ohne Sicherheitshinweis
- `grep -rn "host\|origin\|auth" src/` — keine Treffer

### Risk Description

Wer `MCP_TRANSPORT=streamable_http` auf einem Cloud-VM oder Container ohne
Reverse-Proxy startet, exponiert sämtliche 7 Tools im Internet. Auch wenn alle
Tools `readOnlyHint=True` sind:
- HN/arXiv/Lobsters/GitHub-Calls werden auf Kosten der IP-Adresse / des
  GITHUB_TOKENs des Operators ausgeführt → Rate-Limit-Erschöpfung, ggf. Kosten.
- Wenn GITHUB_TOKEN gesetzt ist, kann jeder Anrufer GitHub-API-Quota verbrennen
  (zusammen mit SEC-001 sogar den Token leak-pfad anstossen).
- Cache-Spam → unbounded Memory Growth (siehe SCALE-001).

### Remediation

```diff
 def main() -> None:
     transport = os.environ.get("MCP_TRANSPORT", "stdio")
     if transport == "streamable_http":
         port = int(os.environ.get("MCP_PORT", "8000"))
-        mcp.run(transport="streamable_http", port=port)
+        host = os.environ.get("MCP_HOST", "127.0.0.1")
+        if host != "127.0.0.1" and not os.environ.get("MCP_BEARER_TOKEN"):
+            raise RuntimeError(
+                "Refusing to bind non-localhost without MCP_BEARER_TOKEN. "
+                "Set MCP_BEARER_TOKEN for Cloud-Deployment."
+            )
+        mcp.run(transport="streamable_http", host=host, port=port)
     else:
         mcp.run()
```

Plus Bearer-Token-Middleware (FastMCP unterstützt `auth=`-Parameter) und
README-Abschnitt «Cloud Deployment Hardening».

### Effort Estimate

**M** — 1–2 Tage inklusive Middleware, README, Integrationstest.

### Verification After Fix

- Start ohne `MCP_HOST` lauscht nur auf `127.0.0.1`
- Start mit `MCP_HOST=0.0.0.0` ohne Bearer wirft beim Boot
- Anfrage ohne Bearer in Cloud-Mode → 401
