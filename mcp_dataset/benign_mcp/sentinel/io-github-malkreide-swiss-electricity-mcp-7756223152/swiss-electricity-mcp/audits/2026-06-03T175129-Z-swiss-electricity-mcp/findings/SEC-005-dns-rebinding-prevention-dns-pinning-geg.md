## Finding: SEC-005 — DNS-Rebinding-Prevention: DNS-Pinning gegen TOCTOU

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Check-Status** | partial |
| **Server** | `swiss-electricity-mcp` |
| **Check-Reference** | `SEC-005` |
| **PDF-Reference** | Sec 4.4 |
| **Audit-Datum** | 2026-06-03 |
| **Auditor** | mcp-audit-skill v1.0.0 (Katalog v0.5.0) |

### Observed Behavior

- Keine user-kontrollierten Hostnamen; nur feste Endpunkte

### Gaps / Abweichung vom Pass-Kriterium

- Kein DNS-Pinning/Single-Resolution-Pattern - Restrisiko niedrig mangels dynamischer URLs, aber Defense-in-Depth-Kontrolle fehlt

### Risk Description

SEC-004 (SSRF-Prevention) verlangt: Resolved IP wird gegen Blocklist geprüft, dann Request mit dieser IP. DNS-Rebinding ist ein verfeinerter Angriff, der diese Defense umgeht — durch zwei verschiedene DNS-Antworten für denselben Hostnamen mit kurzem TTL:

### Remediation

### Schritt 1: HTTP-Client mit Custom Transport

```python
import httpx
import socket
import ipaddress

class PinnedTransport(httpx.AsyncHTTPTransport):
    """HTTPX Transport mit DNS-Pinning."""

    async def handle_async_request(self, request):
        url = request.url
        if url.scheme != "https":
            raise httpx.RequestError("Only HTTPS allowed")

        # Resolve einmalig
        loop = asyncio.get_event_loop()
        addrinfo = await loop.getaddrinfo(
            url.host, url.port, type=socket.SOCK_STREAM
        )
        resolved_ip = addrinfo[0][4][0]

        # Range-Check
        ip = ipaddress.ip_address(resolved_ip)
        for blocked in BLOCKED_NETWORKS:
            if ip in blocked:
                raise httpx.RequestError(f"Blocked IP: {ip}")

        # URL mit gepinnter IP, aber Host-Header bleibt
        pinned_url = httpx.URL(str(url).replace(url.host, resolved_ip, 1))
        new_request = httpx.Request(
            method=request.method,
            url=pinned_url,
            headers=httpx.Headers(request.headers),
            content=request.content,
            extensions=request.extensions,
        )
        new_request.headers["Host"] = url.host
        # SNI bleibt durch URL-Hostname (httpx interner default)
        return await super().handle_async_request(new_request)


# Verwendung
async with httpx.AsyncClient(transport=PinnedTransport()) as client:
    response = await client.get("https://api.external.com/data")
```

### Schritt 2: Alternative — Egress-Proxy

Wenn Custom-Transport zu komplex: Stripe Smokescreen als Sidecar erledigt DNS-Pinning automatisch.

```yaml
# docker-compose.yml
services:
  smokescreen:
    image: stripe/smokescreen:latest
    command: ["--listen-ip", "127.0.0.1", "--listen-port", "4750"]


_(... vollstaendige Remediation siehe checks/SEC-005.md)_

### Effort Estimate

M — 1–3 Tage. Custom-Transport oder Egress-Proxy-Setup + Tests.

### Verification After Fix

- Re-Audit von `SEC-005` via `/audit-mcp`
- Pytest-/grep-Guard gegen das Anti-Pattern (wo automatisierbar)
