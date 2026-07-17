# Finding: ARCH-003 — «Not Found» Anti-Pattern

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Server** | `bakom-mcp` |
| **Check-Reference** | `ARCH-003` |
| **Audit-Datum** | 2026-05-09 |

### Observed Behavior

`_handle_api_error` (`server.py:371-385`) liefert generische Fehlermeldungen für HTTP-404, 429, 5xx, Timeout und ConnectError. Bei leeren Suchergebnissen (z.B. RTV-Suche, Antennensuche, Multi-Standort) wird eine leere Liste oder ein Hinweis ohne Heuristik zurückgegeben.

### Expected Behavior

Bei leeren Resultaten soll der Server Heuristiken anbieten: «keine Antennen im Radius 100m – möchten Sie 1000m versuchen?», «keine Sender mit Name='SRG' gefunden – meinten Sie 'SRF'?»

### Evidence

- File: `src/bakom_mcp/server.py:375` — generischer 404-Text ohne Vorschlag
- grep nach `suggest|hint|alternativ|did_you_mean`: 0 Treffer

### Risk Description

LLM-Konsumenten lassen Calls ergebnislos enden statt iterativ zu verbessern. UX-Verlust beim Anchor-Demo «Schulhäuser ohne Glasfaser».

### Remediation

```python
# Beispiel fuer Antennensuche:
if not antennen and radius < 5000:
    return {
        "treffer": [],
        "hinweis": (
            f"Keine Antennen im Radius {radius}m gefunden. "
            f"Empfehlung: Radius auf {min(radius * 2, 5000)}m erhoehen."
        ),
    }
```

### Effort Estimate

**S** — pro Tool ein 5–10-Zeilen-Block.

### Verification After Fix

Re-Audit ARCH-003 + Pytest-Test mit leerem-Resultat-Fall.
