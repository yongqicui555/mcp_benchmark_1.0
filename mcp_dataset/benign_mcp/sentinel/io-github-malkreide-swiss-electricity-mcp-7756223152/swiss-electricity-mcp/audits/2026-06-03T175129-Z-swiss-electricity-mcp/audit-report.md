# MCP-Server Audit-Report — `swiss-electricity-mcp`

**Audit-Datum:** 2026-06-03
**Skill-Version:** 1.0.0
**Catalog-Version:** 0.5.0 (catalog_hash 091f446b)

---

## 1. Executive Summary

Server `swiss-electricity-mcp` wurde gegen 44 anwendbare Best-Practice-Checks geprüft. 10 bestanden, 28 Findings dokumentiert (4 critical, 13 high, 11 medium, 0 low). Production-Readiness: NICHT erreicht — blockierend: ARCH-009, SDK-001, SEC-007, SEC-016.

**Production-Readiness:** NO

---

## 2. Profil-Snapshot

| Feld | Wert |
|---|---|
| Server-Name | `swiss-electricity-mcp` |
| Audit-Datum | 2026-06-03 |
| Skill-Version | 1.0.0 |
| Catalog-Version | 0.5.0 (catalog_hash 091f446b) |
| transport | `dual` |
| auth_model | `none` |
| data_class | `Public Open Data` |
| write_capable | `False` |
| deployment | `['local-stdio', 'Render', 'Railway', 'andere']` |
| uses_sampling | `False` |
| tools_make_external_requests | `True` |
| stadt_zuerich_context | `False` |
| schulamt_context | `False` |
| data_source.is_swiss_open_data | `True` |

---

## 3. Applicability

### Status pro Kategorie

| Kategorie | Pass | Fail | Partial | Todo | N/A |
|---|---|---|---|---|---|
| ARCH | 3 | 2 | 6 | 0 | 0 |
| CH | 1 | 0 | 0 | 0 | 0 |
| OBS | 1 | 2 | 2 | 0 | 0 |
| OPS | 0 | 0 | 3 | 0 | 0 |
| SCALE | 1 | 1 | 0 | 3 | 0 |
| SDK | 1 | 1 | 2 | 0 | 0 |
| SEC | 3 | 2 | 7 | 3 | 0 |
| **Total** | **10** | **8** | **20** | **6** | **0** |

---

## 4. Findings-Übersicht

_Policy: `fail-or-partial`_

| ID | Category | Severity | Status |
|---|---|---|---|
| ARCH-005 | ARCH | critical | partial |
| SEC-004 | SEC | critical | partial |
| SEC-016 | SEC | critical | fail |
| SEC-019 | SEC | critical | partial |
| ARCH-004 | ARCH | high | partial |
| ARCH-009 | ARCH | high | fail |
| OBS-001 | OBS | high | partial |
| OBS-002 | OBS | high | partial |
| OPS-001 | OPS | high | partial |
| OPS-003 | OPS | high | partial |
| SDK-001 | SDK | high | fail |
| SDK-004 | SDK | high | partial |
| SEC-005 | SEC | high | partial |
| SEC-007 | SEC | high | fail |
| SEC-018 | SEC | high | partial |
| SEC-021 | SEC | high | partial |
| SEC-022 | SEC | high | partial |
| ARCH-003 | ARCH | medium | partial |
| ARCH-007 | ARCH | medium | partial |
| ARCH-008 | ARCH | medium | partial |
| ARCH-011 | ARCH | medium | fail |
| ARCH-012 | ARCH | medium | partial |
| OBS-003 | OBS | medium | fail |
| OBS-006 | OBS | medium | fail |
| OPS-002 | OPS | medium | partial |
| SCALE-004 | SCALE | medium | fail |
| SDK-003 | SDK | medium | partial |
| SEC-008 | SEC | medium | partial |

**Gesamt:** 28 Findings

---

## 5. Detail-Findings

### ARCH-003

## Finding: ARCH-003 — «Not Found» Anti-Pattern: Heuristiken statt leerer Antworten

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Check-Status** | partial |
| **Server** | `swiss-electricity-mcp` |
| **Check-Reference** | `ARCH-003` |
| **PDF-Reference** | Sec 2.2 |
| **Audit-Datum** | 2026-06-03 |
| **Auditor** | mcp-audit-skill v1.0.0 (Katalog v0.5.0) |

### Observed Behavior

- Such-Tools consumption_search_zurich / consumption_search_bfe_datasets vorhanden (server.py:484, :534)
- Leere Treffer liefern leere datasets-Liste + total_hits=0

### Gaps / Abweichung vom Pass-Kriterium

- Kein match_type-Feld (exact/fuzzy/none) in DatasetSearchResponse
- Kein Fuzzy-Fallback und kein actionable Suggestion-Mechanismus bei 0 Treffern

### Risk Description

LLMs reagieren empirisch nachweisbar empfindlich auf negativ-framing in Tool-Responses. Eine Antwort wie `"No results found"` oder `[]` ohne Kontext führt häufig zu einer von zwei Failure-Modes:

### Remediation

```diff
  @mcp.tool()
  async def find_school(name: str) -> list:
      results = await db.find(name)
-     if not results:
-         return []
+     if not results:
+         fuzzy = await db.find_fuzzy(name, threshold=0.7)
+         suggestions = await db.popular_school_names_starting_with(name[:3])
+         return {
+             "results": fuzzy[:5],
+             "match_type": "fuzzy" if fuzzy else "none",
+             "note": (
+                 f"Keine exakten Treffer für '{name}'. "
+                 f"{'Ähnliche Schulen aufgeführt.' if fuzzy else ''} "
+                 f"Häufige Schulnamen: {', '.join(suggestions[:5])}"
+             ),
+         }
      return {"results": results, "match_type": "exact"}
```

### Effort Estimate

S — Pro Tool ~30 Minuten. Bei 10 Such-Tools: 1 Tag.

### Verification After Fix

- Re-Audit von `ARCH-003` via `/audit-mcp`
- Pytest-/grep-Guard gegen das Anti-Pattern (wo automatisierbar)


### ARCH-004

## Finding: ARCH-004 — Inversion of Control: Transport-agnostische Server-Logik

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Check-Status** | partial |
| **Server** | `swiss-electricity-mcp` |
| **Check-Reference** | `ARCH-004` |
| **PDF-Reference** | Sec 2.1 |
| **Audit-Datum** | 2026-06-03 |
| **Auditor** | mcp-audit-skill v1.0.0 (Katalog v0.5.0) |

### Observed Behavior

- ENV-basierte Transport-Selektion stdio + streamable-http (__main__.py:16-24)
- Identische Tool-Outputs unabhaengig vom Transport

### Gaps / Abweichung vom Pass-Kriterium

- Konfiguration ueber Module-Globals (_dashboard/_elcom/_ckan, server.py:70-72) statt Pydantic-Settings
- Kein gemeinsamer Lifespan/Setup-Code (siehe SDK-001)
- Tool-Handler nutzen keinen ctx: Context (siehe SDK-003)

### Risk Description

Die MCP-Spezifikation trennt strikt zwischen Data Layer (JSON-RPC 2.0, Tools/Resources/Prompts) und Transport Layer (stdio / Streamable HTTP / SSE). Der Best-Practice-Standard verlangt, dass die Geschäftslogik des Servers diese Trennung respektiert: Tool-Handler müssen **transport-agnostisch** sein. Derselbe `searchData()`-Tool-Handler muss identisch funktionieren, egal ob er via stdio (Claude Desktop) oder SSE (Cloud-Deployment) aufgerufen wird.

### Remediation

Migrationsweg von monolithischem Setup zu IoC:

```diff
+ from pydantic_settings import BaseSettings
+ from contextlib import asynccontextmanager
+
+ class Settings(BaseSettings):
+     transport: str = "stdio"
+     host: str = "127.0.0.1"
+     port: int = 8000
+
+ @asynccontextmanager
+ async def lifespan(server):
+     # Shared setup für alle Transports
+     server.state.http_client = httpx.AsyncClient(timeout=30)
+     try:
+         yield
+     finally:
+         await server.state.http_client.aclose()
+
- mcp = FastMCP("server")
+ settings = Settings()
+ mcp = FastMCP("server", lifespan=lifespan)

  @mcp.tool()
- async def search(query: str, request: Request):
-     ua = request.headers["User-Agent"]
-     ...
+ async def search(query: str, ctx: Context):
+     client_name = ctx.client_info.name
+     ...

  if __name__ == "__main__":
-     mcp.run(transport="stdio")
+     if settings.transport == "sse":
+         mcp.settings.host = settings.host
+         mcp.settings.port = settings.port
+     mcp.run(transport=settings.transport)
```

### Effort Estimate

M — 1–3 Tage. Refactoring der Transport-Auswahl, Migration aller `request`-Zugriffe auf `ctx`, Testing in beiden Modi.

### Verification After Fix

- Re-Audit von `ARCH-004` via `/audit-mcp`
- Pytest-/grep-Guard gegen das Anti-Pattern (wo automatisierbar)


### ARCH-005

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


### ARCH-007

