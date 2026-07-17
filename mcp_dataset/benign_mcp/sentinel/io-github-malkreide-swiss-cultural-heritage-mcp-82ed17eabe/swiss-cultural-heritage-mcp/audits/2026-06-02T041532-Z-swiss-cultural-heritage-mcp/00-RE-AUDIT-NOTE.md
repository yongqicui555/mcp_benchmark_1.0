# Re-Audit Note — 2026-06-02

This is a **full re-audit** of `swiss-cultural-heritage-mcp` against the
`mcp-audit-skill` v0.5.0 catalog (68 checks), run from a local clone of the
skill (`SKILL_MODE=local`, catalog hash `091f446b…`). It supersedes the
representative-sample audit of **2026-05-21**. Canonical output:
[`audit-report.md`](audit-report.md); machine-readable single-source-of-truth:
[`summary.json`](summary.json).

## Headline

- **44 checks applicable** (after the `applies_when` filter); 3 of them are
  recorded **n/a in practice** (see below), so **41 are scored**.
- **20 pass · 4 fail · 17 partial · 3 n/a**.
- **21 findings** (2 critical, 9 high, 10 medium) under the default
  `fail-or-partial` policy.
- **Production-ready: NO — but blocked by exactly one finding: `OBS-002`.**

## The one blocker

`blocking_findings = ["OBS-002"]`. The server deliberately lets programming
errors propagate to the framework (good, per `OBS-001`), but FastMCP is
constructed **without `mask_error_details=True`**, so an unhandled exception's
raw text reaches the client. Setting `mask_error_details=True` on the
`FastMCP(...)` constructor is a one-line fix that clears the only
production blocker. Everything else is `partial`/medium and non-blocking.

## Delta vs. the 2026-05-21 audit (all prior findings re-checked)

| Prior finding (2026-05-21) | Status now |
|---|---|
| `SDK-001` — no shared HTTP client / lifespan | **FIXED** → `lifespan` + shared `httpx.AsyncClient` (SDK-001 PASS) |
| `SEC-021` — no egress allow-list, `follow_redirects=True` | **FIXED** → `ALLOWED_HOSTS` frozenset, per-hop re-check, `follow_redirects=False` (SEC-021 PASS) |
| `SEC (XML)` — unsafe `xml.etree` | **FIXED** → `defusedxml.ElementTree` (SEC-020 PASS) |
| `SEC-007` — no container/sandbox | **FIXED** → hardened Dockerfile + `docs/security.md` (SEC-007 PASS) |
| `CH-001` — data residency undocumented | **FIXED** → `docs/data-residency.md` + Frankfurt region (CH-001 no longer applicable in this run) |
| `ARCH` — wrong `idempotentHint`, missing input model | **FIXED** → corrected hints + `NbCollectionsInput` (ARCH-009 PASS) |
| `OBS-001` — errors as German strings | **IMPROVED, still partial** → narrow `ExpectedUpstreamError`; remaining gap is `isError`-flagging |
| `OPS-001` — test strategy | **PASS** → respx + `@pytest.mark.live` + nightly workflow |

The remediation between 0.1.0 → 0.2.0/Unreleased closed every high-severity
code finding from the first audit. The new findings in this run come from
sweeping **all 44 applicable checks** (the first audit scored a representative
subset), not from regressions.

## Checks recorded `n/a` in practice (coarse filter included them)

The boolean `applies_when` filter is intentionally loud; three checks it
matched are not meaningfully applicable to this profile and are documented
rather than scored (skill anti-pattern #5):

- **SEC-009** (Session-ID cryptographic binding, critical) — `auth_model=none`;
  no user identity and no per-user data to bind. Session IDs are
  framework-generated.
- **SEC-014** (Tool allow-listing via MCP gateway) — `enterprise_context=false`;
  no gateway / multi-team context.
- **SEC-015** (Pre-flight tool-poisoning detection) — gateway-layer control; no
  gateway fronts this standalone server.

## On the critical `partial`s (not blockers)

- **SEC-004 / SEC-005** (SSRF / DNS-rebinding) — the practical vector is
  **already closed** by the two-host egress allow-list (`SEC-021` PASS) and the
  fact that no user input controls the request host. The gaps are IP-level
  defense-in-depth (resolved-IP blocklist, DNS-pinning), recommended but low
  real risk while the allow-list holds two trusted Swiss-federal hosts.
- **SEC-019** (lethal trifecta) — the server does **not** hold the trifecta
  (public data only, no write/send channel, egress-restricted). The finding is
  a documentation gap: add an explicit trifecta assessment to `docs/security.md`.

## Reproduce

```bash
git clone --depth 1 https://github.com/malkreide/mcp-audit-skill /tmp/mcp-audit-skill
SKILL=/tmp/mcp-audit-skill ; OUT=audits/2026-06-02T041532-Z-swiss-cultural-heritage-mcp
python3 $SKILL/tools/validate_profile.py     $OUT/profile.yaml
python3 $SKILL/tools/eval_applicability.py    catalog $OUT/profile.yaml --checks-dir $SKILL/checks --format table
python3 $SKILL/tools/aggregate_results.py     aggregate $OUT/verification-results.json --policy fail-or-partial --out $OUT/summary.json
python3 $OUT/gen_findings.py
python3 $SKILL/tools/aggregate_results.py     validate $OUT
python3 $SKILL/tools/build_report.py          $OUT --profile $OUT/profile.yaml
```
