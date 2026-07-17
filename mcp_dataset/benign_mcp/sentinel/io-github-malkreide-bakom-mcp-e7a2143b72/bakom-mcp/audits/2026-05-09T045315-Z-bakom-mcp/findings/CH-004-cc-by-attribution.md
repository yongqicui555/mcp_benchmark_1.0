# Finding: CH-004 — OGD CC BY 4.0 Attribution unvollständig

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Server** | `bakom-mcp` |
| **Check-Reference** | `CH-004` |
| **Audit-Datum** | 2026-05-09 |

### Observed Behavior

- README verlinkt BAKOM Open Data Portal (Zeile 281)
- Tool-Outputs enthalten `"datenquelle": "BAKOM + opendata.swiss"` (`server.py:1362`)
- Keine explizite Lizenz-Klausel in Tool-Outputs

### Expected Behavior

OGD-CH-Daten sind unter **CC BY 4.0** verfügbar. Die Lizenz verlangt:
1. Quellenangabe (Urheber: BAKOM / OFCOM)
2. Lizenz-Kennzeichnung (CC BY 4.0)
3. Link zur Lizenz-Seite

In Tool-Outputs sollte das mindestens als Footer mit-ausgegeben werden.

### Evidence

`server.py:1382`:
```python
md += "**Open Data:** https://opendata.swiss/de/organization/bundesamt-fur-kommunikation-bakom"
```

— Quelle ja, aber keine Lizenz-Erwähnung.

### Risk Description

Lizenz-Verstoss formal denkbar (gering, weil Quelle genannt). Reputationsrisiko bei Verwaltungs-Reviews. Compliance-Vermerk in Notion-Tracker erschwert ohne explizite Attribution.

### Remediation

Helper für Tool-Output-Footer:

```python
ATTRIBUTION_FOOTER = (
    "\n\n---\n"
    "**Quelle:** Bundesamt für Kommunikation (BAKOM) via opendata.swiss · "
    "**Lizenz:** [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.de)"
)

# Bei Markdown-Output:
md += ATTRIBUTION_FOOTER
# Bei JSON-Output:
output["lizenz"] = "CC BY 4.0"
output["lizenz_url"] = "https://creativecommons.org/licenses/by/4.0/"
```

README.md ergänzen: Sektion «Lizenz der Daten» (separat von Software-Lizenz MIT).

### Effort Estimate

**S** — 1 Helper + 11 Tool-Edit-Stellen.

### Verification After Fix

`grep "CC BY" src/bakom_mcp/server.py` ≥ 1.
