## Finding: SEC-005 — DNS-Rebinding-Prevention: DNS-Pinning gegen TOCTOU

**Severity:** high
**Status:** open
**Check-Status:** partial
**Server:** zh-education-mcp
**Check-Reference:** SEC-005
**PDF-Reference:** Sec 4.4

### Observed Behavior / Evidence
- Fixer, vertrauenswürdiger Host (BISTA) reduziert DNS-Rebinding-Risiko erheblich
- verify=False wird NICHT verwendet (grep: none)

### Gaps (Abweichung vom Best-Practice-Katalog)
- Kein DNS-Pinning; httpx-Default impliziert separate Lookups
- follow_redirects=True erweitert die Lookup-Fläche
- Kein Test, der 1 DNS-Call pro Request verifiziert

### Effort Estimate
M  (S < 1d · M 1-3d · L 1-2w · XL >2w)