## Finding: ARCH-007 — Capability-Aggregation: Composability intern, Atomarität extern

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Check-Status** | partial |
| **Server** | `swiss-electricity-mcp` |
| **Check-Reference** | `ARCH-007` |
| **PDF-Reference** | Sec 2.3 |
| **Audit-Datum** | 2026-06-03 |
| **Auditor** | mcp-audit-skill v1.0.0 (Katalog v0.5.0) |

### Observed Behavior

- Tools liefern abgeschlossene Resultate (vollstaendige Envelopes, keine reinen IDs/Pointer)
- Aggregations-Tool tariff_compare_municipalities vorhanden (server.py:442)

### Gaps / Abweichung vom Pass-Kriterium

- tariff_compare_municipalities iteriert Gemeinden sequenziell in einer for-Schleife (server.py:451) statt asyncio.gather - bei 20 BFS-Nrn unnoetig langsam

### Risk Description

Eng verwandt zu ARCH-006, aber mit anderem Fokus: **Wo ARCH-006 sagt «weniger Tools, höhere Use-Cases», sagt ARCH-007 «aus LLM-Sicht atomar, intern composable».**

### Remediation

```diff
- @mcp.tool()
- async def get_motion_id(title: str) -> str: ...
-
- @mcp.tool()
- async def get_motion_details(motion_id: str) -> dict: ...
-
- @mcp.tool()
- async def get_motion_tags(motion_id: str) -> list: ...

+ @mcp.tool(
+     name="findMotionWithDetails",
+     description=(
+         "Sucht eine parlamentarische Motion anhand des Titels und liefert "
+         "vollständige Details inkl. Tags, Status, Eingebenden. "
+         "Aggregiert intern Suchindex + Detail-API + Tag-API."
+     ),
+ )
+ async def find_motion_with_details(title: str, ctx: Context) -> dict:
+     motion_ids = await api.search_motion_ids(title, limit=5)
+     if not motion_ids:
+         return {"results": [], "match_type": "none", "note": "..."}  # ARCH-003
+     # Parallel Details + Tags für alle Treffer
+     detail_tasks = [api.get_motion_details(mid) for mid in motion_ids]
+     tag_tasks = [api.get_motion_tags(mid) for mid in motion_ids]
+     details, tags = await asyncio.gather(
+         asyncio.gather(*detail_tasks),
+         asyncio.gather(*tag_tasks),
+     )
+     return {
+         "results": [
+             {**d, "tags": t} for d, t in zip(details, tags)
+         ],
+         "match_type": "exact",
+         "count": len(details),
+     }
```

### Effort Estimate

M — 1–3 Tage. Identifikation der Aggregations-Möglichkeiten + Refactoring + Performance-Tests.

### Verification After Fix

- Re-Audit von `ARCH-007` via `/audit-mcp`
- Pytest-/grep-Guard gegen das Anti-Pattern (wo automatisierbar)


### ARCH-008

## Finding: ARCH-008 — Drei Primitive nutzen: Tools, Resources und Prompts

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Check-Status** | partial |
| **Server** | `swiss-electricity-mcp` |
| **Check-Reference** | `ARCH-008` |
| **PDF-Reference** | Anhang A2 |
| **Audit-Datum** | 2026-06-03 |
| **Auditor** | mcp-audit-skill v1.0.0 (Katalog v0.5.0) |

### Observed Behavior

- Server nutzt das Primitive Tools sauber und konsistent

### Gaps / Abweichung vom Pass-Kriterium

- Nur Tools, keine Resources oder Prompts
- README dokumentiert nicht, warum keine Resources/Prompts (read-only, idempotente Tools waeren Resource-Migrations-Kandidaten)

### Risk Description

MCP definiert drei orthogonale Primitive, von denen die meisten Server nur eines nutzen:

### Remediation

### Schritt 1: Tools-zu-Resources-Audit

Pro Tool prüfen:

```
- Hat Side-Effects? → Tool bleibt
- Ist deterministisch und idempotent? → Resource-Kandidat
- Liefert primär Kontextdaten zum Lesen? → Resource-Kandidat
```

### Schritt 2: URI-Schema definieren

Pro Resource-Klasse ein konsistentes Schema:

```
school://<school_id>/profile
school://<school_id>/classes/<year>
luftqualitaet://<school_id>/<date>
budget://<school_id>/<year>
```

### Schritt 3: Migration

```diff
- @mcp.tool()
- async def get_school_profile(school_id: str) -> dict:
-     return await db.get_school_profile(school_id).dict()

+ @mcp.resource("school://{school_id}/profile")
+ async def school_profile(school_id: str) -> str:
+     profile = await db.get_school_profile(school_id)
+     return profile.as_markdown()
```

### Schritt 4: Prompts-Inventar

Falls wiederkehrende Workflows existieren: pro Workflow ein Prompt-Template, ins README dokumentieren.

### Effort Estimate

M — 1–3 Tage. Audit + Migration einer Handvoll Tools + Doku.

### Verification After Fix

- Re-Audit von `ARCH-008` via `/audit-mcp`
- Pytest-/grep-Guard gegen das Anti-Pattern (wo automatisierbar)


### ARCH-009

## Finding: ARCH-009 — Tool Annotations: readOnlyHint, destructiveHint, idempotentHint, openWorldHint

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Check-Status** | fail |
| **Server** | `swiss-electricity-mcp` |
| **Check-Reference** | `ARCH-009` |
| **PDF-Reference** | Anhang A5 |
| **Audit-Datum** | 2026-06-03 |
| **Auditor** | mcp-audit-skill v1.0.0 (Katalog v0.5.0) |

### Observed Behavior

- grep auf readOnlyHint/destructiveHint/idempotentHint/openWorldHint in src/ = 0 Treffer
- Alle 11 @mcp.tool-Decorators setzen nur description, keine annotations (server.py:119, :163, :248, ...)

### Gaps / Abweichung vom Pass-Kriterium

- KEINE Tool-Annotations vorhanden - alle Tools sind read-only und externe-Aufrufe, sollten readOnlyHint=true und openWorldHint=true deklarieren
- Clients koennen read-only-Charakter nicht aus Annotations ableiten

### Risk Description

Die MCP-Spec von 2025-03-26 hat **Tool Annotations** eingeführt — strukturierte Hints, die Hosts (z.B. Claude Desktop) für UI-Entscheidungen verwenden:

### Remediation

### Schritt 1: Annotations-Inventar

Pro Tool eine Tabelle mit den vier Hints. Wenn unsicher: per Default konservativ (alles `false`/weggelassen impliziert «kann gefährlich sein»).

### Schritt 2: Decorator-Helper

```python
from typing import Literal

def read_only_tool(*args, **kwargs):
    """Shortcut für read-only Tools mit konsistenten Annotations."""
    annotations = kwargs.pop("annotations", {})
    annotations.update({
        "readOnlyHint": True,
        "idempotentHint": True,
        "openWorldHint": False,
    })
    kwargs["annotations"] = annotations
    return mcp.tool(*args, **kwargs)


@read_only_tool()
async def search_motions(args, ctx):
    ...
```

### Schritt 3: CI-Test gegen Drift

```python
def test_destructive_tools_have_destructive_hint():
    """Tools mit delete/create/update im Namen müssen destructiveHint setzen."""
    suspicious_prefixes = ("delete_", "create_", "update_", "remove_")
    for tool_name, tool in mcp.tools.items():
        if any(tool_name.startswith(p) for p in suspicious_prefixes):
            annotations = tool.annotations or {}
            assert annotations.get("readOnlyHint") is not True, (
                f"{tool_name} suggests write but is marked readOnlyHint"
            )
```

### Effort Estimate

S — < 1 Tag. Annotations-Inventar + Decorator + Tests.

### Verification After Fix

- Re-Audit von `ARCH-009` via `/audit-mcp`
- Pytest-/grep-Guard gegen das Anti-Pattern (wo automatisierbar)


### ARCH-011

## Finding: ARCH-011 — Standardisierte Repo-Struktur (src-Layout, tests, README.de.md)

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Check-Status** | fail |
| **Server** | `swiss-electricity-mcp` |
| **Check-Reference** | `ARCH-011` |
| **PDF-Reference** | Anhang A8 |
| **Audit-Datum** | 2026-06-03 |
| **Auditor** | mcp-audit-skill v1.0.0 (Katalog v0.5.0) |

### Observed Behavior

- Pflicht-Files vorhanden: README.md, README.de.md, CHANGELOG.md, LICENSE, pyproject.toml
- Korrektes src-Layout (src/swiss_electricity_mcp/), tests/ vorhanden

### Gaps / Abweichung vom Pass-Kriterium

- .github/workflows/ fehlt komplett - keine test.yml, keine publish.yml
- Kein CI ohne Live-Tests, kein automatisches Publishing

### Risk Description

Aus dem Schweizer Public-Data-Portfolio bewährt sich ein konsistentes Repo-Layout. Das ist nicht nur Code-Schönheit — es ist Operational Discipline:

### Remediation

### Schritt 1: Migration zu src-Layout (falls flat)

```bash
mkdir -p src
git mv my_module src/my_module
# pyproject.toml anpassen:
# [tool.hatch.build.targets.wheel]
# packages = ["src/my_module"]
```

### Schritt 2: README.de.md initial befüllen

