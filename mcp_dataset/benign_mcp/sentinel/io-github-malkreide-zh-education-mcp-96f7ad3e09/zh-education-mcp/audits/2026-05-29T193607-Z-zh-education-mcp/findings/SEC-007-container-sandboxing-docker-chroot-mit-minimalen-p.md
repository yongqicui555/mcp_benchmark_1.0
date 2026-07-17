## Finding: SEC-007 — Container-Sandboxing: Docker / chroot mit minimalen Privilegien

**Severity:** high
**Status:** open
**Check-Status:** fail
**Server:** zh-education-mcp
**Check-Reference:** SEC-007
**PDF-Reference:** Sec 4.5

### Observed Behavior / Evidence
- Profil deployment enthält local-stdio + Cloud ⇒ Check anwendbar

### Gaps (Abweichung vom Best-Practice-Katalog)
- Kein Dockerfile/k8s-Manifest ⇒ kein non-root USER, kein readOnlyRootFilesystem, keine capabilities.drop, kein seccomp-Profil
- Cloud-Deployment ohne jegliche Sandboxing-Definition

### Effort Estimate
M  (S < 1d · M 1-3d · L 1-2w · XL >2w)
