## Finding: SEC-021 — Egress-Allow-List: Code-Layer und Network-Layer

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Check-Status** | partial |
| **Server** | `swiss-electricity-mcp` |
| **Check-Reference** | `SEC-021` |
| **PDF-Reference** | Anhang B5 + B12 |
| **Audit-Datum** | 2026-06-03 |
| **Auditor** | mcp-audit-skill v1.0.0 (Katalog v0.5.0) |

### Observed Behavior

- De-facto-Egress-Allowlist: alle Ziel-Hosts sind hardcodierte Modul-Konstanten (api_client.py:25-28), keine dynamischen Hosts

### Gaps / Abweichung vom Pass-Kriterium

- Keine explizite frozenset-Allowlist mit assert_host_allowed-Pre-Request-Check
- Keine Network-Layer-Egress-Control (NetworkPolicy) dokumentiert; keine docs/network-egress.md

### Risk Description

SEC-004 (SSRF-Prevention) blockiert Requests an interne IP-Ranges. SEC-021 ergänzt das auf der **anderen Seite**: welche externen Ziele darf der Server überhaupt erreichen?

### Remediation

### Schritt 1: Allow-List-Inventar

Pro Server alle ausgehenden HTTP-Hosts identifizieren:

```bash
grep -rE 'https://[a-z0-9.-]+' src/ | \
  sed -E 's/.*https:\/\/([a-z0-9.-]+).*/\1/' | sort -u
```

Resultat: minimale Allow-Liste.

### Schritt 2: Code-Layer einbauen

Wie Pass-Pattern Modus 1.

### Schritt 3: Network-Layer einbauen

Bei Kubernetes: NetworkPolicy wie oben. Bei AWS: Security Group mit egress-Rules. Bei Cloudflare WARP: Zero-Trust-Policy.

### Schritt 4: Tests gegen Regression

```python
async def test_egress_blocked_to_non_allowlisted_host():
    with pytest.raises(PermissionError, match="not in allow-list"):
        await fetch_external_data("https://evil.example.com/", mock_ctx())


async def test_egress_allowed_to_allowlisted_host():
    # Mock-Response, kein echter Network-Call
    with respx.mock:
        respx.get("https://opendata.swiss/api/...").respond(200, json={"ok": True})
        result = await fetch_external_data("https://opendata.swiss/api/...", mock_ctx())
        assert result["ok"]
```

### Effort Estimate

M — 1–3 Tage. Code-Layer-Allow-List + Network-Policy + Doku + Tests.

### Verification After Fix

- Re-Audit von `SEC-021` via `/audit-mcp`
- Pytest-/grep-Guard gegen das Anti-Pattern (wo automatisierbar)
