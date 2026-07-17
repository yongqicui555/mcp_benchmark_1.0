# Finding: SEC-005 — Kein DNS-Pinning (Restrisiko, niedrig)

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Server** | `bakom-mcp` |
| **Check-Reference** | `SEC-005` |
| **Audit-Datum** | 2026-05-08 |

### Observed Behavior

URLs sind statische Konstanten (`server.py:34-47`). Keine DNS-Pinning-Logik. httpx nutzt System-DNS-Resolver mit Standard-TTL.

### Expected Behavior

Für höchste Reife: DNS-Pinning, sodass zwischen `gethostbyname()` und `connect()` kein Resolver-Wechsel den Ziel-Host austauschen kann (TOCTOU).

### Evidence

- `grep "socket.gethostbyname|getaddrinfo|dns_pin"`: 0 Treffer
- Praktisch: alle Hosts sind auf `*.admin.ch` / `opendata.swiss` / `ofcomnet.ch` — staatlich kontrolliert

### Risk Description

DNS-Rebinding-Risiko nur theoretisch:
- Kein User-controlled-Host
- Hosts unter staatlicher Kontrolle
- Risiko-Vector: Adversarial-DNS-Resolver auf der lokalen Maschine

Im stdio-Default-Setup nahezu kein Angriffs-Vektor.

### Remediation

Optional (für höhere Compliance-Anforderungen):

```python
import socket
import ssl

ALLOWED_HOSTS = {
    "api3.geo.admin.ch", "wms.geo.admin.ch", "geodesy.geo.admin.ch",
    "ckan.opendata.swiss", "opendata.swiss",
    "rtvdb.ofcomnet.ch", "www.bakom.admin.ch",
}

def _resolve_pinned(host: str) -> str:
    if host not in ALLOWED_HOSTS:
        raise ValueError(f"Host nicht in Allow-List: {host}")
    return socket.gethostbyname(host)
```

Pragmatisch: für ein Read-only-OGD-Server ist diese Massnahme **akzeptabel als Restrisiko**, dokumentieren und bei Cloud-Deploy nachrüsten.

### Effort Estimate

**S** (optional) — Egress-Allow-List bereits Voraussetzung (SEC-021).

### Verification After Fix

Falls implementiert: Test mit gefälschtem Hostname → ValueError.
