# Data Residency (revDSG / EDÖB)

This document records the data-residency posture of `swiss-cultural-heritage-mcp` for Swiss public-sector readers. Maps to audit finding [`CH-001`](../audits/2026-05-21-swiss-cultural-heritage-mcp/findings/CH-001-data-residency-docs.md).

## Scope of personal data

**None directly processed.** The upstream APIs (opendata.swiss CKAN — SIKART artists + Nationalmuseum datasets; Nationalbibliothek OAI-PMH) return institutional records: artist biographies, museum objects, bibliographic metadata. The server is stateless: no database, no cache, no logging of request bodies.

However, **request strings can carry personal data incidentally** — a user searching for their own family name, a query that includes a learner's name, etc. Operators should treat HTTP access logs accordingly.

## Recommended hosting regions

| Region class | Acceptable? | Notes |
|---|---|---|
| Switzerland (Zurich, Geneva) | ✅ Preferred | revDSG Art. 16 fully satisfied |
| EU / EEA (Frankfurt, Amsterdam, Dublin, Stockholm) | ✅ Yes | Adequacy under Swiss data protection law |
| United States | ❌ Not recommended | Cross-border transfer requires additional safeguards |
| Asia-Pacific | ❌ Not recommended | No adequacy decision |
| Global edge (no region lock) | ❌ Not recommended | Data may transit non-adequate regions |

## Render.com

Render's default region is US-West. **For Swiss public-sector deployments select the `Frankfurt` region** when creating the Web Service. The region picker appears in the same step where you choose the start command.

## Logging endpoints

If you add an APM or log-aggregation service (Sentry, Datadog, etc.), use the EU endpoint:

- Sentry: `*.eu.sentry.io` (not `*.sentry.io`)
- Datadog: `app.datadoghq.eu` (not `app.datadoghq.com`)
- Honeycomb: select the EU instance during onboarding

## Third-party API calls

The server's allow-list (`docs/network-egress.md`) restricts outbound traffic to:

- `ckan.opendata.swiss` — opendata.swiss CKAN portal (Swiss Confederation)
- `helveticat.nb.admin.ch` — Helveticat OAI-PMH (Schweizerische Nationalbibliothek)

Both upstreams are Swiss federal services, so the server itself does not generate cross-border data transfers regardless of where it is deployed. The residency concern applies to the deployment host (which receives request strings) and any logging/observability backend you attach.

## Processing inventory (revDSG Art. 12)

| Item | Value |
|---|---|
| Purpose | Read-only access to Swiss public cultural heritage data |
| Data categories | Search queries (may incidentally contain personal data); responses contain no personal data of end users |
| Recipients | Two Swiss public-sector upstream hosts (see allow-list) |
| Cross-border transfers | None at the application layer; depends on deployment region |
| Retention | None — server is stateless |
| Security measures | TLS to upstreams; egress allow-list; defusedxml; Pydantic input validation; container hardening (see `security.md`) |

Operators in regulated environments should fold this row into their own processing inventory.
