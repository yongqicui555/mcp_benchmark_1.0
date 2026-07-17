# Finding: SDK-002 — `mcp` als Modulname kollidiert mit Python-Standard-Konvention

| Feld | Wert |
|---|---|
| **Severity** | **low** |
| **Status** | closed (re-audit 2026-05-12) |
| **Server** | `hn-tech-signal-mcp` |
| **Check-Reference** | `SDK-005` (Naming Hygiene) |
| **Audit-Datum** | 2026-05-12 |
| **Auditor** | Claude (mcp-audit-skill) |

### Observed Behavior

`src/hn_tech_signal_mcp/server.py:78` bindet die FastMCP-Instanz an die globale
Variable `mcp`. Im selben Modul wird `from mcp.server.fastmcp import FastMCP`
importiert (Zeile 30). Das Modul `mcp` (das Paket) und die lokale Variable
`mcp` (die FastMCP-Instanz) teilen sich den Namensraum **nicht** (Python löst
das auf), aber:

- Autocomplete/IDE-Navigation wird verwirrend.
- Falsch sortierte Imports (z. B. `import mcp` nach Variable-Definition) würden
  schweigend die lokale Variable überschreiben.

### Expected Behavior

Konvention: Server-Instanz heisst `server`, `app` oder vollqualifiziert:

```python
server = FastMCP("hn_tech_signal_mcp", ...)
```

### Evidence

- `src/hn_tech_signal_mcp/server.py:30` — `from mcp.server.fastmcp import FastMCP`
- `src/hn_tech_signal_mcp/server.py:78` — `mcp = FastMCP("hn_tech_signal_mcp", ...)`

### Risk Description

Reines Maintainability-Issue; kein Sicherheits- oder Korrektheits-Impact heute, aber Refactor-Risiko in Zukunft.

### Remediation

```diff
- mcp = FastMCP(...)
+ server = FastMCP(...)
```

Plus Suche/Ersetzen für alle `@mcp.tool(...)`-Decorators.

### Effort Estimate

**S** — 15 Minuten inklusive Tests-Update.

### Verification After Fix

- `pytest tests/` grün
- `grep -n "^mcp = " src/` → 0 Treffer
