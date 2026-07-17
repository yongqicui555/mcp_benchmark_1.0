#!/usr/bin/env python3
"""Generate finding docs (one per fail/partial check) from verification-results.json.

Reproducible companion to the audit run. Filenames follow <CHECK-ID>-<slug>.md so
tools/aggregate_results.py validate matches them against summary.json.
"""
from __future__ import annotations
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
vr = json.loads((HERE / "verification-results.json").read_text(encoding="utf-8"))
results = vr["results"]
server = vr["audit_meta"]["server_name"]
date = "2026-06-02"

# Per-finding: slug, title, pdf_ref, expected, risk, remediation, effort
F = {
    "ARCH-003": dict(slug="not-found-heuristics", title="«Not Found» Anti-Pattern: Heuristiken statt leerer Antworten", pdf="Sec 2.x", effort="S",
        expected="Search tools that return no results should offer a fuzzy match or a suggestion mechanism and expose a match_type field (exact/fuzzy/none); on none, give an actionable hint.",
        risk="On a typo or near-miss query the LLM gets a flat «keine Treffer» and tends to give up or hallucinate, instead of being steered to a corrected term or a sibling tool.",
        rem="Add a `match_type` field to JSON responses; on zero exact hits for SIKART/SNM, retry with a loosened CKAN `q` (partial/OR) and label results `fuzzy`. Keep the existing textual tips. OAI-PMH (NB) has no server-side search, so document the exact-only behaviour there."),
    "ARCH-004": dict(slug="config-settings-object", title="Inversion of Control: Settings-Objekt statt globale Module-Vars", pdf="Sec 2.x", effort="M",
        expected="Configuration (endpoints, timeouts, allow-list, host/port) should come from a Pydantic-Settings object loaded once, not from module-level constants; transport selectable via ENV.",
        risk="Module-global config cannot be overridden per environment without editing code; tests and multi-env deploys monkeypatch globals, which is brittle.",
        rem="Introduce a `Settings(BaseSettings)` with fields for CKAN base URL, timeout, allow-list, transport, host, port (env-prefixed). Instantiate once at startup and inject. Replace the `sys.argv` flag parsing with `MCP_TRANSPORT`/`MCP_HOST`/`MCP_PORT` env vars."),
    "ARCH-011": dict(slug="single-file-tools-layout", title="Repo-Struktur: tools/-Aufteilung bei > 5 Tools", pdf="Sec 2.x", effort="S",
        expected="With more than 5 tools, split tool definitions into a tools/ package (file per group), or justify the single-file layout in the README.",
        risk="A 1300-line single module is harder to navigate and review; the >5-tool guideline exists to keep per-group ownership clear.",
        rem="Either split server.py into `tools/sik_isea.py`, `tools/snm.py`, `tools/nb.py`, `tools/cross.py` registered on the shared `mcp`, or add a short 'Project Structure' note in README explaining the deliberate single-file choice."),
    "ARCH-012": dict(slug="protocol-version-pinning", title="protocolVersion-Pinning + SDK-Update-Disziplin", pdf="Sec 2.x", effort="S",
        expected="protocolVersion explicitly pinned in code; a README 'MCP Protocol Version' section with an update policy; Dependabot/Renovate for monthly SDK PRs.",
        risk="An SDK upgrade can silently bump the negotiated protocol version; without pinning and a changelog discipline, behaviour drifts between releases unnoticed.",
        rem="Document and (where the SDK exposes it) pin the supported MCP protocol version; add a 'MCP Protocol Version' README section; add `.github/dependabot.yml` (pip, weekly/monthly) so `mcp` upgrades arrive as reviewable PRs."),
    "CH-004": dict(slug="ogd-license-attribution", title="OGD-CH Lizenz-Compliance: CC BY Attribution pro Datensatz", pdf="CH custom", effort="S",
        expected="Tool responses carry a structured source+licence field per dataset; provenance preserved per record in aggregation; attribution text per the licence (author, source, licence).",
        risk="Open-government data under CC BY requires attribution; aggregated answers that drop the source/licence per record put the consumer at risk of a licence breach.",
        rem="Add a `source` block (`{name, url, license}`) to every JSON response and a footer line in markdown; in `heritage_cross_search` keep provenance per item, not just per section header."),
    "OBS-001": dict(slug="execution-error-iserror", title="Protocol vs. Execution Errors: isError-Flagging", pdf="Sec 6.x", effort="M",
        expected="Handled application errors should be returned as tool results flagged isError:true (not as plain success strings), so the client can distinguish failure from content.",
        risk="A German «Fehler: …» string is indistinguishable to the LLM from a normal answer; it may relay the error as fact or retry incorrectly.",
        rem="Return execution errors via the FastMCP error path (raise a McpError / return an error-flagged result) instead of `return _handle_error(e)` strings, or wrap the string in a structured `{is_error: true, message}` envelope. Add a test asserting the error result is flagged."),
    "OBS-002": dict(slug="mask-error-details", title="Mask Error Details: keine internen Exceptions ans LLM", pdf="Sec 6.x", effort="S",
        expected="FastMCP initialised with mask_error_details=True so that unhandled exceptions surface a generic message to the client, with the real error only in server logs.",
        risk="BLOCKING. OBS-001 deliberately lets programming errors (KeyError/TypeError/…) propagate. Without mask_error_details, FastMCP's default puts the raw exception text into the client-visible error — internal detail (field names, code paths) leaks to the LLM/end user.",
        rem="Set `mcp = FastMCP(\"swiss_cultural_heritage_mcp\", lifespan=lifespan, mask_error_details=True)`. Add a test that triggers a programming error and asserts the client message is generic. This single change unblocks production-readiness."),
    "OBS-003": dict(slug="structured-logging", title="Structured Logging mit Severity-Stufen", pdf="Sec 6.x", effort="S",
        expected="A structured logger (structlog/loguru) emitting JSON/logfmt to stderr, with per-tool-call bound context (tool name, session id) and >=4 severity levels.",
        risk="With zero logging, operational incidents in the cloud deployment are undiagnosable: no record of which tool ran, which upstream failed, or how often.",
        rem="Add structlog configured with `WriteLoggerFactory(file=sys.stderr)` (keeps stdout clean — see OBS-004); bind tool name + session id per call; log upstream failures at warning/error. Keep payloads out of logs (no PII)."),
    "OBS-006": dict(slug="opentelemetry-tracing", title="OpenTelemetry Distributed Tracing pro Tool-Call", pdf="Sec 6.x", effort="M",
        expected="OTel SDK + OTLP exporter, httpx auto-instrumentation, one span per tool call (mcp.tool.name, is_error), OTLP endpoint via env var, no sensitive data in attributes.",
        risk="No tracing means upstream latency (SIKART/SNM/NB) and cross-search fan-out cannot be observed in production; slow-source diagnosis is guesswork.",
        rem="Add opentelemetry-sdk + opentelemetry-instrumentation-httpx; wrap each tool body in a span; configure the OTLP endpoint via `OTEL_EXPORTER_OTLP_ENDPOINT`; set service.name + environment. Gate it behind the env var so stdio/local stays zero-overhead."),
    "OPS-003": dict(slug="phase-declaration", title="Phasenarchitektur: Phase explizit deklarieren", pdf="App. C", effort="S",
        expected="Current phase (1/2/3) declared in README; a roadmap file with phase-specific tasks and documented transition prerequisites.",
        risk="Without an explicit phase declaration, contributors may add write/destructive tools without triggering the Phase 1->2 gate (audit, ISDS, DSG processing record).",
        rem="Add a 'Phase' line to the README ('Phase 1 — read-only') and a `docs/roadmap.md` listing Phase 1 scope and the Phase 2 prerequisites. Record phase transitions in CHANGELOG."),
    "SCALE-002": dict(slug="stateful-load-balancing", title="Stateful Load Balancing für Streamable HTTP", pdf="Sec 5.x", effort="M",
        expected="Sticky sessions on Mcp-Session-Id at the edge LB, or a shared-state session manager (Redis/Durable Objects), with an explicit session TTL — or a documented single-instance constraint.",
        risk="If the Render service is scaled to >1 instance without affinity, a client's follow-up request can land on an instance that does not know its session, breaking the stream.",
        rem="For now, document the single-instance constraint and the session TTL in docs/. Before horizontal scaling, add sticky sessions on `Mcp-Session-Id` (Variant A) or a Redis session backend (Variant B)."),
    "SCALE-003": dict(slug="session-id-edge-routing", title="Mcp-Session-Id Routing via Edge-LB", pdf="Sec 5.x", effort="M",
        expected="Edge LB reads Mcp-Session-Id and routes via a stick-table/hash with adequate capacity and an explicit TTL; failover tested so sessions are not silently re-homed without shared state.",
        risk="Same horizontal-scaling failure mode as SCALE-002, viewed from the LB layer.",
        rem="When moving beyond single-instance: configure HAProxy/Nginx/Ingress to hash on `Mcp-Session-Id` with TTL ~= session TTL, and test backend-failover behaviour. Until then, document that the deployment is single-instance."),
    "SCALE-004": dict(slug="multistage-dockerfile-healthcheck", title="Containerization: Multi-Stage-Build + HEALTHCHECK", pdf="Sec 5.x", effort="S",
        expected="Dockerfile with >=2 named stages (builder/runtime), slim/alpine final base, non-root user, and a HEALTHCHECK directive; final image < 200 MB.",
        risk="A single-stage image can carry build artefacts into the runtime layer (larger surface); a missing HEALTHCHECK means orchestrators cannot detect a wedged process.",
        rem="Split the Dockerfile into `AS builder` (pip install/wheel) and `AS runtime` (copy site-packages only); add `HEALTHCHECK --interval=30s CMD python -c \"import urllib.request,sys; urllib.request.urlopen('http://127.0.0.1:8000/health')\"` (or curl)."),
    "SCALE-006": dict(slug="resource-limits", title="Resource-Limits per Container (Memory, CPU, FDs)", pdf="Sec 5.x", effort="S",
        expected="Explicit memory and CPU limits (requests < limits), FD limit >= 4096 for many outbound connections, and tested clean OOM/restart behaviour.",
        risk="Without limits a runaway request (e.g. large OAI-PMH ListRecords parse) can exhaust the host; without a restart policy a crash means downtime.",
        rem="Document recommended `resources.requests/limits` (e.g. 128Mi/256Mi, 100m/500m) in docs/, set `restartPolicy`, and note `ulimit -n` guidance. For Render, document the chosen instance size."),
    "SDK-002": dict(slug="structured-tool-returns", title="Strukturierte Tool-Returns / Response-Envelope", pdf="Sec 3.x", effort="S",
        expected="Tools return typed objects (Pydantic/TypedDict/dict[str,X]) with a consistent envelope (source, provenance, results, count), not hand-built strings.",
        risk="String returns force the client to re-parse markdown; there is no machine-stable contract, so downstream automation is fragile and counts/provenance are inconsistent.",
        rem="Define a `SearchResult`/`ResultEnvelope` Pydantic model (`source`, `count`, `results`, optional `has_more`) and return it from search/list tools; keep a `response_format='markdown'` rendering as a thin view over the structured object."),
    "SDK-003": dict(slug="context-injection-progress", title="Context Injection für Progress und Logging", pdf="Sec 3.x", effort="S",
        expected="Tools expected to run >2s take ctx: Context and call ctx.report_progress(); non-fatal issues logged via ctx.warning()/ctx.error() rather than swallowed.",
        risk="heritage_cross_search fans out to three upstreams and silently folds per-source errors into the result text; the client gets no progress signal and no structured warning.",
        rem="Add `ctx: Context` to heritage_cross_search; call `await ctx.report_progress()` per completed source and `await ctx.warning(...)` for each failing source instead of only embedding the error string."),
    "SDK-004": dict(slug="cors-mcp-session-id", title="CORS Mcp-Session-Id Exposure bei HTTP/SSE", pdf="Sec 3.x", effort="S",
        expected="CORS middleware configured for HTTP/SSE; expose_headers and allow_headers include Mcp-Session-Id; allow_origins is an explicit non-wildcard list in production.",
        risk="The README advertises browser access, but browsers cannot read Mcp-Session-Id unless it is in expose_headers — SSE session continuity breaks for browser clients.",
        rem="Mount Starlette `CORSMiddleware` on the Streamable-HTTP app with `expose_headers=['Mcp-Session-Id']`, `allow_headers=['Mcp-Session-Id','Content-Type']`, and an env-driven `allow_origins` allow-list (no `*` in prod)."),
    "SEC-004": dict(slug="ssrf-ip-controls", title="SSRF-Prevention: HTTPS-Enforce + IP-Blocklisting (Defense-in-Depth)", pdf="Sec 4.x", effort="M",
        expected="Explicit https-scheme check before each request; resolved-IP blocklist for private/link-local/loopback incl. 169.254.169.254 and IPv6 (::1, fe80::/10); single DNS resolution reused (no TOCTOU).",
        risk="Low live risk: the 2-host egress allow-list already blocks metadata IPs and there is no user-controlled host. The gap is missing belt-and-suspenders IP-level controls should the allow-list ever widen or a host be added carelessly.",
        rem="In _assert_allowed also assert `httpx.URL(url).scheme == 'https'`; optionally add a resolved-IP blocklist guard for defense-in-depth. Keep the host allow-list as the primary control. Prioritise below the code-finding backlog given the closed allow-list."),
    "SEC-005": dict(slug="dns-rebinding-pinning", title="DNS-Rebinding-Prevention: DNS-Pinning", pdf="Sec 4.x", effort="M",
        expected="DNS resolved once per request and the resolved IP pinned for the TCP connection; original hostname kept for SNI/Host/cert validation.",
        risk="Theoretical TOCTOU only: an attacker would need to control DNS for one of the two fixed Swiss-federal hosts. Real-world risk is minimal given the closed allow-list.",
        rem="If hardening to spec: use a custom httpx transport/resolver that pins the first resolved A/AAAA record and validates the certificate against the original hostname. Treat as low priority while the allow-list holds two trusted hosts."),
    "SEC-019": dict(slug="lethal-trifecta-assessment", title="Lethal Trifecta: Bewertung dokumentieren", pdf="Sec 4.x", effort="S",
        expected="An explicit lethal-trifecta assessment in docs/ confirming the server holds at most two of {private-data access, untrusted-content exposure, exfiltration}; receiver allow-lists as frozensets.",
        risk="The server does NOT possess the trifecta (public data only, no send/write channel), but the absence of a written assessment means a future contributor could add an exfiltration-capable tool without re-evaluating.",
        rem="Add a short 'Lethal Trifecta' subsection to docs/security.md stating: data is public (not private), no outbound send/write capability, egress restricted to ALLOWED_HOSTS — therefore the trifecta is not present. Re-evaluate on any new tool with a send/write side effect."),
    "SEC-022": dict(slug="tool-namespace-hash-pinning", title="Tool-Hash-Pinning + Namespace-Präfix gegen Rug Pull", pdf="Sec 4.x", effort="M",
        expected="Tools namespaced with server identity (<server>__<tool>); a tool-definition hash snapshot generated per release; CHANGELOG flags tool-description changes with a re-approval note.",
        risk="A silently changed tool description (rug pull) could re-task the LLM. The heritage_ prefix is consistent but not server-identified, and there is no release-time hash to detect definition drift.",
        rem="Optionally adopt a `<server>__<tool>` prefix (breaking — major bump); add a release step that hashes tool names+descriptions+schemas into `audits/tool-pins/<version>.json`; add a CHANGELOG note when any tool description changes, prompting user re-approval."),
}

