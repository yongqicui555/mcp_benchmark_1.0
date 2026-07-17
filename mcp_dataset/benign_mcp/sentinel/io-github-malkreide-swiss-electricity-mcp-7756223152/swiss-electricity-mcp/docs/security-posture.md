# Security posture

Companion to [`network-egress.md`](network-egress.md). Records the deliberate
security decisions for this read-only, public-open-data MCP server.

## Lethal trifecta assessment (SEC-019)

The "lethal trifecta" is the dangerous combination of (1) access to private
data, (2) exposure to untrusted content, and (3) the ability to exfiltrate. A
server should hold **at most two** of the three.

| Capability | Present? | Notes |
|---|---|---|
| Access to private/sensitive data | **No** | Only public Swiss open data (CC0 / CC BY 4.0); no auth, no PII, no private stores. |
| Exposure to untrusted content | Partial | Reads JSON/SPARQL responses from four fixed official upstreams; values are parsed into typed models, never executed. |
| Ability to exfiltrate | **No** | No outbound channel beyond the four allow-listed read endpoints; no write/mail/webhook tools; egress is a code-layer `frozenset` + HTTPS gate. |

**Conclusion:** at most one of the three capabilities is meaningfully present, so
the trifecta risk is low by construction. Any future change that adds private
data, a write/exfiltration path, or dynamic egress must update this assessment
and re-run the audit before merge.

## Secret management (SEC-013)

This server uses **no secrets**. All four upstreams are anonymously accessible
public open-data endpoints — there are no API keys, tokens, or credentials in
the code, environment, or deployment. Consequently:

- There is nothing to store in a secret manager.
- `.env`/`.env.*` are git-ignored as a guardrail; `secret-scan.yml` (Gitleaks)
  runs on every push/PR to catch accidental introductions.
- If a future upstream ever requires a key, load it via environment / secret
  manager (EU/CH region) as `pydantic.SecretStr` — never hardcode.

## Supply-chain & install trust (SEC-008)

- Pure-Python package built with `hatchling`; **no** `pre/postinstall` hooks and
  no dynamic code download at install time.
- The full install command is shown transparently in the README; the build is
  reproducible and described in `CONTRIBUTING.md`.
- Dependencies are pinned (`mcp[cli]>=1.2.0,<2.0.0`) and updated via Dependabot.
- Releases publish to PyPI via an OIDC **Trusted Publisher** (`publish.yml`) — no
  long-lived API token in repository secrets.
