# MCP-Server Audit-Report — `lobbywatch-mcp`

**Audit-Datum:** 
**Skill-Version:** 1.0.0
**Catalog-Version:** ?

---

## 1. Executive Summary

Server `lobbywatch-mcp` wurde gegen 44 anwendbare Best-Practice-Checks geprüft. 17 bestanden, 25 Findings dokumentiert (2 critical, 12 high, 11 medium, 0 low). Production-Readiness: NICHT erreicht — blockierend: ARCH-009, SCALE-002, SCALE-003, SDK-001, SDK-004, SEC-005, SEC-007, SEC-016, SEC-021, SEC-022.

**Production-Readiness:** NO

---

## 2. Profil-Snapshot

| Feld | Wert |
|---|---|
| Server-Name | `lobbywatch-mcp` |
| Audit-Datum | ? |
| Skill-Version | 1.0.0 |
| Catalog-Version | ? |

---

## 3. Applicability

### Status pro Kategorie

| Kategorie | Pass | Fail | Partial | Todo | N/A |
|---|---|---|---|---|---|
| ARCH | 6 | 3 | 2 | 0 | 0 |
| CH | 1 | 0 | 0 | 0 | 0 |
| OBS | 1 | 1 | 3 | 0 | 0 |
| OPS | 2 | 0 | 1 | 0 | 0 |
| SCALE | 1 | 4 | 0 | 0 | 0 |
| SDK | 0 | 3 | 1 | 0 | 0 |
| SEC | 6 | 5 | 2 | 2 | 0 |
| **Total** | **17** | **16** | **9** | **2** | **0** |

---

## 4. Findings-Übersicht

_Policy: `fail-or-partial`_

| ID | Category | Severity | Status |
|---|---|---|---|
| SEC-004 | SEC | critical | partial |
| SEC-016 | SEC | critical | fail |
| ARCH-009 | ARCH | high | fail |
| OBS-001 | OBS | high | partial |
| OBS-002 | OBS | high | partial |
| SCALE-002 | SCALE | high | fail |
| SCALE-003 | SCALE | high | fail |
| SDK-001 | SDK | high | fail |
| SDK-004 | SDK | high | fail |
| SEC-005 | SEC | high | fail |
| SEC-007 | SEC | high | fail |
| SEC-018 | SEC | high | partial |
| SEC-021 | SEC | high | fail |
| SEC-022 | SEC | high | fail |
| ARCH-002 | ARCH | medium | fail |
| ARCH-003 | ARCH | medium | partial |
| ARCH-008 | ARCH | medium | fail |
| ARCH-012 | ARCH | medium | partial |
| OBS-003 | OBS | medium | partial |
| OBS-006 | OBS | medium | fail |
| OPS-002 | OPS | medium | partial |
| SCALE-004 | SCALE | medium | fail |
| SCALE-006 | SCALE | medium | fail |
| SDK-002 | SDK | medium | partial |
| SDK-003 | SDK | medium | fail |

**Gesamt:** 25 Findings

---

## 5. Detail-Findings

### ARCH-002

## Finding: ARCH-002 — Tool-Beschreibung mit Use-Case-Tags

**Severity:** medium
**Status:** open
**Server:** lobbywatch-mcp
**Check-Reference:** ARCH-002

### Observed Behavior

Tool-Docstrings enthalten keine strukturierten Use-Case-Tags.

### Expected Behavior

Best-Practice-Katalog (ARCH-002). Siehe checks/ARCH-002.md für volle Pass-Criteria.

### Evidence

src/lobbywatch_mcp/server.py:147-401 — alle Docstrings beschreiben Args, keiner enthält 'Use cases:'

### Risk Description

LLM-Tool-Auswahl-Heuristik schlechter; weniger zielgenaue Routing-Entscheidung.

### Remediation

```
Use cases: Sektion am Ende jedes Docstrings, z.B.
  Use cases:
  - 'Welche IBs hat MP X?'
  - 'Show me all WBK-N Bildungs-Mandate'
```

### Effort Estimate

S (< 1d)


### ARCH-003