Wenn nur `README.md` existiert, mit Übersetzung beginnen — mindestens Top-Level-Sektionen synchron halten.

### Schritt 3: CI-Workflows aufsetzen

`.github/workflows/test.yml`:

```yaml
name: Tests
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-python@v6
        with:
          python-version: "3.11"
      - run: pip install -e ".[dev]"
      - run: pytest -m "not live"
```

### Schritt 4: Tools aufteilen

Bei > 5 Tools:

```diff
  src/server_name/
+ ├── tools/
+ │   ├── __init__.py
+ │   ├── search.py        # search_motions, search_authors
+ │   ├── statistics.py    # aggregate_*, count_*
+ │   └── notifications.py # send_*
- └── server.py            # vorher 800 Zeilen
+ └── server.py            # nur Registry, ~100 Zeilen
```

### Effort Estimate

S — < 1 Tag bei einzelnem Server. M — 1 Woche bei portfolio-weitem Roll-out (29 Server).

### Verification After Fix

- Re-Audit von `ARCH-011` via `/audit-mcp`
- Pytest-/grep-Guard gegen das Anti-Pattern (wo automatisierbar)


### ARCH-012

## Finding: ARCH-012 — protocolVersion-Pinning + CHANGELOG + SDK-Update-Disziplin

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Check-Status** | partial |
| **Server** | `swiss-electricity-mcp` |
| **Check-Reference** | `ARCH-012` |
| **PDF-Reference** | Anhang A9 |
| **Audit-Datum** | 2026-06-03 |
| **Auditor** | mcp-audit-skill v1.0.0 (Katalog v0.5.0) |

### Observed Behavior

- CHANGELOG.md vorhanden (Keep-a-Changelog-naher Stil)
- mcp[cli]>=1.2.0 als Dependency gepinnt (pyproject.toml)

### Gaps / Abweichung vom Pass-Kriterium

- protocolVersion wird im Code nicht explizit gepinnt (FastMCP-Default)
- Keine README-Sektion 'MCP Protocol Version' mit Update-Policy
- Kein Dependabot/Renovate (.github fehlt)

### Risk Description

Die MCP-Spec hat in 13 Monaten vier Major-Updates erlebt (2024-11, 2025-03, 2025-06, 2025-11). Das ist eine ungewöhnlich hohe Velocity für einen Industriestandard. Konkrete Folgen für Server-Maintainer:

### Remediation

### Schritt 1: protocolVersion pinnen

```diff
+ from importlib.metadata import version

  mcp = FastMCP(
      name="zh-education-mcp",
+     protocol_version="2025-06-18",
  )
```

### Schritt 2: CHANGELOG initialisieren

Wenn nicht vorhanden, mit Template starten und retroaktiv Major-Versionen dokumentieren (mindestens letzte 3).

### Schritt 3: Dependabot konfigurieren

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "monthly"
    open-pull-requests-limit: 5
```

### Schritt 4: Quartalsweise Spec-Review

Im Audit-Tracker (Notion) oder GitHub Issues ein recurring Reminder für quartalsweise Spec-Velocity-Review:

- Was hat sich an der MCP-Spec geändert seit letztem Release?
- Welche Server müssen ihre `protocolVersion` aktualisieren?
- Gibt es Compliance-relevante Spec-Änderungen?

### Effort Estimate

S — < 1 Tag pro Server. Pinning + CHANGELOG-Template + Dependabot-Setup.

### Verification After Fix

- Re-Audit von `ARCH-012` via `/audit-mcp`
- Pytest-/grep-Guard gegen das Anti-Pattern (wo automatisierbar)


### OBS-001

## Finding: OBS-001 — Protocol vs. Execution Errors: korrekte Trennung

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Check-Status** | partial |
| **Server** | `swiss-electricity-mcp` |
| **Check-Reference** | `OBS-001` |
| **PDF-Reference** | Sec 6.1 |
| **Audit-Datum** | 2026-06-03 |
| **Auditor** | mcp-audit-skill v1.0.0 (Katalog v0.5.0) |

### Observed Behavior

- Anwendungsfehler werden als Exceptions geworfen und von FastMCP in isError-Tool-Results uebersetzt (UpstreamUnreachableError, server.py:496/543)
- 4xx/5xx-Differenzierung im API-Client (api_client.py:57-66)

### Gaps / Abweichung vom Pass-Kriterium

- Keine explizite isError-Behandlung im Tool-Code; Verlass auf FastMCP-Default-Wrapping
- Kein dedizierter Test fuer Protocol-Error-Pfad (falsches Tool/falsche Args) erkennbar

### Risk Description

Die MCP-Spezifikation fordert eine strikte Trennung zwischen zwei Fehler-Typen. Werden sie verwechselt, kann das LLM den Fehler nicht korrekt interpretieren und bricht in eine Halluzinations- oder Sackgassen-Schleife.

### Remediation

```diff
+ from mcp.types import TextContent
+
  @mcp.tool()
  async def query_database(query: str) -> dict:
-     # FAIL: alle Exceptions werden zu JSON-RPC-Errors
-     conn = await asyncpg.connect(DATABASE_URL)
-     return {"rows": await conn.fetch(query)}
+     try:
+         conn = await asyncpg.connect(DATABASE_URL)
+         try:
+             rows = await conn.fetch(query)
+             return {"rows": [dict(r) for r in rows]}
+         finally:
+             await conn.close()
+     except asyncpg.PostgresSyntaxError as e:
+         # Execution Error: Query-Problem ist Aufgabe des LLMs zu lösen
+         return {
+             "isError": True,
+             "content": [TextContent(
+                 type="text",
+                 text=f"SQL syntax error: {str(e)}. Try simplifying the query."
+             )],
+         }
+     except asyncpg.PostgresConnectionError:
+         # Protocol-nahe: Server ist degraded
+         raise McpError(code=-32603, message="Database temporarily unavailable")
```

### Effort Estimate

M — 1–3 Tage. Pro Tool muss der Error-Pfad reviewed werden. Bei vielen Tools (>10) entsprechend aufwändiger.

### Verification After Fix

- Re-Audit von `OBS-001` via `/audit-mcp`
- Pytest-/grep-Guard gegen das Anti-Pattern (wo automatisierbar)


### OBS-002

## Finding: OBS-002 — Mask Error Details: keine Stacktraces / SQL ans LLM

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Check-Status** | partial |
| **Server** | `swiss-electricity-mcp` |
| **Check-Reference** | `OBS-002` |
| **PDF-Reference** | Sec 6.2 |
| **Audit-Datum** | 2026-06-03 |
| **Auditor** | mcp-audit-skill v1.0.0 (Katalog v0.5.0) |

### Observed Behavior

- Keine traceback.format_exc()/sys.exc_info()-Ausgaben in Tool-Returns
- Fehlermeldungen ohne SQL/Stacktrace

### Gaps / Abweichung vom Pass-Kriterium

- FastMCP wird nicht mit mask_error_details=True initialisiert (server.py:59)
- electricity_check_status gibt Exception-Typ+Message im note-Feld zurueck (server.py:615) - leakt Internals an Client

### Risk Description

Wenn Tool-Errors Stacktraces, SQL-Syntax, Datei-Pfade oder gar Credentials enthalten, fliesst dieser Inhalt in den LLM-Kontext und damit potentiell ins User-Sichtbare zurück. Das ist Information Disclosure: Angreifer mit User-Zugriff erfahren über provozierte Errors die Server-Architektur, DB-Schema, gemountete Pfade, sogar geleakte Tokens (z.B. in `Authorization`-Headern, die im Stacktrace landen).

### Remediation

```diff
  mcp = FastMCP(
      "server",
+     mask_error_details=True,
  )

  @mcp.tool()
  async def search(query: str):
      try:
          return await db.search(query)
-     except Exception as e:
-         return {"error": str(e), "traceback": traceback.format_exc()}
+     except UserInputError as e:
+         return {"isError": True, "content": [
+             TextContent(type="text", text=f"Invalid input: {e.user_message}")
+         ]}
+     except Exception:
+         logger.exception("Unhandled error in search tool")
+         raise  # mask_error_details greift, generische Message ans LLM
```

### Effort Estimate

S — < 1 Tag pro Server.

### Verification After Fix

- Re-Audit von `OBS-002` via `/audit-mcp`
- Pytest-/grep-Guard gegen das Anti-Pattern (wo automatisierbar)


### OBS-003

## Finding: OBS-003 — Structured Logging mit RFC 5424 Severity-Stufen

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Check-Status** | fail |
| **Server** | `swiss-electricity-mcp` |
| **Check-Reference** | `OBS-003` |
| **PDF-Reference** | Sec 6.3 |
| **Audit-Datum** | 2026-06-03 |
| **Auditor** | mcp-audit-skill v1.0.0 (Katalog v0.5.0) |

### Observed Behavior

- Kein Structured-Logging-Framework (structlog/loguru) in dependencies
- grep: keine Logger-Instanz im src/-Code

### Gaps / Abweichung vom Pass-Kriterium

- Ueberhaupt kein Logging vorhanden - kein JSON/logfmt, keine Severity-Stufen, kein per-Tool-Call-Context (tool name/session_id/correlation_id)

### Risk Description

MCP-Server-Logs müssen strukturiert sein (JSON oder logfmt), nicht plaintext. Das ermöglicht Aggregation in Datadog/Splunk/Loki ohne Regex-Parsing, korrelierte Suche über Correlation-IDs, und konsistente Severity-Filterung.

### Remediation

```diff
- import logging
- logger = logging.getLogger(__name__)
+ import structlog
+ logger = structlog.get_logger("mcp.server")

  @mcp.tool()
  async def search(query: str, ctx):
