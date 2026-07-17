# Server Profile — swiss-cultural-heritage-mcp

**Date:** 2026-05-21
**Auditor:** Claude (mcp-audit-skill methodology)
**Skill Source:** https://github.com/malkreide/mcp-audit-skill
**Repository:** https://github.com/malkreide/swiss-cultural-heritage-mcp
**Commit / Branch:** `claude/audit-mcp-skill-JGJI1` (HEAD `aef77c6`)

---

## Server Properties

| Property | Value |
|---|---|
| Language / Runtime | Python 3.11+ |
| SDK | FastMCP (`mcp[cli]>=1.0.0`) |
| Transport | stdio (default) + Streamable HTTP (`--http --port`) |
| Authentication | None (public read-only data) |
| Write operations | None — all tools `readOnlyHint: true` |
| Destructive operations | None |
| External upstreams | `api.sik-isea.ch`, `opendata.swiss`, `nb.admin.ch` (3 hardcoded hosts) |
| Personal data (PII) | None — institutional records only |
| Persistence | None — stateless |
| Tools | 7 (`heritage_*`) |
| Resources | 2 |
| Prompts | 2 |
| Deployment targets | Claude Desktop (stdio), Render.com (HTTP) |
| Test suite | `pytest` + `respx`; 38 unit cases, 5 live cases; CI excludes `live` marker |
| License | MIT |
| Domain | Swiss cultural heritage (CH-relevant compliance scope) |

## Applicability Filter

The full catalog has 68 checks. Based on the server profile, the following blocks are **not applicable** and were skipped:

| Category | Excluded | Reason |
|---|---|---|
| ARCH-010 (Idempotency keys) | n/a | No write operations |
| HITL-005 (Destructive confirmation) | n/a | No destructive tools |
| SEC-001/002/003 (OAuth 2.1 / PKCE / Resource Indicators) | n/a | No auth surface; public anonymous APIs |
| SEC-013 (Least-privilege service accounts) | n/a | No credentials handled |
| SCALE-005 (Gateway stacking) | partial | Single-tenant deployment; stacking is optional |

Applied: representative checks across ARCH, SDK, SEC, OBS, OPS, CH covering the threat model relevant to a read-only, anonymous, public-data MCP server.
