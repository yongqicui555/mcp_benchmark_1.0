## Finding: ARCH-003 — «Not Found» Anti-Pattern: Heuristiken statt leerer Antworten

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Check-Status** | partial |
| **Server** | `swiss-electricity-mcp` |
| **Check-Reference** | `ARCH-003` |
| **PDF-Reference** | Sec 2.2 |
| **Audit-Datum** | 2026-06-03 |
| **Auditor** | mcp-audit-skill v1.0.0 (Katalog v0.5.0) |

### Observed Behavior

- Such-Tools consumption_search_zurich / consumption_search_bfe_datasets vorhanden (server.py:484, :534)
- Leere Treffer liefern leere datasets-Liste + total_hits=0

### Gaps / Abweichung vom Pass-Kriterium

- Kein match_type-Feld (exact/fuzzy/none) in DatasetSearchResponse
- Kein Fuzzy-Fallback und kein actionable Suggestion-Mechanismus bei 0 Treffern

### Risk Description

LLMs reagieren empirisch nachweisbar empfindlich auf negativ-framing in Tool-Responses. Eine Antwort wie `"No results found"` oder `[]` ohne Kontext führt häufig zu einer von zwei Failure-Modes:

### Remediation

```diff
  @mcp.tool()
  async def find_school(name: str) -> list:
      results = await db.find(name)
-     if not results:
-         return []
+     if not results:
+         fuzzy = await db.find_fuzzy(name, threshold=0.7)
+         suggestions = await db.popular_school_names_starting_with(name[:3])
+         return {
+             "results": fuzzy[:5],
+             "match_type": "fuzzy" if fuzzy else "none",
+             "note": (
+                 f"Keine exakten Treffer für '{name}'. "
+                 f"{'Ähnliche Schulen aufgeführt.' if fuzzy else ''} "
+                 f"Häufige Schulnamen: {', '.join(suggestions[:5])}"
+             ),
+         }
      return {"results": results, "match_type": "exact"}
```

### Effort Estimate

S — Pro Tool ~30 Minuten. Bei 10 Such-Tools: 1 Tag.

### Verification After Fix

- Re-Audit von `ARCH-003` via `/audit-mcp`
- Pytest-/grep-Guard gegen das Anti-Pattern (wo automatisierbar)