## Finding: ARCH-003 — «Not Found» Anti-Pattern: Heuristiken statt leerer Antworten

**Severity:** medium
**Status:** open
**Server:** lobbywatch-mcp
**Check-Reference:** ARCH-003

### Observed Behavior

Bei Fuzzy-Miss (score < 70) liefert get_parlamentarier nur None ohne Suggestion.

### Expected Behavior

Best-Practice-Katalog (ARCH-003). Siehe checks/ARCH-003.md für volle Pass-Criteria.

### Evidence

src/lobbywatch_mcp/client.py:184 best = process.extractOne(..., score_cutoff=70); if not best: return None
server.py:156-160 returns ParlamentarierResponse(parlamentarier=None) — kein 'did you mean'

### Risk Description

Schlechtes UX bei Tippfehlern; LLM muss reaktiv neu suchen statt direkt korrigiert zu werden.

### Remediation

```
Bei score zwischen 50–70: liefere top_3 candidates als Suggestion-Liste im Response-Envelope.
```

### Effort Estimate

S (< 1d)


### ARCH-008

## Finding: ARCH-008 — Drei Primitive nutzen: Tools, Resources und Prompts

**Severity:** medium
**Status:** open
**Server:** lobbywatch-mcp
**Check-Reference:** ARCH-008

### Observed Behavior

Nur @mcp.tool verwendet; keine Resources oder Prompts.

### Expected Behavior

Best-Practice-Katalog (ARCH-008). Siehe checks/ARCH-008.md für volle Pass-Criteria.

### Evidence

grep -rn '@mcp\.(resource|prompt)' src/ → 0 hits

### Risk Description

Verfehlt MCP-Architektur-Mehrwert: Attribution-Text als Resource, Anchor-Demo-Query als Prompt würden LLM-Lifecycle besser bedienen.

### Remediation

```
@mcp.resource('lobbywatch://attribution') → liefert ATTRIBUTION-String
@mcp.prompt('wbk_education_conflicts') → kanonischer Demo-Prompt aus README
```

### Effort Estimate

M (1-3d)


### ARCH-009

## Finding: ARCH-009 — Tool Annotations: readOnlyHint, destructiveHint, idempotentHint, openWorldHint

**Severity:** high
**Status:** open
**Server:** lobbywatch-mcp
**Check-Reference:** ARCH-009

### Observed Behavior

Keine der 8 Tools deklariert MCP Tool Annotations.

### Expected Behavior

Best-Practice-Katalog (ARCH-009). Siehe checks/ARCH-009.md für volle Pass-Criteria.

### Evidence

src/lobbywatch_mcp/server.py:146-401: alle @mcp.tool() ohne annotations=...

### Risk Description

Clients können nicht erkennen welche Tools sicher / read-only / external-data sind. UI-Hinweise (z.B. Confirmation-Prompts vor destructive Tools) fehlen.

### Remediation

```
@mcp.tool(annotations={'readOnlyHint': True, 'openWorldHint': False})
async def get_parlamentarier(...): ...

# refresh_dump → idempotentHint=True (re-running yields same cache state)
# get_lobbygruppe → openWorldHint=True (live external data)
```

### Effort Estimate

S (< 1d)


### ARCH-012

## Finding: ARCH-012 — protocolVersion-Pinning + CHANGELOG + SDK-Update-Disziplin

**Severity:** medium
**Status:** open
**Server:** lobbywatch-mcp
**Check-Reference:** ARCH-012

### Observed Behavior

mcp[cli]>=1.2.0 hat keinen Upper Bound; Protocol-Version wird nirgends gepinnt/geloggt.

### Expected Behavior

Best-Practice-Katalog (ARCH-012). Siehe checks/ARCH-012.md für volle Pass-Criteria.

### Evidence

pyproject.toml:40 mcp[cli]>=1.2.0

### Risk Description

Unkontrollierte SDK-Major-Bumps können Breaking Changes ohne CI-Signal einführen.

### Remediation

```
mcp[cli]>=1.2.0,<2.0.0 in pyproject.toml; logger.info("Using mcp protocolVersion=%s", PROTOCOL_VERSION) im server.py
```