findings_dir = HERE / "findings"
findings_dir.mkdir(exist_ok=True)
written = []
for cid, meta in F.items():
    r = results[cid]
    obs_ev = "\n".join(f"- {e}" for e in r["evidence"]) or "- (see check execution log)"
    gaps = "\n".join(f"- {g}" for g in r["gaps"]) or "- (none recorded)"
    body = f"""## Finding: {cid} — {meta['title']}

| Feld | Wert |
|---|---|
| **Severity** | {r['severity']} |
| **Status** | open |
| **Server** | `{server}` |
| **Check-Reference** | `{cid}` |
| **PDF-Reference** | {meta['pdf']} |
| **Audit-Datum** | {date} |
| **Auditor** | Claude (mcp-audit-skill) |

### Observed Behavior

{obs_ev}

### Gaps vs. Pass Criteria

{gaps}

### Expected Behavior

{meta['expected']}

### Risk Description

{meta['risk']}

### Remediation

{meta['rem']}

### Effort Estimate

**{meta['effort']}**  (S < 1d · M 1–3d · L 1–2w · XL > 2w)

### Verification After Fix

Re-run check `{cid}` from the mcp-audit-skill catalog; add/adjust the pytest case noted in the remediation where applicable.
"""
    fp = findings_dir / f"{cid}-{meta['slug']}.md"
    fp.write_text(body, encoding="utf-8")
    written.append(fp.name)

print(f"wrote {len(written)} findings:")
for w in sorted(written):
    print(" ", w)
