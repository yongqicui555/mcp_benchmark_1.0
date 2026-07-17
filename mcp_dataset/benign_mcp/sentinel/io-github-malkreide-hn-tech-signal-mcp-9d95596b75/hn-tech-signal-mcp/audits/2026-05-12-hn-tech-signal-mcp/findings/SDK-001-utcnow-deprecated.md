# Finding: SDK-001 — `datetime.utcnow()` deprecated ab Python 3.12

| Feld | Wert |
|---|---|
| **Severity** | **medium** |
| **Status** | closed (re-audit 2026-05-12) |
| **Server** | `hn-tech-signal-mcp` |
| **Check-Reference** | `SDK-003` (Forward-Compatible Standard Library Usage) |
| **Audit-Datum** | 2026-05-12 |
| **Auditor** | Claude (mcp-audit-skill) |

### Observed Behavior

`datetime.utcnow()` wird sechsmal verwendet:

```
src/hn_tech_signal_mcp/server.py:339
src/hn_tech_signal_mcp/server.py:447
src/hn_tech_signal_mcp/server.py:494
src/hn_tech_signal_mcp/server.py:552
src/hn_tech_signal_mcp/server.py:613
src/hn_tech_signal_mcp/server.py:713
```

`pyproject.toml` deklariert Python 3.11, 3.12, 3.13 als Targets. Ab CPython
3.12 ist `datetime.utcnow()` mit `DeprecationWarning` markiert (PEP-aligned
Deprecation), Entfernung in einer zukünftigen Version vorgesehen. Die Methode
liefert ausserdem ein *naives* Datetime-Objekt — Quelle vieler Timezone-Bugs.

Bemerkenswert: in `_ts_to_iso` (Zeile 128-132) wird bereits korrekt mit
`tz=timezone.utc` gearbeitet — die Inkonsistenz fällt also doppelt auf.

### Expected Behavior

```python
from datetime import datetime, timezone
datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
```

oder einmaliger Helper:

```python
def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
```

### Evidence

`grep -n "datetime.utcnow" src/hn_tech_signal_mcp/server.py` → 6 Treffer (siehe oben).

### Risk Description

- Lautlose `DeprecationWarning`-Floods in Python 3.12 / 3.13 CI-Logs.
- Bruchgefahr in zukünftiger Python-Version.
- Naive Datetimes sind eine bekannte Bug-Quelle bei JSON-Round-Trips.

### Remediation

```diff
- datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
+ _now_iso()
```

Plus einmalige Helper-Definition ganz oben im Modul. Bonus: Linter-Regel
`DTZ005` (ruff `flake8-datetimez`) aktivieren, um Regressionen zu blockieren.

### Effort Estimate

**S** — 30 Minuten.

### Verification After Fix

- `ruff check --select=DTZ src/` ohne Treffer
- Tests grün