-     logger.info(f"Searching for {query}")
-     result = await api.search(query)
-     logger.info(f"Got {len(result)} results")
+     log = logger.bind(tool="search", query=query, session=ctx.session_id)
+     log.info("tool_invoked")
+     result = await api.search(query)
+     log.info("tool_succeeded", count=len(result))
      return result
```

### Effort Estimate

S — < 1 Tag pro Server.

### Verification After Fix

- Re-Audit von `OBS-003` via `/audit-mcp`
- Pytest-/grep-Guard gegen das Anti-Pattern (wo automatisierbar)


### OBS-006

## Finding: OBS-006 — OpenTelemetry Distributed Tracing pro Tool-Call

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Check-Status** | fail |
| **Server** | `swiss-electricity-mcp` |
| **Check-Reference** | `OBS-006` |
| **PDF-Reference** | Anhang B10 |
| **Audit-Datum** | 2026-06-03 |
| **Auditor** | mcp-audit-skill v1.0.0 (Katalog v0.5.0) |

### Observed Behavior

- is_cloud_deployed=true -> Check anwendbar

### Gaps / Abweichung vom Pass-Kriterium

- Kein OpenTelemetry-SDK, kein TracerProvider/OTLP-Exporter
- Keine httpx-Auto-Instrumentation, keine per-Tool-Call-Spans

### Risk Description

OBS-005 deckt Audit-Logs für SIEM-Integration ab — Security-fokussiert. OBS-006 ergänzt das auf der **Performance- und Behavior-Seite**: jeder Tool-Call wird als OpenTelemetry-Span erfasst, mit:

### Remediation

### Schritt 1: SDK-Installation

```toml
# pyproject.toml
[project.dependencies]
"opentelemetry-api" = "^1.21"
"opentelemetry-sdk" = "^1.21"
"opentelemetry-exporter-otlp" = "^1.21"
"opentelemetry-instrumentation-httpx" = "^0.42b0"
```

### Schritt 2: Setup-Modul

```python
# src/server_name/observability.py
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.resources import Resource
# ...

def setup_tracing():
    resource = Resource.create({
        "service.name": os.environ.get("OTEL_SERVICE_NAME", "schulamt-mcp"),
        "deployment.environment": os.environ.get("ENVIRONMENT", "development"),
    })
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    trace.set_tracer_provider(provider)
    HTTPXClientInstrumentor().instrument()
```

### Schritt 3: Decorator anwenden

`@traced_tool` als Standard auf alle Tool-Decorators stacken.

### Schritt 4: OTLP-Backend wählen

Für Schulamt-Kontext: Datadog (DSG-konform mit `DD_SITE=datadoghq.eu`), Grafana Tempo (selbst-gehostet, OpenBao-Compatible), oder Honeycomb (EU-Region).

### Effort Estimate

M — 1–3 Tage. SDK-Setup + Decorator + Backend-Konfiguration + Tests.

### Verification After Fix

- Re-Audit von `OBS-006` via `/audit-mcp`
- Pytest-/grep-Guard gegen das Anti-Pattern (wo automatisierbar)


### OPS-001

## Finding: OPS-001 — Test-Strategie: Unit-Tests mocked + Live-Tests gemarkert

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Check-Status** | partial |
| **Server** | `swiss-electricity-mcp` |
| **Check-Reference** | `OPS-001` |
| **PDF-Reference** | Anhang C1 |
| **Audit-Datum** | 2026-06-03 |
| **Auditor** | mcp-audit-skill v1.0.0 (Katalog v0.5.0) |

### Observed Behavior

- tests/test_server.py mit 22 Tests, respx-HTTP-Mocking (test_server.py:16,156)
- Live-Marker 'live' in pyproject.toml registriert; respx in dev-deps

### Gaps / Abweichung vom Pass-Kriterium

- Keine Trennung test_unit.py/test_live.py
- Keine CI (.github/workflows fehlt) - pytest -m 'not live' laeuft nirgends automatisch
- Kein separater nightly Live-Test-Workflow

### Risk Description

Aus dem Sormena-Pattern bewährt: zwei Test-Kategorien mit klarer Trennung.

### Remediation

### Schritt 1: pyproject.toml-Marker registrieren

```toml
[tool.pytest.ini_options]
markers = [
    "live: tests against real APIs (manual, nightly only)",
]
```

### Schritt 2: respx als Dev-Dependency

```toml
[project.optional-dependencies]
dev = [
    "pytest >= 7.4",
    "pytest-asyncio >= 0.21",
    "pytest-cov >= 4.1",
    "respx >= 0.20",
]
```

### Schritt 3: Unit-Test-Suite aufbauen

Pro Tool mindestens drei Tests:
- Happy-Path (200, expected schema)
- Error-Path (4xx/5xx)
- Edge-Case (leere Antwort, malformed input)

### Schritt 4: CI-Workflow updaten

`.github/workflows/test.yml`:

```yaml
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-python@v6
        with:
          python-version: "3.11"
      - run: pip install -e ".[dev]"
      - run: pytest -m "not live" --cov=src
```

### Schritt 5: Nightly-Live-Workflow

Wie im Pass-Pattern Modus 4.

### Effort Estimate

M — 1–3 Tage Initial-Setup. Tests-Schreiben skaliert mit Tool-Anzahl.

### Verification After Fix

- Re-Audit von `OPS-001` via `/audit-mcp`
- Pytest-/grep-Guard gegen das Anti-Pattern (wo automatisierbar)


### OPS-002

## Finding: OPS-002 — Doku-Standard: bilingualer README, ASCII-Diagramm, Limits-Sektion

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Check-Status** | partial |
| **Server** | `swiss-electricity-mcp` |
| **Check-Reference** | `OPS-002` |
| **PDF-Reference** | Anhang C2 |
| **Audit-Datum** | 2026-06-03 |
| **Auditor** | mcp-audit-skill v1.0.0 (Katalog v0.5.0) |

### Observed Behavior

- README.md mit allen Kern-Sektionen (Anchor-Demo, Installation, Tools, Cloud, Architecture, Testing, Known limitations, Licensing)
- README.de.md parallel; CHANGELOG.md + CONTRIBUTING.md (bilingual) + EXAMPLES.md vorhanden

### Gaps / Abweichung vom Pass-Kriterium

- Architektur-Sektion ist narrativ - kein ASCII-/Mermaid-Architekturdiagramm

### Risk Description

ARCH-011 verlangt die Existenz von `README.md`, `README.de.md`, `CHANGELOG.md` als Files. OPS-002 verlangt **Inhalt-Disziplin** für diese Files — nicht nur Existenz.

### Remediation

### Schritt 1: README-Skelett

Vorlage in `templates/server-readme.md` (im Skill-Repo). Pro Server kopieren und befüllen.

### Schritt 2: Anchor-Demo-Query identifizieren

Für jeden Server eine konkrete Frage formulieren, die ein:e Schulamts-Mitarbeiter:in stellen würde. Diese im README prominent.

### Schritt 3: Limits-Workshop

15-Minuten-Workshop pro Server mit Maintainer. Drei Fragen:
- Was funktioniert sehr gut?
- Wo bricht der Server typischerweise?
- Welche Erwartungen sollte der User **nicht** haben?

Resultat als Limits-Sektion.

### Schritt 4: ASCII-Diagramm

Tools wie [Mermaid](https://mermaid.js.org/) oder einfach pure ASCII mit `─`-Box-Drawing-Characters. Bei mehr als 5 Komponenten: zwei Diagramme (Übersicht + Detail).

### Schritt 5: README.de.md synchron halten

Bei jedem PR mit README-Änderungen muss README.de.md auch aktualisiert werden. CI-Hook:

```yaml
- name: Check README parity
  run: |
    grep -E '^## ' README.md | sort > /tmp/en.txt
    grep -E '^## ' README.de.md | sort > /tmp/de.txt
    diff -u /tmp/en.txt /tmp/de.txt || (echo "README sections out of sync"; exit 1)
