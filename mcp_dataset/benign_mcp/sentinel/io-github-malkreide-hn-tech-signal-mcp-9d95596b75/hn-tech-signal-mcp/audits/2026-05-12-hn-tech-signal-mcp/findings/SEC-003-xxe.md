# Finding: SEC-003 — Unsicheres XML-Parsing der arXiv-Antwort

| Feld | Wert |
|---|---|
| **Severity** | **medium** |
| **Status** | closed (re-audit 2026-05-12) |
| **Server** | `hn-tech-signal-mcp` |
| **Check-Reference** | `SEC-011` (Untrusted Input Parsing) |
| **Audit-Datum** | 2026-05-12 |
| **Auditor** | Claude (mcp-audit-skill) |

### Observed Behavior

`src/hn_tech_signal_mcp/server.py:27` importiert `xml.etree.ElementTree` und
parst die arXiv-Antwort in `_fetch_arxiv` (Zeile 198-211) via
`ElementTree.fromstring(xml_text)`. Die offizielle Python-Doku empfiehlt
ausdrücklich `defusedxml` für externe XML-Inputs.

### Expected Behavior

Externes XML wird ausschliesslich mit `defusedxml.ElementTree.fromstring`
geparst, um XXE-, External-Entity- und Billion-Laughs-Angriffe zu blockieren.

### Evidence

- `src/hn_tech_signal_mcp/server.py:27` — `from xml.etree import ElementTree`
- `src/hn_tech_signal_mcp/server.py:209` — `root = ElementTree.fromstring(xml_text)`
- `pyproject.toml` — `defusedxml` nicht in Dependencies

### Risk Description

arXiv selbst ist vertrauenswürdig, aber:
- TLS-MITM-Szenarien (Corp-Proxy, kompromittierte CA) können den Response-Body manipulieren.
- DNS-Hijack auf `export.arxiv.org` würde dem Angreifer beliebige XML-Payloads erlauben.
- Ein Billion-Laughs-Payload würde den Python-Prozess in die Speicher-Knie zwingen → DoS für den lokalen MCP-Client.

Realistic Severity: **medium** — ausgenutzt nur bei Netzwerkpfad-Kompromittierung,
aber Fix ist trivial.

### Remediation

```diff
- from xml.etree import ElementTree
+ from defusedxml import ElementTree
```

```diff
 # pyproject.toml
 dependencies = [
     "fastmcp>=2.0.0",
     "httpx>=0.27.0",
     "pydantic>=2.0.0",
+    "defusedxml>=0.7.1",
 ]
```

### Effort Estimate

**S** — < 1 Stunde.

### Verification After Fix

- `pytest tests/` weiterhin grün
- Bösartiges XML in Unit-Test (entity expansion) wirft kontrolliert
