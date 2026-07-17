# MCP-Server Audit-Report — `swiss-electricity-mcp`

**Audit-Datum:** 2026-06-03
**Skill-Version:** 1.0.0
**Catalog-Version:** 0.5.0 (catalog_hash 091f446b)

---

## 1. Executive Summary

Server `swiss-electricity-mcp` wurde gegen 44 anwendbare Best-Practice-Checks geprüft. 36 bestanden, 2 Findings dokumentiert (0 critical, 2 high, 0 medium, 0 low). Production-Readiness: erreicht.

**Production-Readiness:** YES

---

## 2. Profil-Snapshot

| Feld | Wert |
|---|---|
| Server-Name | `swiss-electricity-mcp` |
| Audit-Datum | 2026-06-03 |
| Skill-Version | 1.0.0 |
| Catalog-Version | 0.5.0 (catalog_hash 091f446b) |
| transport | `dual` |
| auth_model | `none` |
| data_class | `Public Open Data` |
| write_capable | `False` |
| deployment | `['local-stdio', 'Render', 'Railway', 'andere']` |
| uses_sampling | `False` |
| tools_make_external_requests | `True` |
| stadt_zuerich_context | `False` |
| schulamt_context | `False` |
| data_source.is_swiss_open_data | `True` |

---

## 3. Applicability

### Status pro Kategorie

| Kategorie | Pass | Fail | Partial | Todo | N/A |
|---|---|---|---|---|---|
| ARCH | 11 | 0 | 0 | 0 | 0 |
| CH | 1 | 0 | 0 | 0 | 0 |
| OBS | 5 | 0 | 0 | 0 | 0 |
| OPS | 3 | 0 | 0 | 0 | 0 |
| SCALE | 2 | 0 | 0 | 3 | 0 |
| SDK | 4 | 0 | 0 | 0 | 0 |
| SEC | 10 | 0 | 2 | 3 | 0 |
| **Total** | **36** | **0** | **2** | **6** | **0** |

---

## 4. Findings-Übersicht

_Policy: `fail-or-partial`_

| ID | Category | Severity | Status |
|---|---|---|---|
| SEC-005 | SEC | high | partial |
| SEC-022 | SEC | high | partial |

**Gesamt:** 2 Findings

---

## 5. Detail-Findings

### SEC-005

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

- Only 4 fixed allow-listed hosts; no user-controlled hostnames -> low residual DNS-rebinding risk

### Gaps / Abweichung vom Pass-Kriterium

- No explicit DNS-pinning / single-resolution-then-pin-IP; relies on host allow-list + absence of dynamic URLs

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


### SEC-022

## Finding: SEC-022 — Tool-Hash-Pinning + Namespace-Präfix gegen Rug Pull

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Check-Status** | partial |
| **Server** | `swiss-electricity-mcp` |
| **Check-Reference** | `SEC-022` |
| **PDF-Reference** | Anhang B4 |
| **Audit-Datum** | 2026-06-03 |
| **Auditor** | mcp-audit-skill v1.0.0 (Katalog v0.5.0) |

### Observed Behavior

- Tool-definition hash pinning via tool-definitions.lock.json + test guard against drift; CHANGELOG records tool changes

### Gaps / Abweichung vom Pass-Kriterium

- Server-identity namespace prefix (<server>__<tool>) deliberately deferred to a major-version bump (breaking client change)

### Risk Description

SEC-015 deckt **Tool-Poisoning** ab — bösartige Inhalte in Tool-Beschreibungen beim Onboarding. SEC-022 ergänzt das um zwei verwandte Angriffsklassen:

### Remediation

### Schritt 1: Namespace-Audit

Server-Identity festlegen — typisch der Repo-Name als snake_case-Präfix:

| Repo | Namespace |
|---|---|
| `zh-education-mcp` | `zh_education` |
| `zurich-opendata-mcp` | `zurich_opendata` |
| `parlament-mcp` | `parlament_ch` |

### Schritt 2: Tool-Renaming

```diff
- @mcp.tool()
- async def search(query: str): ...
+ @mcp.tool(name="zh_education__search")
+ async def search(query: str): ...
```

Bei Renaming: Major-Version-Bump, da Tool-Namen Breaking-Changes sind.

### Schritt 3: Hash-Snapshot-Workflow

CI-Step wie im Pass-Pattern Modus 2. `tool-hashes.json` als Artefakt im Release.

### Schritt 4: Bei Update-Disziplin (Synergie zu ARCH-012)

CHANGELOG-Template um «Tool Definition Changes»-Sektion erweitern:

```markdown

### Effort Estimate

M — 1–3 Tage pro Server. Namespace-Renaming + Hash-Workflow + CHANGELOG-Updates.

### Verification After Fix

- Re-Audit von `SEC-022` via `/audit-mcp`
- Pytest-/grep-Guard gegen das Anti-Pattern (wo automatisierbar)


---

## 6. Remediation-Plan

### Empfohlene Reihenfolge

1. **SEC-005** (high, partial)
2. **SEC-022** (high, partial)

---

## 7. Audit-Metadata

| Feld | Wert |
|---|---|
| skill_version | `1.0.0` |
| catalog_version | `0.5.0 (catalog_hash 091f446b)` |
| audit_date | `2026-06-03` |


_Generated by tools/build_report.py — do not edit by hand._