```

### Effort Estimate

M — 1–3 Tage pro Server für Initial-Doku. Bei portfolio-weitem Roll-out: ~1 Tag pro Server.

### Verification After Fix

- Re-Audit von `OPS-002` via `/audit-mcp`
- Pytest-/grep-Guard gegen das Anti-Pattern (wo automatisierbar)


### OPS-003

## Finding: OPS-003 — Phasenarchitektur: Read-only First, dann Write, dann Multi-Agent

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Check-Status** | partial |
| **Server** | `swiss-electricity-mcp` |
| **Check-Reference** | `OPS-003` |
| **PDF-Reference** | Anhang C4 |
| **Audit-Datum** | 2026-06-03 |
| **Auditor** | mcp-audit-skill v1.0.0 (Katalog v0.5.0) |

### Observed Behavior

- Server ist faktisch Phase 1 (read-only first): alle Tools read-only, keine destruktiven Operationen

### Gaps / Abweichung vom Pass-Kriterium

- Keine explizite Phasen-Deklaration (Phase 1/2/3) im README
- Kein roadmap-File mit phasenspezifischen Tasks

### Risk Description

Der Anhang sagt klar: «Die häufigste Ursache von MCP-Sicherheitsvorfällen 2025/26 war: ‹Wir haben gleich Schreibzugriffe gebaut, weil es ging.›»

### Remediation

### Schritt 1: Phase-Audit pro Server

Pro Server im Portfolio:

| Frage | Antwort |
|---|---|
| Hat der Server destruktive Tools? | ja → mindestens Phase 3 |
| Hat der Server Semantic Layer / Federation? | ja → mindestens Phase 2 |
| Sonst | Phase 1 |

### Schritt 2: Phase-Sektion ins README

Mit Status-Tabelle wie im Pass-Pattern Modus 1.

### Schritt 3: Roadmap erstellen

Mit Phase-Voraussetzungen als Tasks. Falls aktueller Server in Phase 2 oder 3 ist und Phase-1-Voraussetzungen fehlen: Findings im Audit-Tracker dokumentieren, retroaktiv schliessen.

### Schritt 4: Phase-Gate als Notion-Workflow

In Notion-Audit-Tracker-Schema (`a2736a65-...`) ein Feld «Phase» (Single-Select: 1, 2, 3) mit klaren Übergangs-Anforderungen.

### Effort Estimate

S — < 1 Tag pro Server für Initial-Phase-Deklaration. M — Wochen für Phase-Übergänge mit allen Compensating-Action-Anforderungen.

### Verification After Fix

- Re-Audit von `OPS-003` via `/audit-mcp`
- Pytest-/grep-Guard gegen das Anti-Pattern (wo automatisierbar)


### SCALE-004

## Finding: SCALE-004 — Containerization mit Multi-Stage-Builds

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Check-Status** | fail |
| **Server** | `swiss-electricity-mcp` |
| **Check-Reference** | `SCALE-004` |
| **PDF-Reference** | Sec 5.3 |
| **Audit-Datum** | 2026-06-03 |
| **Auditor** | mcp-audit-skill v1.0.0 (Katalog v0.5.0) |

### Observed Behavior

- is_cloud_deployed=true -> Containerization anwendbar

### Gaps / Abweichung vom Pass-Kriterium

- Kein Dockerfile im Repo - kein Multi-Stage-Build, kein slim/alpine-Base, kein non-root USER, kein HEALTHCHECK

### Risk Description

Container-Images für MCP-Server sind oft 800 MB – 1.5 GB gross, weil Build-Toolchains (gcc, Rust, npm-build-deps) im finalen Image bleiben. Multi-Stage-Builds trennen Build und Runtime: das finale Image enthält nur den fertigen Server plus minimale Runtime-Dependencies (typischerweise 80–150 MB).

### Remediation

```diff
- FROM python:3.11
- WORKDIR /app
- COPY . .
- RUN pip install -e .
- CMD ["python", "-m", "server"]
+ FROM python:3.11-slim AS builder
+ WORKDIR /build
+ COPY pyproject.toml .
+ COPY src/ ./src/
+ RUN pip install --no-cache-dir --user -e .
+
+ FROM python:3.11-slim AS runtime
+ COPY --from=builder /root/.local /root/.local
+ COPY src/ /app/src/
+ WORKDIR /app
+ ENV PATH=/root/.local/bin:$PATH PYTHONUNBUFFERED=1
+ USER nobody
+ HEALTHCHECK CMD curl -f http://localhost:8000/healthz || exit 1
+ CMD ["python", "-m", "server"]
```

### Effort Estimate

S — < 1 Tag.

### Verification After Fix

- Re-Audit von `SCALE-004` via `/audit-mcp`
- Pytest-/grep-Guard gegen das Anti-Pattern (wo automatisierbar)


### SDK-001

## Finding: SDK-001 — FastMCP Lifespan via @asynccontextmanager + AsyncExitStack

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Check-Status** | fail |
| **Server** | `swiss-electricity-mcp` |
| **Check-Reference** | `SDK-001` |
| **PDF-Reference** | Sec 3.1 |
| **Audit-Datum** | 2026-06-03 |
| **Auditor** | mcp-audit-skill v1.0.0 (Katalog v0.5.0) |

### Observed Behavior

- grep auf lifespan/asynccontextmanager in src/ = 0 Treffer
- HTTP-Clients werden als Module-Globals beim Import erzeugt und nie geschlossen (server.py:70-72; api_client.py:116/183/336)

### Gaps / Abweichung vom Pass-Kriterium

- Kein @asynccontextmanager-Lifespan, FastMCP erhaelt kein lifespan=
- aclose() der Clients wird nie aufgerufen - Connection-Cleanup fehlt

### Risk Description

MCP-Server halten häufig Ressourcen, die über die einzelne Tool-Anfrage hinaus existieren: HTTP-Connection-Pools, DB-Pools, Redis-Verbindungen, gecachte Auth-Tokens, Pre-Computed-Indexes. Werden diese pro Tool-Call neu erzeugt, bricht die Performance ein. Werden sie gar nicht aufgeräumt, ergeben sich Resource-Leaks (offene TCP-Connections, dangling Cursor).

### Remediation

Migrationsweg:

```diff
+ from contextlib import asynccontextmanager
+ import httpx
+
+ @asynccontextmanager
+ async def lifespan(server):
+     server.state.http = httpx.AsyncClient(timeout=30)
+     try:
+         yield
+     finally:
+         await server.state.http.aclose()
+
- mcp = FastMCP("zurich-opendata")
+ mcp = FastMCP("zurich-opendata", lifespan=lifespan)

  @mcp.tool()
- async def search(query: str):
-     async with httpx.AsyncClient() as client:
-         return (await client.get(f"https://api/{query}")).json()
+ async def search(query: str, ctx):
+     return (await ctx.fastmcp.state.http.get(f"https://api/{query}")).json()
```

### Effort Estimate

S — < 1 Tag. Lifespan-Block + Tool-Refactoring + Tests.

### Verification After Fix

- Re-Audit von `SDK-001` via `/audit-mcp`
- Pytest-/grep-Guard gegen das Anti-Pattern (wo automatisierbar)


### SDK-003

## Finding: SDK-003 — Context Injection für Progress Reports und Logging

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Check-Status** | partial |
| **Server** | `swiss-electricity-mcp` |
| **Check-Reference** | `SDK-003` |
| **PDF-Reference** | Sec 3.1 |
| **Audit-Datum** | 2026-06-03 |
| **Auditor** | mcp-audit-skill v1.0.0 (Katalog v0.5.0) |

### Observed Behavior

- Tools machen externe Requests die >2s dauern koennen (LINDAS SPARQL Timeout 60s, api_client.py:184)

### Gaps / Abweichung vom Pass-Kriterium

- Kein ctx: Context-Parameter, kein ctx.report_progress() bei langlaufenden SPARQL-/Compare-Tools
- Fehler werden nicht via ctx.warning()/ctx.error() berichtet

### Risk Description

FastMCP bietet via `Context`-Parameter ein typsicheres Interface zu Server-Internals: Logging, Progress-Reports, Client-Info, Session-State, Sampling, Elicitation. Tools, die `ctx: Context` als Parameter deklarieren, bekommen dieses Objekt automatisch injiziert (Dependency Injection durch FastMCP).

### Remediation

Migrationsweg für ein langes Tool:

```diff
+ from mcp.server.fastmcp import Context

  @mcp.tool()
- async def export_all_records(format: str) -> dict:
-     records = await db.fetch_all()
-     for record in records:
-         await transform(record, format)
-     return {"count": len(records)}
+ async def export_all_records(format: str, ctx: Context) -> dict:
+     await ctx.info(f"Starting export in format={format}")
+     records = await db.fetch_all()
+     await ctx.info(f"Loaded {len(records)} records, transforming...")
+
+     transformed = []
+     for i, record in enumerate(records):
+         if i % 50 == 0:
+             await ctx.report_progress(
+                 progress=i,
+                 total=len(records),
+                 message=f"Transformed {i}/{len(records)}",
+             )
+         transformed.append(await transform(record, format))
+
+     await ctx.info(f"Export complete: {len(transformed)} records")
+     return {"count": len(transformed), "format": format}
```

### Effort Estimate

S — < 1 Tag. Pro Tool 10 Minuten + Tests.

### Verification After Fix

- Re-Audit von `SDK-003` via `/audit-mcp`
- Pytest-/grep-Guard gegen das Anti-Pattern (wo automatisierbar)


### SDK-004

## Finding: SDK-004 — CORS Mcp-Session-Id Exposure bei HTTP/SSE

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Check-Status** | partial |
| **Server** | `swiss-electricity-mcp` |
| **Check-Reference** | `SDK-004` |
| **PDF-Reference** | Sec 3.1 |
| **Audit-Datum** | 2026-06-03 |
| **Auditor** | mcp-audit-skill v1.0.0 (Katalog v0.5.0) |

### Observed Behavior

- dual transport -> CORS-Check anwendbar

### Gaps / Abweichung vom Pass-Kriterium

- Keine explizite CORS-Middleware-Konfiguration; Verlass auf FastMCP-Default
- expose_headers/allow_headers fuer Mcp-Session-Id nicht explizit gesetzt; allow_origins nicht eingeschraenkt

### Risk Description

Bei Streamable HTTP / SSE läuft die MCP-Kommunikation über Cross-Origin-Requests, wenn der Client (Browser-basiert) auf einer anderen Domain als der Server hostet. Der Server gibt nach `init` einen `Mcp-Session-Id`-Header in der Response zurück — diesen muss der Browser an Folge-Requests anhängen können.

### Remediation

```diff
  from starlette.applications import Starlette
  from starlette.routing import Mount
