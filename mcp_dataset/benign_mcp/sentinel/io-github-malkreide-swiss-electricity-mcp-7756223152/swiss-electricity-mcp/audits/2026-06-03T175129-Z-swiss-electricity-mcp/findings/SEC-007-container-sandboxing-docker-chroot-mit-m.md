## Finding: SEC-007 — Container-Sandboxing: Docker / chroot mit minimalen Privilegien

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Check-Status** | fail |
| **Server** | `swiss-electricity-mcp` |
| **Check-Reference** | `SEC-007` |
| **PDF-Reference** | Sec 4.5 |
| **Audit-Datum** | 2026-06-03 |
| **Auditor** | mcp-audit-skill v1.0.0 (Katalog v0.5.0) |

### Observed Behavior

- deployment enthaelt local-stdio/Railway/Render -> Sandboxing anwendbar

### Gaps / Abweichung vom Pass-Kriterium

- Kein Dockerfile -> kein non-root USER (>=10000), kein readOnlyRootFilesystem, kein capabilities.drop, kein seccomp-Profil

### Risk Description

Lokale stdio-Server (siehe SEC-006) eliminieren die Netzwerk-Angriffsfläche, behalten aber das Risiko, dass ein kompromittierter Server-Code (durch Supply-Chain-Attack, böswilliges Update, oder Bug-Exploitation) mit User-Privilegien ausgeführt wird. Read-Zugriff auf `~/.ssh/`, `~/.aws/credentials`, Browser-Cookies, lokal gespeicherte Tokens — alles direkt erreichbar.

### Remediation

### Schritt 1: Dockerfile-User anpassen

Wie im Pass-Pattern oben.

### Schritt 2: Kubernetes-SecurityContext setzen

Im Helm-Chart oder Deployment-Manifest.

### Schritt 3: Tests gegen Privileg-Eskalation

```python
def test_container_runs_as_non_root():
    result = subprocess.run(
        ["docker", "exec", CONTAINER_ID, "id", "-u"],
        capture_output=True, text=True,
    )
    assert int(result.stdout.strip()) >= 10000

def test_filesystem_read_only():
    result = subprocess.run(
        ["docker", "exec", CONTAINER_ID, "touch", "/etc/test"],
        capture_output=True, text=True,
    )
    assert "Read-only" in result.stderr or result.returncode != 0
```

### Schritt 4: CI-Check via Trivy / Snyk

```yaml
- name: Container security scan
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: malkreide/mcp-server:${{ github.sha }}
    severity: CRITICAL,HIGH
    exit-code: 1
```

### Effort Estimate

S — < 1 Tag bei sauberem Dockerfile-Setup. Bei Legacy-Container mit root-Defaults: 1–2 Tage.

### Verification After Fix

- Re-Audit von `SEC-007` via `/audit-mcp`
- Pytest-/grep-Guard gegen das Anti-Pattern (wo automatisierbar)
