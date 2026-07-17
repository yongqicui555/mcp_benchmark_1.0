# Finding — CH-001 / Data residency documentation

**Check:** CH-001 — revDSG / EDÖB data residency (Switzerland / EU/EEA)
**Status:** PARTIAL
**Severity:** medium
**File:** `README.md:131-141`

## Evidence

The README recommends Render.com as the cloud deployment target without specifying a region:

```
**Render.com (recommended):**
1. Push/fork the repository to GitHub
2. On render.com: New Web Service → connect GitHub repo
3. Set start command: python -m swiss_cultural_heritage_mcp.server --http --port 8000
```

Render's default region is `Oregon (US-West)`. The server processes no PII, so revDSG Art. 16 (cross-border transfer of personal data) is not strictly engaged — but:
- Request logs (query strings: artist names, search topics) may incidentally contain user-identifying patterns when accessed from a workstation
- The README explicitly targets `Schulamt` / public-sector users via the educational prompts — Swiss cantonal IT policies typically require CH/EU hosting regardless of PII status
- The audit framework treats CH-001 as critical for any public-sector-adjacent server

## Impact

- Public-sector deployers may unknowingly select a US region
- No documented processing inventory or hosting-region requirement

## Remediation

1. In the Render section, explicitly recommend region `Frankfurt` (EU) and add a one-line note: *"For Swiss public-sector use (Schulamt, cantonal admin) select an EU/EEA region; US regions are not compliant with revDSG / EDÖB guidance."*
2. Add a short `docs/data-residency.md` with the four CH-001 verification items (region, logging endpoint, third-party APIs, processing inventory).
3. If logging is added later (see OBS findings), default to EU endpoints (e.g., `*.eu.sentry.io`).

**Effort:** XS (< 1 hour)