### Effort Estimate

S (< 1d)


### OBS-001

## Finding: OBS-001 — Protocol vs. Execution Errors: korrekte Trennung

**Severity:** high
**Status:** open
**Server:** lobbywatch-mcp
**Check-Reference:** OBS-001

### Observed Behavior

ValueError/RuntimeError werden roh geraised statt FastMCP ToolError / McpError.

### Expected Behavior

Best-Practice-Katalog (OBS-001). Siehe checks/OBS-001.md für volle Pass-Criteria.

### Evidence

src/lobbywatch_mcp/server.py:292 raise ValueError(...)
src/lobbywatch_mcp/client.py:126,140,150 raise RuntimeError(...)

### Risk Description

Client kann nicht unterscheiden zwischen Protocol-Layer-Fehler (Server kaputt) und Tool-Execution-Fehler (User-Eingabe falsch). LLM erhält keine differenzierte Reaktion.

### Remediation

```
from mcp.shared.exceptions import McpError
from mcp.types import INVALID_PARAMS, INTERNAL_ERROR

raise McpError(ErrorData(code=INVALID_PARAMS, message=f'kriterium must be one of {sorted(allowed)}'))
```

### Effort Estimate

S (< 1d)


### OBS-002

## Finding: OBS-002 — Mask Error Details: keine Stacktraces / SQL ans LLM

**Severity:** high
**Status:** open
**Server:** lobbywatch-mcp
**Check-Reference:** OBS-002

### Observed Behavior

Error-Strings enthalten interne Strukturen (zip-Member-Listing, Type-Names).

### Expected Behavior

Best-Practice-Katalog (OBS-002). Siehe checks/OBS-002.md für volle Pass-Criteria.

### Evidence

src/lobbywatch_mcp/client.py:140 RuntimeError(f'Dump does not contain expected file. Got: {zf.namelist()}')
client.py:150 f'Unexpected dump shape: {type(data).__name__}'

### Risk Description

Interne Pfad-/Schema-Details propagieren ins LLM-Context und können als Reconnaissance-Hilfe dienen.

### Remediation

```
Generische User-Facing-Message + Detailed-Internal-Log: 
logger.error('Dump shape mismatch: %s', zf.namelist())
raise RuntimeError('Lobbywatch dump format unexpected; refresh required.')
```

### Effort Estimate

S (< 1d)


### OBS-003

## Finding: OBS-003 — Structured Logging mit RFC 5424 Severity-Stufen

**Severity:** medium
**Status:** open
**Server:** lobbywatch-mcp
**Check-Reference:** OBS-003

### Observed Behavior

Python-Standard-Logging ohne JSON/structlog; keine Request-IDs.

### Expected Behavior

Best-Practice-Katalog (OBS-003). Siehe checks/OBS-003.md für volle Pass-Criteria.

### Evidence

Nur logging.getLogger(__name__) in src/

### Risk Description

Schwer in SIEM zu indizieren; keine Korrelation Tool-Call ↔ Log-Lines.

### Remediation

```
structlog mit JSONRenderer; pro Tool-Call eine UUID4-Correlation-ID via context.
```

### Effort Estimate

M (1-3d)


### OBS-006

## Finding: OBS-006 — OpenTelemetry Distributed Tracing pro Tool-Call

**Severity:** medium
**Status:** open
**Server:** lobbywatch-mcp
**Check-Reference:** OBS-006

### Observed Behavior

Keine OTel-Instrumentation.

### Expected Behavior

Best-Practice-Katalog (OBS-006). Siehe checks/OBS-006.md für volle Pass-Criteria.

### Evidence

grep opentelemetry|otel src/ pyproject.toml → 0 hits

### Risk Description

Performance-Probleme im Tool-Pipeline (Dump-Parse, Fuzzy-Match, dataIF-Live-Call) sind ohne Tracing schwer zu lokalisieren.

### Remediation

```
opentelemetry-api + opentelemetry-instrumentation-httpx; Span pro Tool-Call mit tool_name als Attribute.
```

