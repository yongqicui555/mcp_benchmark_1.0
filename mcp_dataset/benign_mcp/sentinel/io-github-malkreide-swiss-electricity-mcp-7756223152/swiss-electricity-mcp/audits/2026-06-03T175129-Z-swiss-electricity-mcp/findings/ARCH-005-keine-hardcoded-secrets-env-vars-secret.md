## Finding: ARCH-005 — Keine Hardcoded Secrets: Env-Vars / Secret Manager only

| Feld | Wert |
|---|---|
| **Severity** | critical |
| **Status** | open |
| **Check-Status** | partial |
| **Server** | `swiss-electricity-mcp` |
| **Check-Reference** | `ARCH-005` |
| **PDF-Reference** | Sec 2.1 |
| **Audit-Datum** | 2026-06-03 |
| **Auditor** | mcp-audit-skill v1.0.0 (Katalog v0.5.0) |

### Observed Behavior

- Keine Hardcoded Secrets im Source (grep ueber src/ negativ)
- Server benoetigt gar keine Secrets (auth_model=none, nur Public Open Data)
- Keine os.environ.get(..., default=<secret>)-Pattern

### Gaps / Abweichung vom Pass-Kriterium

- Keine .gitignore mit .env/.env.* im Repo
- Keine .env.example
- Kein CI-Secret-Scan (Gitleaks/Trufflehog) - .github/workflows fehlt komplett

### Risk Description

Hardcoded Secrets (API-Keys, Passwörter, Tokens, Connection-Strings, Encryption-Keys) im Source-Code sind die häufigste vermeidbare Sicherheitsschwäche in MCP-Server-Repositories. Sobald das Repo öffentlich ist (oder versehentlich öffentlich wird), oder ein Mitarbeiter aus dem Team ausscheidet, sind alle Secrets kompromittiert.

### Remediation

### Schritt 1: Bestehende Secrets identifizieren und ersetzen

```bash
# Lokale Suche (vor jeglichem Push)
gitleaks detect --source . --verbose

# Falls schon committed: History-Rewrite ZUSÄTZLICH zur Schlüssel-Rotation
# Wichtig: rotation FIRST, history-rewrite zweitrangig
```

### Schritt 2: Migration zu Pydantic-Settings

```python
# Vorher
API_KEY = "sk-1234..."

# Nachher
from pydantic import SecretStr
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    api_key: SecretStr
    model_config = {"env_file": ".env", "extra": "forbid"}

settings = Settings()
# Im Code: settings.api_key.get_secret_value()
```

### Schritt 3: `.env.example` mit Platzhaltern

```bash
# .env.example (committet)
API_KEY=replace-with-real-key
DATABASE_URL=postgresql://user:pass@localhost/dbname
OAUTH_CLIENT_SECRET=at-least-32-characters-long-secret

# .env (NICHT committet, in .gitignore)
API_KEY=sk-actual-real-key
...
```

### Schritt 4: Production-Secret-Manager (höhere Reife)

| Plattform | Mechanismus |
|---|---|
| Railway | Project-Variables (verschlüsselt at-rest) |
| Render | Environment-Groups |
| Kubernetes | `Secret`-Objects + `secretKeyRef` in Pod-Spec |
| Self-Hosted | HashiCorp Vault, AWS Secrets Manager (EU-Region!), GCP Secret Manager |

```python
# AWS Secrets Manager (EU-Region für DSG, siehe CH-001)
import boto3
import json

def load_secret(name: str) -> dict:
    client = boto3.client("secretsmanager", region_name="eu-central-1")
    response = client.get_secret_value(SecretId=name)
    return json.loads(response["SecretString"])

secrets = load_secret("schulamt-mcp/production")
api_key = secrets["api_key"]
```

### Schritt 5: CI-Scan einrichten

Siehe Modus 5 oben.

### Schritt 6: Pre-Commit-Hook lokal

```yaml
# .pre-commit-config.yaml
repos:

_(... vollstaendige Remediation siehe checks/ARCH-005.md)_

### Effort Estimate

S–M — Bei sauberem Repo: < 1 Tag (Settings-Migration + CI-Setup). Bei Repo mit Secret-Leak in History: 2–3 Tage (Rotation aller Schlüssel, History-Rewrite, Audit aller Forks/Clones).

### Verification After Fix

- Re-Audit von `ARCH-005` via `/audit-mcp`
- Pytest-/grep-Guard gegen das Anti-Pattern (wo automatisierbar)
