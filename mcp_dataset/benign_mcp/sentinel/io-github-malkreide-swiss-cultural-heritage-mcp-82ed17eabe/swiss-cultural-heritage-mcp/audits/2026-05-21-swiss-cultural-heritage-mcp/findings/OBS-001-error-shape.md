# Finding — OBS-001 / Protocol vs. execution errors

**Check:** OBS-001 — Distinguish protocol vs. execution errors
**Status:** PARTIAL
**Severity:** medium
**File:** `src/swiss_cultural_heritage_mcp/server.py:60-75` (and every tool's `except Exception as e: return _handle_error(e)`)

## Evidence

All seven tools catch `Exception` broadly and return a plain string starting with `"Fehler: …"`:

```python
except Exception as e:
    return _handle_error(e)
```

From the LLM's perspective, this is indistinguishable from a successful result containing the German word "Fehler". The FastMCP SDK supports surfacing tool failures as `ToolResult(isError=True, ...)`, which most clients (incl. Claude Desktop) render differently and which downstream agents can branch on programmatically.

Additionally, `except Exception` swallows programming errors (e.g., `KeyError`, `AttributeError`) into the same string channel, hiding real bugs from observability.

## Impact

- LLMs cannot reliably detect failure → may treat error text as content and present it to users as a finding
- No structured signal for monitoring/alerting (would require regex on `"Fehler:"`)
- Programming bugs (not just upstream API failures) reach the user as opaque strings

## Remediation

1. Catch only the expected exception classes individually (`httpx.HTTPStatusError`, `httpx.TimeoutException`, `httpx.RequestError`, `ET.ParseError`, `ValueError`) and let unexpected exceptions propagate to the framework.
2. Where FastMCP exposes it, return errors via `isError: true` tool-result envelopes rather than as plain strings — or raise `mcp.ToolError` so the SDK formats it correctly.
3. Add at least one test that asserts the error envelope shape (not just substring `"Fehler"`).

**Effort:** S (≤ 1 day)
