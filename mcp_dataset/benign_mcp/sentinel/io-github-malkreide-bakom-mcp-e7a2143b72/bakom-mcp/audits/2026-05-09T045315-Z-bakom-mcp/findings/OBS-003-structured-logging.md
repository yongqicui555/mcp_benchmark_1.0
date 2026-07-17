# Finding: OBS-003 — Strukturiertes Logging unvollständig

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open (Fortschritt: partial) |
| **Server** | `bakom-mcp` |
| **Check-Reference** | `OBS-003` |
| **Audit-Datum** | 2026-05-09 (Re-Audit) |

### Observed Behavior

Re-Audit 2026-05-09 — partial Fortschritt aus den Phase-1/3 PRs:

- `logging.basicConfig(level=logging.INFO)` beim Modul-Import gesetzt (PR #17)
- `logger.exception()` in `_handle_api_error` und im Multi-Standort-Loop (PR #17)
- `logger.warning("Egress blocked", extra={"host": host, ...})` im Egress-Hook (PR #21)
- 3 Logger-Calls (vs. 0 im ersten Run am 2026-05-08)

Lücke: kein info-Logging pro Tool-Call (Start/Ende/Duration), kein `structlog` für JSON-Output, keine SIEM-tauglichen Felder.

### Expected Behavior

Strukturiertes Logging mit RFC-5424-Severity (`debug`, `info`, `warning`, `error`, `critical`). Bei jedem Tool-Call mindestens: tool-name, status, duration, error-class.

### Evidence

- Import vorhanden, Variable initialisiert, aber kein einziger `logger.info`/`logger.error`-Call
- Keine `logging.basicConfig(...)`-Konfiguration
- Kein structlog/loguru in dependencies

### Risk Description

Bei Production-Betrieb (auch lokal stdio) keine Diagnose-Spur. Bei Fehlern muss man auf User-Reports verlassen können — keine SIEM-Integration möglich (siehe OBS-005, derzeit N/A).

### Remediation

```python
import logging
import sys
import time

# stderr fuer stdio-Server
logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
)
logger = logging.getLogger("bakom_mcp")

# In Tool-Funktionen:
async def bakom_broadband_coverage(params):
    start = time.monotonic()
    logger.info("tool_call_start", extra={"tool": "bakom_broadband_coverage"})
    try:
        result = await ...
        logger.info("tool_call_ok", extra={"tool": ..., "duration_ms": (time.monotonic()-start)*1000})
        return result
    except Exception as e:
        logger.error("tool_call_failed", extra={"tool": ..., "error_class": type(e).__name__})
        return _handle_api_error(e)
```

Alternativ: `structlog` für JSON-Logs (Cloud-ready).

### Effort Estimate

**S** — basicConfig + Decorator-Pattern um alle Tools (oder Manual-Calls).

### Verification After Fix

`grep -c "logger\." src/bakom_mcp/server.py` ≥ 22 (info+error pro Tool).
