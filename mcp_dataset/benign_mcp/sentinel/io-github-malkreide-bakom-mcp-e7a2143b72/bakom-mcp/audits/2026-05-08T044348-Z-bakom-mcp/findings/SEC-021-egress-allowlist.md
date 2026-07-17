# Finding: SEC-021 — Keine explizite Egress-Allow-List

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Server** | `bakom-mcp` |
| **Check-Reference** | `SEC-021` |
| **Audit-Datum** | 2026-05-08 |

### Observed Behavior

URLs sind als Konstanten am File-Top deklariert (`server.py:34-47`). Keine User-controlled URLs. Aber: keine zentrale `ALLOWED_HOSTS`-Konstante mit Membership-Check vor jedem httpx-Call.

### Expected Behavior

Code-Layer-Allow-List als frozenset, plus Helper, der jeden Outbound-Call gegen diese Liste prüft.

### Evidence

```python
# server.py:34-47
GEO_ADMIN_API = "https://api3.geo.admin.ch/..."
OPENDATA_SWISS_API = "https://ckan.opendata.swiss/api/3/action"
RTV_DB_API = "https://rtvdb.ofcomnet.ch/api"
# ... 7+ Konstanten ohne zentrale Validierung
```

`grep "ALLOWED_HOSTS|allow_list|egress"`: 0 Treffer.

### Risk Description

- Aktuell impliziter Code-Schutz (URLs sind Konstanten, kein User-Input)
- **Future-Risiko:** Bei einem PR, der einen neuen httpx-Call mit User-controlled-URL einführt, gibt es keinen Review-Trigger
- Network-Layer fehlt komplett (Egress-Firewall) — relevant für Cloud-Deployment

### Remediation

```python
from urllib.parse import urlparse

ALLOWED_EGRESS_HOSTS: frozenset[str] = frozenset({
    "api3.geo.admin.ch",
    "wms.geo.admin.ch",
    "geodesy.geo.admin.ch",
    "ckan.opendata.swiss",
    "opendata.swiss",
    "rtvdb.ofcomnet.ch",
    "www.bakom.admin.ch",
})

async def _http_get(client: httpx.AsyncClient, url: str, **kwargs) -> httpx.Response:
    host = urlparse(url).hostname
    if host not in ALLOWED_EGRESS_HOSTS:
        raise ValueError(f"Egress-Block: {host} nicht in Allow-List")
    return await client.get(url, **kwargs)
```

Alle Tool-Funktionen migrieren auf `_http_get`. Plus pytest-Test, der einen `evil.com`-URL probiert.

### Effort Estimate

**S** — 1 Helper + Refactor von ~10 Call-Stellen.

### Verification After Fix

Pytest-Test: Tool-Aufruf mit gemockter `evil.com`-URL → `ValueError`.