+ from starlette.middleware import Middleware
+ from starlette.middleware.cors import CORSMiddleware

+ ALLOWED_ORIGINS = [
+     o.strip() for o in os.environ.get("ALLOWED_ORIGINS", "").split(",") if o.strip()
+ ]
+
+ middleware = [
+     Middleware(
+         CORSMiddleware,
+         allow_origins=ALLOWED_ORIGINS,
+         allow_methods=["GET", "POST", "OPTIONS"],
+         allow_headers=["Content-Type", "Mcp-Session-Id", "Authorization"],
+         expose_headers=["Mcp-Session-Id"],
+         allow_credentials=True,
+     ),
+ ]
+
  app = Starlette(
      routes=[Mount("/", app=mcp.streamable_http_app())],
+     middleware=middleware,
  )
```

Plus Umgebungsvariable:

```bash
# .env (production)
ALLOWED_ORIGINS=https://app.schulamt.zh.ch,https://claude.ai
```

### Effort Estimate

S — < 1 Tag. Middleware-Konfig + ENV-Var + Browser-Test.

### Verification After Fix

- Re-Audit von `SDK-004` via `/audit-mcp`
- Pytest-/grep-Guard gegen das Anti-Pattern (wo automatisierbar)


### SEC-004

## Finding: SEC-004 — SSRF-Prevention: HTTPS-Enforcement + IP-Blocklisting

| Feld | Wert |
|---|---|
| **Severity** | critical |
| **Status** | open |
| **Check-Status** | partial |
| **Server** | `swiss-electricity-mcp` |
| **Check-Reference** | `SEC-004` |
| **PDF-Reference** | Sec 4.4 |
| **Audit-Datum** | 2026-06-03 |
| **Auditor** | mcp-audit-skill v1.0.0 (Katalog v0.5.0) |

### Observed Behavior

- Alle Upstream-URLs sind hardcodierte Konstanten (api_client.py:25-28) - KEIN user-kontrollierter URL-Parameter in irgendeinem Tool
- Alle Endpunkte sind https://

### Gaps / Abweichung vom Pass-Kriterium

- Keine explizite HTTPS-Schema-Validierung als Layer
- Keine IP-Blocklist/getaddrinfo-Pruefung gegen 169.254.169.254 & private Ranges (Defense-in-Depth fehlt, Restrisiko niedrig da keine dynamischen URLs)

### Risk Description

Server-Side Request Forgery (SSRF) entsteht, wenn ein MCP-Server URLs aus User-Input (oder LLM-generierten Args) direkt an HTTP-Clients weitergibt. Ein Angreifer kann den Server dann zwingen, beliebige interne Adressen abzurufen — insbesondere die Cloud-Metadata-Endpunkte.

### Remediation

Volles Pattern oben. Zusätzlich für Defense-in-Depth:

### Container-Level Egress-Filtering

```yaml
# Kubernetes NetworkPolicy
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: mcp-server-egress
spec:
  podSelector:
    matchLabels:
      app: mcp-server
  policyTypes:
    - Egress
  egress:
    - to:
        - ipBlock:
            cidr: 0.0.0.0/0
            except:
              - 10.0.0.0/8
              - 172.16.0.0/12
              - 192.168.0.0/16
              - 169.254.0.0/16
              - 127.0.0.0/8
      ports:
        - protocol: TCP
          port: 443
```

### IMDSv2 statt IMDSv1 (AWS-spezifisch)

Falls auf AWS deployed: IMDSv2 mit Hop-Limit 1 erzwingen (verhindert SSRF auch bei Code-Bug).

```bash
aws ec2 modify-instance-metadata-options \
  --instance-id i-xxx \
  --http-tokens required \
  --http-put-response-hop-limit 1
```

### Effort Estimate

M — 1–3 Tage. Egress-Proxy-Setup + URL-Validation-Layer + Tests.

### Verification After Fix

- Re-Audit von `SEC-004` via `/audit-mcp`
- Pytest-/grep-Guard gegen das Anti-Pattern (wo automatisierbar)


### SEC-005

## Finding: SEC-005 — DNS-Rebinding-Prevention: DNS-Pinning gegen TOCTOU

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Check-Status** | partial |
| **Server** | `swiss-electricity-mcp` |
| **Check-Reference** | `SEC-005` |
| **PDF-Reference** | Sec 4.4 |
| **Audit-Datum** | 2026-06-03 |
| **Auditor** | mcp-audit-skill v1.0.0 (Katalog v0.5.0) |

### Observed Behavior

- Keine user-kontrollierten Hostnamen; nur feste Endpunkte

### Gaps / Abweichung vom Pass-Kriterium

- Kein DNS-Pinning/Single-Resolution-Pattern - Restrisiko niedrig mangels dynamischer URLs, aber Defense-in-Depth-Kontrolle fehlt

### Risk Description

SEC-004 (SSRF-Prevention) verlangt: Resolved IP wird gegen Blocklist geprüft, dann Request mit dieser IP. DNS-Rebinding ist ein verfeinerter Angriff, der diese Defense umgeht — durch zwei verschiedene DNS-Antworten für denselben Hostnamen mit kurzem TTL:

### Remediation

### Schritt 1: HTTP-Client mit Custom Transport

```python
import httpx
import socket
import ipaddress

class PinnedTransport(httpx.AsyncHTTPTransport):
    """HTTPX Transport mit DNS-Pinning."""

    async def handle_async_request(self, request):
        url = request.url
        if url.scheme != "https":
            raise httpx.RequestError("Only HTTPS allowed")

        # Resolve einmalig
        loop = asyncio.get_event_loop()
        addrinfo = await loop.getaddrinfo(
            url.host, url.port, type=socket.SOCK_STREAM
        )
        resolved_ip = addrinfo[0][4][0]

        # Range-Check
        ip = ipaddress.ip_address(resolved_ip)
        for blocked in BLOCKED_NETWORKS:
            if ip in blocked:
                raise httpx.RequestError(f"Blocked IP: {ip}")

        # URL mit gepinnter IP, aber Host-Header bleibt
        pinned_url = httpx.URL(str(url).replace(url.host, resolved_ip, 1))
        new_request = httpx.Request(
            method=request.method,
            url=pinned_url,
            headers=httpx.Headers(request.headers),
            content=request.content,
            extensions=request.extensions,
        )
        new_request.headers["Host"] = url.host
        # SNI bleibt durch URL-Hostname (httpx interner default)
        return await super().handle_async_request(new_request)


# Verwendung
async with httpx.AsyncClient(transport=PinnedTransport()) as client:
    response = await client.get("https://api.external.com/data")
```

### Schritt 2: Alternative — Egress-Proxy

Wenn Custom-Transport zu komplex: Stripe Smokescreen als Sidecar erledigt DNS-Pinning automatisch.

```yaml
# docker-compose.yml
services:
  smokescreen:
    image: stripe/smokescreen:latest
    command: ["--listen-ip", "127.0.0.1", "--listen-port", "4750"]


_(... vollstaendige Remediation siehe checks/SEC-005.md)_

### Effort Estimate

M — 1–3 Tage. Custom-Transport oder Egress-Proxy-Setup + Tests.

### Verification After Fix

- Re-Audit von `SEC-005` via `/audit-mcp`
- Pytest-/grep-Guard gegen das Anti-Pattern (wo automatisierbar)


### SEC-007

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


### SEC-008

## Finding: SEC-008 — Pre-Configuration Consent für Local-Server-Installation

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Check-Status** | partial |
| **Server** | `swiss-electricity-mcp` |
| **Check-Reference** | `SEC-008` |
| **PDF-Reference** | Sec 4.5 |
| **Audit-Datum** | 2026-06-03 |
| **Auditor** | mcp-audit-skill v1.0.0 (Katalog v0.5.0) |

### Observed Behavior

- Keine pre/postinstall-Hooks (reines Python-Paket, hatchling); keine dynamischen Setup-Scripts
- README zeigt vollen Installationsbefehl transparent; CONTRIBUTING.md erklaert Build

### Gaps / Abweichung vom Pass-Kriterium

- Keine PyPI-OIDC-Trusted-Publisher/Sigstore-Signatur (kein publish-Workflow, .github fehlt)

### Risk Description

Wenn ein User einen lokalen MCP-Server installiert (typischerweise via `claude_desktop_config.json`), wird ein Subprozess mit User-Privilegien gestartet. Der Befehl steht in der Konfig-Datei — `npx -y @malkreide/zh-education-mcp`, `uvx zh-education-mcp`, etc.

### Remediation

