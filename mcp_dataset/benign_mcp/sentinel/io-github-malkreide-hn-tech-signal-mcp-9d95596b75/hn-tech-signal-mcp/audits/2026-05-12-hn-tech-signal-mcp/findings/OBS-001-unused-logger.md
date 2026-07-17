# Finding: OBS-001 — Logger deklariert, aber nie verwendet

| Feld | Wert |
|---|---|
| **Severity** | **medium** |
| **Status** | closed (re-audit 2026-05-12) |
| **Server** | `hn-tech-signal-mcp` |
| **Check-Reference** | `OBS-001` (Structured Logging Baseline) / `OBS-003` (Error Visibility) |
| **Audit-Datum** | 2026-05-12 |
| **Auditor** | Claude (mcp-audit-skill) |

### Observed Behavior

`src/hn_tech_signal_mcp/server.py:33` deklariert
`logger = logging.getLogger("hn-tech-signal-mcp")`, aber `grep -n "logger\."
src/` liefert **null** Treffer — der Logger wird nie aufgerufen.

`_handle_error` (Zeile 114-125) konvertiert Exceptions in benutzerfreundliche
Strings, **ohne** sie zu loggen. Auch die `fetch_item`-Fehler in `_fetch_hn_stories`
(Zeile 143-147) werden via blankem `except Exception: return None`
verschluckt.

### Expected Behavior

Jeder Fehler-Pfad logged mindestens auf `WARNING`-Level mit Kontext
(Tool-Name, Parameter-Hash, Upstream-Host). Bei `streamable_http`-Mode strukturiertes JSON-Logging
(z. B. via `structlog`), damit Cloud-Logs durchsuchbar sind.

### Evidence

- `src/hn_tech_signal_mcp/server.py:33` — Logger-Deklaration
- `src/hn_tech_signal_mcp/server.py:114-125` — `_handle_error` ohne Logging
- `src/hn_tech_signal_mcp/server.py:146` — `except Exception: return None`
- `grep -rn "logger\." src/` → 0 Treffer

### Risk Description

- Im Produktivbetrieb (Cloud, HTTP-Transport) wird Debugging unmöglich — kein einziger Eintrag landet im Log.
- Stille Fehler bei HN-Item-Fetches (Zeile 143-147) verbergen partial-degradation: Nutzer bekommen leere Listen ohne Hinweis.
- Cache-Hits/Misses sind unsichtbar — Performance-Tuning blind.

### Remediation

```diff
 def _handle_error(e: Exception, source: str = "") -> str:
+    logger.warning("Upstream error from %s: %s: %s", source, type(e).__name__, str(e)[:200])
     prefix = f"[{source}] " if source else ""
     ...
```

```diff
 async def fetch_item(item_id: int) -> Optional[dict]:
     try:
         return await _get(f"{HN_BASE_URL}/item/{item_id}.json")
-    except Exception:
+    except Exception as e:
+        logger.debug("HN item %s fetch failed: %s", item_id, e)
         return None
```

Plus einmalige Basis-Konfiguration in `main()`:

```python
def main() -> None:
    logging.basicConfig(
        level=os.environ.get("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    ...
```

### Effort Estimate

**S–M** — 0.5–1 Tag inklusive Tests und README-Hinweis.

### Verification After Fix

- `grep -rn "logger\." src/` ≥ 4 Treffer
- Test: simulierter Timeout produziert WARN-Log-Eintrag