### Effort Estimate

M (1-3d)


### OPS-002

## Finding: OPS-002 — Doku-Standard: bilingualer README, ASCII-Diagramm, Limits-Sektion

**Severity:** medium
**Status:** open
**Server:** lobbywatch-mcp
**Check-Reference:** OPS-002

### Observed Behavior

Bilingual + Limits ✅, aber: ASCII-Architekturdiagramm fehlt; CI-Badge zeigt auf nicht-existenten Workflow.

### Expected Behavior

Best-Practice-Katalog (OPS-002). Siehe checks/OPS-002.md für volle Pass-Criteria.

### Evidence

README.md:3 [![CI](https://github.com/malkreide/lobbywatch-mcp/actions/workflows/ci.yml/badge.svg)] aber .github/workflows/ existiert nicht
Kein Diagramm dump-first / API-fallback

### Risk Description

Vertrauensverlust durch broken Badge (404). Architektur-Verständnis erschwert.

### Remediation

```
(a) ASCII-Diagramm: LLM → FastMCP → LobbywatchClient → {Dump-Cache | dataIF-Live} → cms.lobbywatch.ch
(b) .github/workflows/ci.yml anlegen ODER Badge entfernen.
```

### Effort Estimate

S (< 1d)


### SCALE-002

## Finding: SCALE-002 — Stateful Load Balancing für Streamable HTTP / SSE

**Severity:** high
**Status:** open
**Server:** lobbywatch-mcp
**Check-Reference:** SCALE-002

### Observed Behavior

README dokumentiert HTTP-Deployment, aber keinen Hinweis auf sticky-session-Anforderung.

### Expected Behavior

Best-Practice-Katalog (SCALE-002). Siehe checks/SCALE-002.md für volle Pass-Criteria.

### Evidence

Kein Dockerfile/k8s-Manifest/HAProxy-Config im Repo
README.md:74-76 zeigt einfachen `LOBBYWATCH_MCP_TRANSPORT=http`-Aufruf

### Risk Description

Operatoren deployen hinter Round-Robin-LB. Mcp-Session-Id-Continuity bricht; Clients erleben sporadische Session-Drops.

### Remediation

```
Sektion 'Deployment Notes' in README.md mit: 'Cloud HTTP requires Mcp-Session-Id-aware sticky LB. See SCALE-003 for HAProxy stick-table config.'
```

### Effort Estimate

S (< 1d)


### SCALE-003

## Finding: SCALE-003 — Mcp-Session-Id Routing via Edge-LB (HAProxy Stick-Tables)

**Severity:** high
**Status:** open
**Server:** lobbywatch-mcp
**Check-Reference:** SCALE-003

### Observed Behavior

Keine HAProxy-/Envoy-Beispielkonfiguration vorhanden.

### Expected Behavior

Best-Practice-Katalog (SCALE-003). Siehe checks/SCALE-003.md für volle Pass-Criteria.

### Evidence

find . -name '*.haproxy*' -o -name '*.envoy*' → 0 hits

### Risk Description

Wie SCALE-002 — Operatoren haben kein Referenzbeispiel und improvisieren.

### Remediation

```
deploy/haproxy.cfg (oder docs/) mit Stick-Table-Beispiel auf Mcp-Session-Id Header.
```

### Effort Estimate

M (1-3d)


### SCALE-004

## Finding: SCALE-004 — Containerization mit Multi-Stage-Builds

**Severity:** medium
**Status:** open
**Server:** lobbywatch-mcp
**Check-Reference:** SCALE-004

### Observed Behavior

Kein Dockerfile.

### Expected Behavior

Best-Practice-Katalog (SCALE-004). Siehe checks/SCALE-004.md für volle Pass-Criteria.

### Evidence

find . -name 'Dockerfile*' → 0 hits

### Risk Description

Cloud-Deployments improvisieren; reproduzierbares Build fehlt.

### Remediation

```
Multi-stage Dockerfile: builder (uv pip install) → runtime (slim, USER 1000, ENTRYPOINT ["lobbywatch-mcp"]).
```

### Effort Estimate

M (1-3d)


### SCALE-006

## Finding: SCALE-006 — Resource-Limits per Container (Memory, CPU, FDs)

**Severity:** medium
**Status:** open
**Server:** lobbywatch-mcp
**Check-Reference:** SCALE-006

### Observed Behavior

Keine Resource-Limits-Spec.

### Expected Behavior

Best-Practice-Katalog (SCALE-006). Siehe checks/SCALE-006.md für volle Pass-Criteria.

### Evidence

Kein Dockerfile / k8s-Manifest mit limits

### Risk Description

Dump (~17 MB komprimiert, ~80 MB im RAM) + 245 Records: ohne Memory-Limit kann ein Memory-Leak den Host instabil machen.

### Remediation

```
k8s-Manifest mit resources: requests {memory: 256Mi, cpu: 100m}, limits {memory: 512Mi, cpu: 500m}; ulimit -n im Dockerfile.
```

### Effort Estimate

S (< 1d)


### SDK-001

## Finding: SDK-001 — FastMCP Lifespan via @asynccontextmanager + AsyncExitStack

**Severity:** high
**Status:** open
**Server:** lobbywatch-mcp
**Check-Reference:** SDK-001

### Observed Behavior

FastMCP wird ohne lifespan= konstruiert. LobbywatchClient.aclose() wird in Produktion nie aufgerufen.

### Expected Behavior

Best-Practice-Katalog (SDK-001). Siehe checks/SDK-001.md für volle Pass-Criteria.

### Evidence

src/lobbywatch_mcp/server.py:134 FastMCP(name=..., instructions=...) - kein lifespan
src/lobbywatch_mcp/client.py:64 aclose() existiert aber ungenutzt
grep asynccontextmanager|AsyncExitStack|lifespan src/ → 0 hits

### Risk Description

httpx.AsyncClient leakt Connections beim Shutdown. Bei Cloud-Deployments (HTTP-Transport) führt das zu File-Descriptor-Leaks und unsauberem TCP-Teardown.

### Remediation

```
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(server):
    client = LobbywatchClient()
    try:
        yield {'client': client}
    finally:
        await client.aclose()

mcp = FastMCP(name='lobbywatch-mcp', lifespan=lifespan, ...)
```

### Effort Estimate

M (1-3d)


### SDK-002

## Finding: SDK-002 — Pydantic v2 / TypedDict / Dataclass als Tool-Returns

**Severity:** medium
**Status:** open
**Server:** lobbywatch-mcp
**Check-Reference:** SDK-002

### Observed Behavior

Tools returnen dict[str, Any] (nach .model_dump()) statt Pydantic-Modell direkt.

### Expected Behavior

Best-Practice-Katalog (SDK-002). Siehe checks/SDK-002.md für volle Pass-Criteria.

### Evidence

src/lobbywatch_mcp/server.py:147 -> dict[str, Any] (return ParlamentarierResponse(...).model_dump())

### Risk Description

FastMCP verliert Schema-Treue im Tool-Descriptor; Clients sehen generic 'object' statt strukturiertem Schema.

### Remediation

```
Direct return: -> ParlamentarierResponse mit return ParlamentarierResponse(...) (ohne .model_dump()).
```

### Effort Estimate

S (< 1d)


### SDK-003

## Finding: SDK-003 — Context Injection für Progress Reports und Logging

**Severity:** medium
**Status:** open
**Server:** lobbywatch-mcp
**Check-Reference:** SDK-003

### Observed Behavior

Kein ctx: Context Parameter; refresh_dump (Long-running, ~17 MB Download) hat keine Progress-Reports.

### Expected Behavior

Best-Practice-Katalog (SDK-003). Siehe checks/SDK-003.md für volle Pass-Criteria.

### Evidence

grep Context|ctx: src/lobbywatch_mcp/server.py → 0 hits

### Risk Description

User wartet blind während Dump-Download (10–60 s); kein progress-Feedback ans LLM.

### Remediation

```
async def refresh_dump(ctx: Context) -> ...:
    await ctx.info('Downloading weekly dump...')
    await ctx.report_progress(0.5, 1.0, 'Downloading...')
```

### Effort Estimate

S (< 1d)


### SDK-004

## Finding: SDK-004 — CORS Mcp-Session-Id Exposure bei HTTP/SSE

**Severity:** high
**Status:** open
**Server:** lobbywatch-mcp
**Check-Reference:** SDK-004

### Observed Behavior

Keine CORS-Konfiguration; Mcp-Session-Id-Header wird Browser-Clients nicht exponiert.

### Expected Behavior

Best-Practice-Katalog (SDK-004). Siehe checks/SDK-004.md für volle Pass-Criteria.

### Evidence

grep CORS|expose_headers|cors src/ → 0 hits
FastMCP-Defaults setzen Access-Control-Expose-Headers nicht für Mcp-Session-Id

### Risk Description

Browser-basierte Clients (Web-Inspector, custom UIs) verlieren Session-Continuity bei cross-origin requests; Tool-Calls schlagen sporadisch fehl.

### Remediation

```
FastMCP-Settings konfigurieren oder Starlette-Middleware hinzufügen: 
allow_origins=['https://your-app'], expose_headers=['Mcp-Session-Id']
```

### Effort Estimate

S (< 1d)


### SEC-004

## Finding: SEC-004 — SSRF-Prevention: HTTPS-Enforcement + IP-Blocklisting

**Severity:** critical
**Status:** open
**Server:** lobbywatch-mcp
**Check-Reference:** SEC-004
**PDF-Reference:** Sec 4.x / Anhang B

### Observed Behavior

`API_BASE` is hardcoded https → host is not user-controlled. However user-supplied `id_or_name` is interpolated raw into the URL path:

```python
# client.py:216
search = await self.api_get(f"search/default/{id_or_name}", params={"limit": 5})
```

`httpx.AsyncClient(follow_redirects=True)` (client.py:61) blindly follows 30x. No IP-blocklist, no link-local / metadata-IP guard, no allow-list of expected paths.

### Expected Behavior

- URL-encode user-supplied path segments (`urllib.parse.quote`)
- Validate `id_or_name` length / character set before interpolation
- Disable redirects or restrict to same-origin
- Add an httpx event hook that rejects responses from RFC1918 / link-local / 169.254.0.0/16 if the host ever resolves there

### Evidence

- `src/lobbywatch_mcp/client.py:216` — raw f-string interpolation of `id_or_name`
- `src/lobbywatch_mcp/client.py:61` — `follow_redirects=True`
- `src/lobbywatch_mcp/client.py:212` — numeric path uses `int(id_or_name)` (good — already coerced)

### Risk Description

Mostly mitigated by hardcoded host. Worst case: malformed `id_or_name="../../../admin/dump"` reaches an unintended cms.lobbywatch.ch endpoint. Risk escalates if `API_BASE` is ever made configurable or upstream introduces a redirect chain to a third-party CDN.

### Remediation

```diff
-        search = await self.api_get(f"search/default/{id_or_name}", params={"limit": 5})
+        from urllib.parse import quote
+        search = await self.api_get(f"search/default/{quote(str(id_or_name), safe='')}", params={"limit": 5})
```

Plus: turn off `follow_redirects` for `api_get` or whitelist hosts on redirect.

### Effort Estimate

S (< 1d)


### SEC-005

## Finding: SEC-005 — DNS-Rebinding-Prevention: DNS-Pinning gegen TOCTOU

**Severity:** high
**Status:** open
**Server:** lobbywatch-mcp
**Check-Reference:** SEC-005

### Observed Behavior

Kein DNS-Pinning. httpx-Default verwendet OS-Resolver pro Request.

### Expected Behavior

Best-Practice-Katalog (SEC-005). Siehe checks/SEC-005.md für volle Pass-Criteria.

### Evidence

grep DNS|resolve|getaddrinfo src/ → 0 hits

### Risk Description

Bei HTTP-Transport mit 0.0.0.0-Binding (siehe SEC-016): malicious DNS-Antwort kann zwischen TOCTOU-Window auf Metadata-IP wechseln.

### Remediation

```
Custom httpx Transport mit IP-pinning beim Startup, oder pinning der `cms.lobbywatch.ch`-Auflösung mit TTL-Cache.
```

### Effort Estimate

M (1-3d)


### SEC-007

## Finding: SEC-007 — Container-Sandboxing: Docker / chroot mit minimalen Privilegien

**Severity:** high
**Status:** open
**Server:** lobbywatch-mcp
**Check-Reference:** SEC-007

### Observed Behavior

Kein Dockerfile vorhanden; keine seccomp/AppArmor-Profile.

### Expected Behavior

Best-Practice-Katalog (SEC-007). Siehe checks/SEC-007.md für volle Pass-Criteria.

### Evidence

find . -name 'Dockerfile*' -o -name 'docker-compose*' → 0 hits

### Risk Description

Cloud-Deployment ohne Container = Process auf Host mit voller Privilege-Surface.

### Remediation

```
Multi-stage Dockerfile (siehe SCALE-004) mit `USER 1000`, `--read-only` rootfs, drop ALL capabilities ausser NET_BIND_SERVICE.
```

### Effort Estimate

M (1-3d)


### SEC-016

## Finding: SEC-016 — 0.0.0.0-Binding-Prevention (NeighborJack)

**Severity:** critical
**Status:** open
**Server:** lobbywatch-mcp
**Check-Reference:** SEC-016
**PDF-Reference:** Sec 4 / Anhang B

### Observed Behavior

`src/lobbywatch_mcp/__main__.py:19,25` defaults the HTTP/SSE bind host to `0.0.0.0`:

```python
host = os.getenv("LOBBYWATCH_MCP_HOST", "0.0.0.0")
```

`README.md:124` documents this default to operators. With no auth (`auth_model=none`), any device on the LAN can issue MCP calls when a developer runs `LOBBYWATCH_MCP_TRANSPORT=http lobbywatch-mcp`.

### Expected Behavior

Default to `127.0.0.1` (loopback). Operators wanting LAN/cloud exposure must set `LOBBYWATCH_MCP_HOST=0.0.0.0` explicitly and acknowledge they have placed an auth-gateway in front.

### Evidence

- File: `src/lobbywatch_mcp/__main__.py:19`
- File: `src/lobbywatch_mcp/__main__.py:25`
- Doc: `README.md:124` lists default as `0.0.0.0`

### Risk Description

Coffee-shop / corporate-LAN attack: a colleague's laptop on the same Wi-Fi can curl the server, exfiltrate the (admittedly public) data, and abuse the local cache; in production this is the canonical NeighborJack configuration.

### Remediation

```diff
-        host = os.getenv("LOBBYWATCH_MCP_HOST", "0.0.0.0")
+        host = os.getenv("LOBBYWATCH_MCP_HOST", "127.0.0.1")
```

Update README config table accordingly. Consider emitting a `logger.warning` at startup when host == "0.0.0.0" and auth_model == "none".

### Effort Estimate

S (< 1d)


### SEC-018

## Finding: SEC-018 — Input-Validation an Tool-Boundaries (Pydantic strict)

**Severity:** high
**Status:** open
**Server:** lobbywatch-mcp
**Check-Reference:** SEC-018

### Observed Behavior

Pydantic-Modelle nutzen extra='allow' und kein strict-Mode. Tool-Parameter haben unbegrenzte Range.

### Expected Behavior

Best-Practice-Katalog (SEC-018). Siehe checks/SEC-018.md für volle Pass-Criteria.

### Evidence

src/lobbywatch_mcp/models.py:19,28,51,67,81 ConfigDict(extra='allow')
src/lobbywatch_mcp/server.py:202 limit: int = 25 (kein Upper Bound)
server.py:223 branche_query.strip().lower() (kein Length-Check)

### Risk Description

DoS via `limit=10**9` triggert Full-Scan über alle 245 Parlamentarier × 7800 IBs. Unbegrenzte Strings können RegEx-Engines stressen.

### Remediation

```
Annotated[int, Field(ge=1, le=200)] für limit; Annotated[str, Field(min_length=1, max_length=200)] für query-Strings; ConfigDict(extra='forbid') für Response-Modelle.
```

### Effort Estimate

M (1-3d)


### SEC-021

## Finding: SEC-021 — Egress-Allow-List: Code-Layer und Network-Layer

**Severity:** high
**Status:** open
**Server:** lobbywatch-mcp
**Check-Reference:** SEC-021

### Observed Behavior

Code-Layer-Allow-List existiert (hardcoded URLs), aber kein Network-Layer-Egress-Control.

### Expected Behavior

Best-Practice-Katalog (SEC-021). Siehe checks/SEC-021.md für volle Pass-Criteria.

### Evidence

src/lobbywatch_mcp/config.py:13-23 hardcoded URLs (gut)
Kein Proxy/Mount im httpx-Client; kein Firewall-Manifest

### Risk Description

Wenn ein DI-replaced Client (z.B. in Tests oder Fork) andere Hosts ansteuert, gibt es keine Schutzschicht.

### Remediation

```
Optional: httpx.AsyncClient(transport=AllowListTransport(['cms.lobbywatch.ch']))
Deployment-Doku: 'Container should run with NetworkPolicy egress allow-list to cms.lobbywatch.ch:443 only'.
```

### Effort Estimate

M (1-3d)


### SEC-022

## Finding: SEC-022 — Tool-Hash-Pinning + Namespace-Präfix gegen Rug Pull

**Severity:** high
**Status:** open
**Server:** lobbywatch-mcp
**Check-Reference:** SEC-022

### Observed Behavior

Tool-Namen wie `get_parlamentarier` sind nicht namespaced.

### Expected Behavior

Best-Practice-Katalog (SEC-022). Siehe checks/SEC-022.md für volle Pass-Criteria.

### Evidence

src/lobbywatch_mcp/server.py:147 async def get_parlamentarier — kein lobbywatch_-Präfix
Kollisionsrisiko mit parlament-mcp (Portfolio enthält beide)

### Risk Description

Wenn beide Server (lobbywatch-mcp + parlament-mcp) gleichzeitig laufen, kollidieren Tool-Namen oder ein bösartiger Server-Update überschreibt semantisch die Bedeutung beim Client.

### Remediation

```
Tools umbenennen: lobbywatch_get_parlamentarier, lobbywatch_list_interessenbindungen, lobbywatch_search_branche, lobbywatch_get_lobbygruppe, lobbywatch_get_ranking, lobbywatch_get_transparenzquote, lobbywatch_refresh_dump, lobbywatch_dump_status.
```

### Effort Estimate

M (1-3d)


---

## 6. Remediation-Plan

### Empfohlene Reihenfolge

1. **SEC-004** (critical, partial)
2. **SEC-016** (critical, fail)
3. **ARCH-009** (high, fail)
4. **OBS-001** (high, partial)
5. **OBS-002** (high, partial)
6. **SCALE-002** (high, fail)
7. **SCALE-003** (high, fail)
8. **SDK-001** (high, fail)
9. **SDK-004** (high, fail)
10. **SEC-005** (high, fail)
11. **SEC-007** (high, fail)
12. **SEC-018** (high, partial)
13. **SEC-021** (high, fail)
14. **SEC-022** (high, fail)
15. **ARCH-002** (medium, fail)
16. **ARCH-003** (medium, partial)
17. **ARCH-008** (medium, fail)
18. **ARCH-012** (medium, partial)
19. **OBS-003** (medium, partial)
20. **OBS-006** (medium, fail)
21. **OPS-002** (medium, partial)
22. **SCALE-004** (medium, fail)
23. **SCALE-006** (medium, fail)
24. **SDK-002** (medium, partial)
25. **SDK-003** (medium, fail)

---

## 7. Audit-Metadata

| Feld | Wert |
|---|---|
| skill_version | `1.0.0` |
| policy | `fail-or-partial` |


_Generated by tools/build_report.py — do not edit by hand._
