## Finding: ARCH-011 — Repo-Struktur: tools/-Aufteilung bei > 5 Tools

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Server** | `swiss-cultural-heritage-mcp` |
| **Check-Reference** | `ARCH-011` |
| **PDF-Reference** | Sec 2.x |
| **Audit-Datum** | 2026-06-02 |
| **Auditor** | Claude (mcp-audit-skill) |

### Observed Behavior

- All mandatory top-level files present: README.md, README.de.md, CHANGELOG.md, LICENSE, pyproject.toml
- src/ layout correct, tests/ and .github/workflows/ present
- README.de.md mirrors README.md sections
- CI (ci.yml) + publish.yml present

### Gaps vs. Pass Criteria

- 8 tools in a single server.py (>5-tool threshold) with no tools/ package split and no README justification for the deviation

### Expected Behavior

With more than 5 tools, split tool definitions into a tools/ package (file per group), or justify the single-file layout in the README.

### Risk Description

A 1300-line single module is harder to navigate and review; the >5-tool guideline exists to keep per-group ownership clear.

### Remediation

Either split server.py into `tools/sik_isea.py`, `tools/snm.py`, `tools/nb.py`, `tools/cross.py` registered on the shared `mcp`, or add a short 'Project Structure' note in README explaining the deliberate single-file choice.

### Effort Estimate

**S**  (S < 1d · M 1–3d · L 1–2w · XL > 2w)

### Verification After Fix

Re-run check `ARCH-011` from the mcp-audit-skill catalog; add/adjust the pytest case noted in the remediation where applicable.