### Schritt 1: Hooks entfernen

```diff
  {
    "scripts": {
-     "postinstall": "node ./scripts/setup.js",
      "build": "tsc",
      "start": "node dist/server.js"
    }
  }
```

Falls Setup wirklich nötig ist: als separater, dokumentierter Schritt nach Installation, nicht automatisch.

### Schritt 2: README-Transparenz

Vollen Befehl mit Erklärung wie im Pass-Pattern. Kein Hide-Behind-One-Liner.

### Schritt 3: PyPI-Trusted-Publisher konfigurieren

Auf pypi.org → Project Settings → Publishing → Add trusted publisher mit GitHub-Repo.

```yaml
# .github/workflows/release.yml
on:
  push:
    tags: ['v*']

jobs:
  build-and-publish:
    runs-on: ubuntu-latest
    environment: pypi
    permissions:
      id-token: write
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-python@v6
      - run: pip install build && python -m build
      - uses: pypa/gh-action-pypi-publish@release/v1
        # Sigstore-Signaturen automatisch
```

### Schritt 4: User-seitige Empfehlung im README

```markdown

### Effort Estimate

S — < 1 Tag. Hauptaufwand: Trusted-Publisher-Setup auf PyPI/npm + README-Update.

### Verification After Fix

- Re-Audit von `SEC-008` via `/audit-mcp`
- Pytest-/grep-Guard gegen das Anti-Pattern (wo automatisierbar)


### SEC-016

## Finding: SEC-016 — 0.0.0.0-Binding-Prevention (NeighborJack)

| Feld | Wert |
|---|---|
| **Severity** | critical |
| **Status** | open |
| **Check-Status** | fail |
| **Server** | `swiss-electricity-mcp` |
| **Check-Reference** | `SEC-016` |
| **PDF-Reference** | Sec 4 (Empirie 2025) |
| **Audit-Datum** | 2026-06-03 |
| **Auditor** | mcp-audit-skill v1.0.0 (Katalog v0.5.0) |

### Observed Behavior

- Default-Host ist hardcodiert 0.0.0.0: os.environ.get('SWISS_ELECTRICITY_HOST', '0.0.0.0') (__main__.py:18)

### Gaps / Abweichung vom Pass-Kriterium

- 0.0.0.0 als Default-Binding (NeighborJack-Anti-Pattern) - Default sollte 127.0.0.1 sein, 0.0.0.0 nur im Dockerfile/Container explizit
- Keine Warnung bei 0.0.0.0 ohne Container-Detection

### Risk Description

Die empirische Untersuchung von 2025 ergab: ein erheblicher Teil der OSS-MCP-Server bindet ihren HTTP-Listener an `0.0.0.0` (alle Interfaces) und vertraut implizit darauf, dass Firewall-Regeln den Zugang beschränken. Auf einem Entwickler-Laptop in einem öffentlichen WLAN, einem Co-Working-Space oder einer Konferenz wird der lokale MCP-Server damit für **alle** Geräte im selben Subnetz erreichbar.

### Remediation

### Schritt 1: Code-Default auf 127.0.0.1 ändern

```diff
  if __name__ == "__main__":
      transport = os.environ.get("MCP_TRANSPORT", "stdio")
      if transport == "sse":
-         mcp.run(transport="sse", host="0.0.0.0", port=8000)
+         host = os.environ.get("MCP_HOST", "127.0.0.1")
+         port = int(os.environ.get("MCP_PORT", "8000"))
+         mcp.settings.host = host
+         mcp.settings.port = port
+         mcp.run(transport="sse")
```

### Schritt 2: Container-Override im Dockerfile

```dockerfile
ENV MCP_HOST=0.0.0.0
```

### Schritt 3: Docker-Compose Bind-Adresse

```yaml
# docker-compose.yml
services:
  mcp:
    image: malkreide/zurich-opendata-mcp
    ports:
-     - "8000:8000"           # bindet an alle Interfaces
+     - "127.0.0.1:8000:8000" # nur lokal erreichbar
```

### Schritt 4: Warnung bei riskantem Binding

```python
import logging
import socket

def warn_on_dangerous_binding(host: str):
    if host in ("0.0.0.0", "::"):
        # Container-Detection (heuristisch)
        in_container = (
            os.path.exists("/.dockerenv")
            or os.environ.get("KUBERNETES_SERVICE_HOST")
            or os.environ.get("RAILWAY_PROJECT_ID")
        )
        if not in_container:
            logging.warning(
                "Binding to %s outside container context. "
                "This exposes the MCP server to the local network. "
                "Use MCP_HOST=127.0.0.1 for local development.",
                host,
            )
```

### Schritt 5: README-Dokumentation

```markdown

### Effort Estimate

S — < 1 Tag. Default-Änderung + Dockerfile-ENV + README-Update + Test.

### Verification After Fix

- Re-Audit von `SEC-016` via `/audit-mcp`
- Pytest-/grep-Guard gegen das Anti-Pattern (wo automatisierbar)


### SEC-018

## Finding: SEC-018 — Input-Validation an Tool-Boundaries (Pydantic strict / Zod)

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Check-Status** | partial |
| **Server** | `swiss-electricity-mcp` |
| **Check-Reference** | `SEC-018` |
| **PDF-Reference** | Sec 3 / Sec 4 (Defense-in-Depth) |
| **Audit-Datum** | 2026-06-03 |
| **Auditor** | mcp-audit-skill v1.0.0 (Katalog v0.5.0) |

### Observed Behavior

- Numerische Felder mit ge/le-Constraints (server.py:171 limit_days ge=1 le=400; :308 bfs_nr ge=1; :443 bfs_numbers min/max_length)
- Pydantic-Field-Validierung an allen Tool-Boundaries; Literal-Types fuer Enums

### Gaps / Abweichung vom Pass-Kriterium

- String-Parameter category/canton/query ohne max_length/pattern (server.py:309/401/485)
- category/canton werden ungeprueft in SPARQL-Query-Strings interpoliert (api_client.py:218/312) -> SPARQL-Injection-Risiko
- Kein strict=True/extra='forbid' an den Modellen

### Risk Description

Tool-Argumente kommen vom LLM — einer probabilistischen Quelle, die halluzinieren, formattieren-falsch oder von Prompt-Injection beeinflusst sein kann. Ohne strikte Input-Validation am Tool-Boundary werden invalide oder bösartige Inputs in die Geschäftslogik weitergereicht und können dort:

### Remediation

### Schritt 1: Schema pro Tool extrahieren

```diff
+ from typing import Annotated
+ from pydantic import BaseModel, Field, StringConstraints
+
+ class SearchArgs(BaseModel):
+     model_config = {"strict": True, "extra": "forbid"}
+     query: Annotated[str, StringConstraints(min_length=2, max_length=200)]
+     limit: Annotated[int, Field(ge=1, le=100)] = 10

  @mcp.tool()
- async def search(query: str, limit: int = 10) -> dict:
+ async def search(args: SearchArgs, ctx: Context) -> dict:
-     return await db.search(query, limit=limit)
+     return await db.search(args.query, limit=args.limit)
```

### Schritt 2: ValidationError sauber behandeln

```python
from pydantic import ValidationError

@mcp.tool()
async def search(args: SearchArgs, ctx: Context) -> dict:
    try:
        # Pydantic validiert beim Parsing automatisch — kein Aufruf nötig
        # Falls manuell aus dict gebaut: SearchArgs.model_validate(raw_dict)
        return await db.search(args.query, limit=args.limit)
    except ValidationError as e:
        # Wird normal nicht erreicht (FastMCP fängt das ab),
        # aber Defense-in-Depth:
        return {
            "isError": True,
            "content": [TextContent(
                type="text",
                text=f"Invalid arguments: {e.errors()[0]['msg']}"
            )],
        }
```

### Schritt 3: Tests gegen Edge-Cases

