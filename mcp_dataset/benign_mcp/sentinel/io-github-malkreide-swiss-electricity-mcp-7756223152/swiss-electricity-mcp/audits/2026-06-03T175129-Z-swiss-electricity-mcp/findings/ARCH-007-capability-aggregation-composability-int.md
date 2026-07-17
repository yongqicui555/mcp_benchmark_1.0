## Finding: ARCH-007 — Capability-Aggregation: Composability intern, Atomarität extern

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Check-Status** | partial |
| **Server** | `swiss-electricity-mcp` |
| **Check-Reference** | `ARCH-007` |
| **PDF-Reference** | Sec 2.3 |
| **Audit-Datum** | 2026-06-03 |
| **Auditor** | mcp-audit-skill v1.0.0 (Katalog v0.5.0) |

### Observed Behavior

- Tools liefern abgeschlossene Resultate (vollstaendige Envelopes, keine reinen IDs/Pointer)
- Aggregations-Tool tariff_compare_municipalities vorhanden (server.py:442)

### Gaps / Abweichung vom Pass-Kriterium

- tariff_compare_municipalities iteriert Gemeinden sequenziell in einer for-Schleife (server.py:451) statt asyncio.gather - bei 20 BFS-Nrn unnoetig langsam

### Risk Description

Eng verwandt zu ARCH-006, aber mit anderem Fokus: **Wo ARCH-006 sagt «weniger Tools, höhere Use-Cases», sagt ARCH-007 «aus LLM-Sicht atomar, intern composable».**

### Remediation

```diff
- @mcp.tool()
- async def get_motion_id(title: str) -> str: ...
-
- @mcp.tool()
- async def get_motion_details(motion_id: str) -> dict: ...
-
- @mcp.tool()
- async def get_motion_tags(motion_id: str) -> list: ...

+ @mcp.tool(
+     name="findMotionWithDetails",
+     description=(
+         "Sucht eine parlamentarische Motion anhand des Titels und liefert "
+         "vollständige Details inkl. Tags, Status, Eingebenden. "
+         "Aggregiert intern Suchindex + Detail-API + Tag-API."
+     ),
+ )
+ async def find_motion_with_details(title: str, ctx: Context) -> dict:
+     motion_ids = await api.search_motion_ids(title, limit=5)
+     if not motion_ids:
+         return {"results": [], "match_type": "none", "note": "..."}  # ARCH-003
+     # Parallel Details + Tags für alle Treffer
+     detail_tasks = [api.get_motion_details(mid) for mid in motion_ids]
+     tag_tasks = [api.get_motion_tags(mid) for mid in motion_ids]
+     details, tags = await asyncio.gather(
+         asyncio.gather(*detail_tasks),
+         asyncio.gather(*tag_tasks),
+     )
+     return {
+         "results": [
+             {**d, "tags": t} for d, t in zip(details, tags)
+         ],
+         "match_type": "exact",
+         "count": len(details),
+     }
```

### Effort Estimate

M — 1–3 Tage. Identifikation der Aggregations-Möglichkeiten + Refactoring + Performance-Tests.

### Verification After Fix

- Re-Audit von `ARCH-007` via `/audit-mcp`
- Pytest-/grep-Guard gegen das Anti-Pattern (wo automatisierbar)
