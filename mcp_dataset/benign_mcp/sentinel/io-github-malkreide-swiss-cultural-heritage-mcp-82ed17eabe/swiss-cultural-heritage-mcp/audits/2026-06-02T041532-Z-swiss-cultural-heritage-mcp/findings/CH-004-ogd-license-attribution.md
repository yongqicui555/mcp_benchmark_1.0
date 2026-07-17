## Finding: CH-004 — OGD-CH Lizenz-Compliance: CC BY Attribution pro Datensatz

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Server** | `swiss-cultural-heritage-mcp` |
| **Check-Reference** | `CH-004` |
| **PDF-Reference** | CH custom |
| **Audit-Datum** | 2026-06-02 |
| **Auditor** | Claude (mcp-audit-skill) |

### Observed Behavior

- README documents all three sources and notes open licences (CC0/CC BY, README.md:241)
- Per-record SIKART links and NUTZUNGSLIZENZ/rights fields surfaced in detail views (server.py:440,974)

### Gaps vs. Pass Criteria

- Tool responses carry no consistent structured source+licence field per dataset; provenance is incidental, not guaranteed per record (esp. in cross_search aggregation)

### Expected Behavior

Tool responses carry a structured source+licence field per dataset; provenance preserved per record in aggregation; attribution text per the licence (author, source, licence).

### Risk Description

Open-government data under CC BY requires attribution; aggregated answers that drop the source/licence per record put the consumer at risk of a licence breach.

### Remediation

Add a `source` block (`{name, url, license}`) to every JSON response and a footer line in markdown; in `heritage_cross_search` keep provenance per item, not just per section header.

### Effort Estimate

**S**  (S < 1d · M 1–3d · L 1–2w · XL > 2w)

### Verification After Fix

Re-run check `CH-004` from the mcp-audit-skill catalog; add/adjust the pytest case noted in the remediation where applicable.