```python
@pytest.mark.parametrize("invalid_args,expected_error", [
    ({"query": "a", "limit": 10}, "min_length"),       # zu kurz
    ({"query": "x"*500, "limit": 10}, "max_length"),   # zu lang
    ({"query": "test", "limit": 0}, "greater_than_or_equal"),
    ({"query": "test", "limit": 99999}, "less_than_or_equal"),
    ({"query": "test", "limit": 10, "evil": "field"}, "extra_forbidden"),
])

_(... vollstaendige Remediation siehe checks/SEC-018.md)_

### Effort Estimate

S — < 1 Tag pro Server bei wenigen Tools, M bei vielen Tools (10+).

### Verification After Fix

- Re-Audit von `SEC-018` via `/audit-mcp`
- Pytest-/grep-Guard gegen das Anti-Pattern (wo automatisierbar)


### SEC-019

## Finding: SEC-019 — Lethal Trifecta vermeiden: Server-Separation Read vs Write/Send

| Feld | Wert |
|---|---|
| **Severity** | critical |
| **Status** | open |
| **Check-Status** | partial |
| **Server** | `swiss-electricity-mcp` |
| **Check-Reference** | `SEC-019` |
| **PDF-Reference** | Anhang B1 |
| **Audit-Datum** | 2026-06-03 |
| **Auditor** | mcp-audit-skill v1.0.0 (Katalog v0.5.0) |

### Observed Behavior

- Trifecta-Bewertung: (1) nur Public Open Data, keine privaten Daten; (2) liest externe API-Daten; (3) kein Exfiltrations-Kanal (Egress hardcodiert) -> maximal 1-2 Faehigkeiten, Risiko niedrig

### Gaps / Abweichung vom Pass-Kriterium

- Trifecta-Assessment ist nicht im README/docs dokumentiert (Katalog verlangt explizite Dokumentation/ADR)

### Risk Description

Simon Willisons «Lethal Trifecta»-Konzept beschreibt drei Fähigkeiten, die einzeln harmlos, **kombiniert** aber den Server zur Waffe in der Hand eines Prompt-Injection-Angreifers machen:

### Remediation

### Schritt 1: Trifecta-Audit pro Server

Für jeden Server im Portfolio die drei Fragen beantworten:

| Frage | Antwort | Score-Beitrag |
|---|---|---|
| Liest privater Daten? | ja/nein | +1 wenn ja |
| Untrusted Content? | ja/nein | +1 wenn ja |
| Externe Kommunikation? | ja/nein | +1 wenn ja |

Score 0–1: sicher. Score 2: ADR + Compensating Controls. Score 3: Server splitten.

### Schritt 2: Server-Splittung (bei Score 3)

Beispiel — aus einem hypothetischen `eltern-comm-mcp`:

```diff
- # Vorher: ein Server liest UND sendet
- @mcp.tool() def get_eltern_data(klassenid): ...
- @mcp.tool() def send_eltern_mail(recipient, body): ...

+ # Nachher: zwei Server
+ # eltern-data-mcp/
+ @mcp.tool() def get_eltern_data(klassenid): ...
+
+ # eltern-mail-mcp/  (separater Repo, separate Service-Identity)
+ ALLOWED_DOMAINS = frozenset({"schulen.zuerich.ch"})
+ @mcp.tool() def send_eltern_mail(recipient, body):
+     if recipient.split("@")[-1] not in ALLOWED_DOMAINS:
+         raise PermissionError(...)
```

### Schritt 3: ADR dokumentieren

Wie im Pass-Pattern Modus 2.

### Schritt 4: Audit-Trail

Bei Score-2-Servern: alle Tool-Calls werden geloggt, SIEM-Alerts (siehe OBS-005) auf ungewöhnliche Pattern (z.B. Recipients ausserhalb Allow-List).

### Effort Estimate

L — 1–2 Wochen bei nötiger Server-Splittung. S — < 1 Tag für reine Bewertung und ADR.

### Verification After Fix

- Re-Audit von `SEC-019` via `/audit-mcp`
- Pytest-/grep-Guard gegen das Anti-Pattern (wo automatisierbar)


### SEC-021

## Finding: SEC-021 — Egress-Allow-List: Code-Layer und Network-Layer

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Check-Status** | partial |
| **Server** | `swiss-electricity-mcp` |
| **Check-Reference** | `SEC-021` |
| **PDF-Reference** | Anhang B5 + B12 |
| **Audit-Datum** | 2026-06-03 |
| **Auditor** | mcp-audit-skill v1.0.0 (Katalog v0.5.0) |

### Observed Behavior

- De-facto-Egress-Allowlist: alle Ziel-Hosts sind hardcodierte Modul-Konstanten (api_client.py:25-28), keine dynamischen Hosts

### Gaps / Abweichung vom Pass-Kriterium

- Keine explizite frozenset-Allowlist mit assert_host_allowed-Pre-Request-Check
- Keine Network-Layer-Egress-Control (NetworkPolicy) dokumentiert; keine docs/network-egress.md

### Risk Description

SEC-004 (SSRF-Prevention) blockiert Requests an interne IP-Ranges. SEC-021 ergänzt das auf der **anderen Seite**: welche externen Ziele darf der Server überhaupt erreichen?

### Remediation

### Schritt 1: Allow-List-Inventar

Pro Server alle ausgehenden HTTP-Hosts identifizieren:

```bash
grep -rE 'https://[a-z0-9.-]+' src/ | \
  sed -E 's/.*https:\/\/([a-z0-9.-]+).*/\1/' | sort -u
```

Resultat: minimale Allow-Liste.

### Schritt 2: Code-Layer einbauen

Wie Pass-Pattern Modus 1.

### Schritt 3: Network-Layer einbauen

Bei Kubernetes: NetworkPolicy wie oben. Bei AWS: Security Group mit egress-Rules. Bei Cloudflare WARP: Zero-Trust-Policy.

### Schritt 4: Tests gegen Regression

```python
async def test_egress_blocked_to_non_allowlisted_host():
    with pytest.raises(PermissionError, match="not in allow-list"):
        await fetch_external_data("https://evil.example.com/", mock_ctx())


async def test_egress_allowed_to_allowlisted_host():
    # Mock-Response, kein echter Network-Call
    with respx.mock:
        respx.get("https://opendata.swiss/api/...").respond(200, json={"ok": True})
        result = await fetch_external_data("https://opendata.swiss/api/...", mock_ctx())
        assert result["ok"]
```

### Effort Estimate

M — 1–3 Tage. Code-Layer-Allow-List + Network-Policy + Doku + Tests.

### Verification After Fix

- Re-Audit von `SEC-021` via `/audit-mcp`
- Pytest-/grep-Guard gegen das Anti-Pattern (wo automatisierbar)


### SEC-022

## Finding: SEC-022 — Tool-Hash-Pinning + Namespace-Präfix gegen Rug Pull

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Check-Status** | partial |
| **Server** | `swiss-electricity-mcp` |
| **Check-Reference** | `SEC-022` |
| **PDF-Reference** | Anhang B4 |
| **Audit-Datum** | 2026-06-03 |
| **Auditor** | mcp-audit-skill v1.0.0 (Katalog v0.5.0) |

### Observed Behavior

- Funktionale Praefixe dashboard_/tariff_/consumption_ vorhanden

### Gaps / Abweichung vom Pass-Kriterium

- Praefixe sind Funktionsgruppen, kein Server-Identity-Namespace (<server>__<tool>)
- Kein Tool-Definition-Hash-Snapshot pro Release; CHANGELOG nennt Tool-Aenderungen nicht explizit

### Risk Description

SEC-015 deckt **Tool-Poisoning** ab — bösartige Inhalte in Tool-Beschreibungen beim Onboarding. SEC-022 ergänzt das um zwei verwandte Angriffsklassen:

### Remediation

### Schritt 1: Namespace-Audit

Server-Identity festlegen — typisch der Repo-Name als snake_case-Präfix:

| Repo | Namespace |
|---|---|
| `zh-education-mcp` | `zh_education` |
| `zurich-opendata-mcp` | `zurich_opendata` |
| `parlament-mcp` | `parlament_ch` |

### Schritt 2: Tool-Renaming

```diff
- @mcp.tool()
- async def search(query: str): ...
+ @mcp.tool(name="zh_education__search")
+ async def search(query: str): ...
```

Bei Renaming: Major-Version-Bump, da Tool-Namen Breaking-Changes sind.

### Schritt 3: Hash-Snapshot-Workflow

CI-Step wie im Pass-Pattern Modus 2. `tool-hashes.json` als Artefakt im Release.

### Schritt 4: Bei Update-Disziplin (Synergie zu ARCH-012)

CHANGELOG-Template um «Tool Definition Changes»-Sektion erweitern:

```markdown

### Effort Estimate

M — 1–3 Tage pro Server. Namespace-Renaming + Hash-Workflow + CHANGELOG-Updates.

### Verification After Fix

- Re-Audit von `SEC-022` via `/audit-mcp`
- Pytest-/grep-Guard gegen das Anti-Pattern (wo automatisierbar)


---

## 6. Remediation-Plan

### Empfohlene Reihenfolge

1. **ARCH-005** (critical, partial)
2. **SEC-004** (critical, partial)
3. **SEC-016** (critical, fail)
4. **SEC-019** (critical, partial)
5. **ARCH-004** (high, partial)
6. **ARCH-009** (high, fail)
7. **OBS-001** (high, partial)
8. **OBS-002** (high, partial)
9. **OPS-001** (high, partial)
10. **OPS-003** (high, partial)
11. **SDK-001** (high, fail)
12. **SDK-004** (high, partial)
13. **SEC-005** (high, partial)
14. **SEC-007** (high, fail)
15. **SEC-018** (high, partial)
16. **SEC-021** (high, partial)
17. **SEC-022** (high, partial)
18. **ARCH-003** (medium, partial)
19. **ARCH-007** (medium, partial)
20. **ARCH-008** (medium, partial)
21. **ARCH-011** (medium, fail)
22. **ARCH-012** (medium, partial)
23. **OBS-003** (medium, fail)
24. **OBS-006** (medium, fail)
25. **OPS-002** (medium, partial)
26. **SCALE-004** (medium, fail)
27. **SDK-003** (medium, partial)
28. **SEC-008** (medium, partial)

---

## 7. Audit-Metadata

| Feld | Wert |
|---|---|
| skill_version | `1.0.0` |
| catalog_version | `0.5.0 (catalog_hash 091f446b)` |
| audit_date | `2026-06-03` |


_Generated by tools/build_report.py — do not edit by hand._
