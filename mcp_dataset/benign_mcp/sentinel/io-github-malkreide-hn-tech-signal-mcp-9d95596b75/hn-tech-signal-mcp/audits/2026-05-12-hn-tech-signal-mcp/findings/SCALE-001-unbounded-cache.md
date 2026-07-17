# Finding: SCALE-001 — Unbounded In-Memory-Cache

| Feld | Wert |
|---|---|
| **Severity** | **low** |
| **Status** | closed (re-audit 2026-05-12) |
| **Server** | `hn-tech-signal-mcp` |
| **Check-Reference** | `SCALE-002` (Bounded Resources) |
| **Audit-Datum** | 2026-05-12 |
| **Auditor** | Claude (mcp-audit-skill) |

### Observed Behavior

`src/hn_tech_signal_mcp/server.py:49` — `_cache: dict[str, tuple[float, Any]] = {}` ist
ein gewöhnliches Dict ohne Grössenbeschränkung. Cache-Keys enthalten freien User-
Input (HN-Query, GitHub-Topic, arXiv-Query):

```python
cache_key = f"hn_search|{params.query}|{params.limit}|{params.days_back}|{params.tags}"
```

`_cache_get` löscht abgelaufene Einträge nur beim Re-Read desselben Keys,
nicht periodisch. Bei vielen einmaligen Queries wächst der Cache linear ohne
Eviction.

### Expected Behavior

LRU-Eviction mit Max-Size (z. B. 512 Einträge) oder regelmässiges Sweep.

### Evidence

- `src/hn_tech_signal_mcp/server.py:49-71` — Cache-Implementierung
- `src/hn_tech_signal_mcp/server.py:374` — User-controlled Cache-Key

### Risk Description

- Stdio-Mode: Prozess hat normalerweise kurze Lebensdauer → geringe Auswirkung.
- HTTP-Mode (siehe SEC-002): Long-running-Server kann RAM gesteuert von externen Anrufern füllen → DoS-fähig.

### Remediation

```diff
- _cache: dict[str, tuple[float, Any]] = {}
+ from collections import OrderedDict
+ _CACHE_MAX_ENTRIES = 512
+ _cache: "OrderedDict[str, tuple[float, Any]]" = OrderedDict()

  def _cache_set(key: str, data: Any) -> None:
+     if key in _cache:
+         _cache.move_to_end(key)
      _cache[key] = (time.time(), data)
+     while len(_cache) > _CACHE_MAX_ENTRIES:
+         _cache.popitem(last=False)
```

### Effort Estimate

**S** — < 1 Stunde.

### Verification After Fix

- Unit-Test: 1000 Inserts → `len(_cache) == 512`
