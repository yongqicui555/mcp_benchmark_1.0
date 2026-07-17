# Finding: SEC-004 — `arxiv_search.category` ohne Whitelist-Validierung

| Feld | Wert |
|---|---|
| **Severity** | **low** |
| **Status** | closed (re-audit 2026-05-12) |
| **Server** | `hn-tech-signal-mcp` |
| **Check-Reference** | `SEC-013` (Input Validation Symmetry) |
| **Audit-Datum** | 2026-05-12 |
| **Auditor** | Claude (mcp-audit-skill) |

### Observed Behavior

`ArxivLatestInput.categories` wird gegen `ARXIV_AI_CATEGORIES` validiert
(`server.py:251-260`). `ArxivSearchInput.category` dagegen ist
freie Form (`server.py:266`) und wird in `arxiv_search` direkt in die
Query interpoliert:

```python
search_query = f"all:{params.query} AND cat:{params.category}"
```

### Expected Behavior

Gleiche Validierungs-Symmetrie wie `categories` — Whitelist gegen
`ARXIV_AI_CATEGORIES` oder Erweiterung um weitere offizielle arXiv-Codes.

### Evidence

- `src/hn_tech_signal_mcp/server.py:266` — `category: Optional[str] = Field(default=None, ...)` ohne Validator
- `src/hn_tech_signal_mcp/server.py:487-490` — direkte Stringinterpolation

### Risk Description

- Kein klassisches Injection-Risk (arXiv-Query-Syntax, nicht SQL/Shell), aber
  inkonsistente UX: Tool-Autoren erwarten symmetrische Validierung.
- Tippfehler-Resilienz fehlt — User bekommen leeres Result statt klarer
  Fehlermeldung.

### Remediation

```diff
 class ArxivSearchInput(BaseModel):
     model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
     query: str = Field(..., description="...", min_length=1, max_length=300)
     category: Optional[str] = Field(default=None, description="...")
+
+    @field_validator("category")
+    @classmethod
+    def validate_category(cls, v: Optional[str]) -> Optional[str]:
+        if v is None:
+            return v
+        if v not in ARXIV_AI_CATEGORIES:
+            raise ValueError(f"Invalid category '{v}'. Valid: {sorted(ARXIV_AI_CATEGORIES)}")
+        return v
```

### Effort Estimate

**S** — < 30 Minuten inkl. Test.

### Verification After Fix

- Pytest-Test analog `test_arxiv_latest_input_invalid_category`
