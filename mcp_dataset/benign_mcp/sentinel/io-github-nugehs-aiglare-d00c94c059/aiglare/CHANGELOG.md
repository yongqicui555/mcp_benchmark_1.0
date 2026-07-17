# Changelog

All notable changes to aiglare are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/), and versions follow
[Semantic Versioning](https://semver.org/). Bump the version in `package.json`
and `package-lock.json` together — `npm run version:check` enforces that they
match before publish.

## [0.3.0] - 2026-06-13

### Added

- **Compliance framework mapping** — `--compliance soc2,eu-ai-act,nist,owasp` (or `all`)
  maps every AI surface to the specific controls it violates across four frameworks:
  - SOC 2 Trust Services Criteria (CC7.2, CC7.4, CC9.1, A1.2, PI1.2, PI1.3)
  - EU AI Act (Art. 9, 13, 14, 17)
  - NIST AI RMF (GOVERN-1.2, MAP-2.3, MEASURE-2.5, MEASURE-2.6, MANAGE-1.3, MANAGE-2.2)
  - OWASP LLM Top 10 (LLM02, LLM04, LLM08, LLM09)
- **`--format` flag** — choose output format:
  - `terminal` (default) — existing coloured terminal report, now with compliance summary footer
  - `lint` — ESLint-style output (`file:line  error  message  framework/control-id`), works with or without `--compliance`; without it, uses guardrail-based rule IDs
  - `markdown` — evidence artifact with per-framework control tables ready to hand to an auditor
  - `html` — branded HTML report with sticky nav, collapsible framework sections, colour-coded control cards, severity pills, and a guardrail matrix table
  - `json` — existing machine-readable output, now includes `compliance` and `violations[]` on each surface
- **Multi-path scanning** — pass multiple paths to produce a single combined report:
  `aiglare ./api ./web --compliance all --format html`
- **MCP**: `ai_surface_audit` now accepts an optional `compliance` array; each surface in the response includes a `violations[]` array when set.
- 19 new tests covering `mapViolations`, `parseFrameworks`, `buildComplianceSummary`, `renderLint`, `renderMarkdown`, and the `runAudit` compliance integration.

### Changed

- `--json` is now an alias for `--format json` (fully backwards-compatible).

## [0.2.3] - 2026-06-10

### Added

- README: demo GIF showing a `--ci` scan of a failing fixture.
- `version` lifecycle hook: `npm version` now syncs `server.json` (MCP registry
  manifest) with `package.json` automatically.
- `version:check` now fails when `server.json` is out of sync.

### Changed

- README badges use semantic colors (blue for info, green for positive) instead
  of brand red, which read as failures on npm.

### Note

- 0.2.2 was published to npm but its MCP Registry publish failed because
  `server.json` still said 0.2.1. 0.2.3 republishes both in sync.

## [0.2.1] - 2026-06-09
### Added
- CommonJS detection: `require('pkg')` in every position (plain
  `const X = require(...)`, destructured `const { X } = require(...)`, member
  access `require('pkg').X`, bare expression) and dynamic `import('pkg')` now
  resolve through the same provider-package registry as ESM imports. CommonJS
  codebases (e.g. LibreChat's `api/`, anything-llm's `server/`) were
  previously invisible to the scanner.
- `.cjs` files are scanned (`.test.cjs` / `.spec.cjs` remain excluded).
- Registry: Groq (`groq-sdk` + `api.groq.com`), `@google/genai`, and the
  official `@ai-sdk/*` provider packages (google, mistral, groq, xai, cohere,
  amazon-bedrock, azure, deepseek, perplexity) under the Vercel AI SDK entry.

### Fixed
- `require('@aws-sdk/client-bedrock-runtime')` was only detected by accident:
  the host matcher substring-matched `bedrock-runtime` inside the require
  string. require/`import()` specifiers now match by package — intentionally —
  and are excluded from host matching, so SDK wiring files that never call the
  model are no longer reported as surfaces.

## [0.2.0] - 2026-06-09
### Changed
- `PILOT.md` rewritten as a generic runbook (`./my-api`, `./my-app` examples)
  — removed machine-specific paths and private project references.

### Added
- Brand alignment: toolchain footer/badges.
- `aiglare mcp` — stdio MCP server (hand-rolled JSON-RPC, no SDK dependency)
  exposing `ai_surface_audit`, `ai_surface_gate`, and `list_providers`.
- `scripts/check-version.js` (`npm run version:check`) — SemVer + lockfile
  alignment guard, wired into CI.
- npm publish readiness: scoped `@nugehs/aiglare`, `files` whitelist,
  `publishConfig.access = public`, `mcpName`.
- Tag-triggered release workflow (`.github/workflows/release.yml`): pushing a
  `vX.Y.Z` tag runs the quality gate, publishes to npm with OIDC provenance,
  creates a GitHub Release with notes extracted from this changelog, and
  publishes `server.json` to the MCP Registry.
- README polish: badge row (npm, CI, license, Node), prominent link to the
  live site (https://nugehs.github.io/aiglare-web/), an "aiglare vs
  alternatives" comparison, and a "Run a 1-week pilot" section linking
  `PILOT.md`.

## [0.1.0]

### Added
- Initial release: static linter that finds where LLM/AI output reaches a user
  or a side-effect (payment, booking, email, db/fs write, shell) and scores each
  surface on five governance guardrails.
- Provider-agnostic registry (OpenAI, Anthropic, Google, Cohere, Mistral,
  Replicate, Vercel AI SDK, LangChain, Ollama, Bedrock, Cloudflare Workers AI,
  Hugging Face + raw fetch/axios hosts).
- Sink classification (user-facing / side-effectful / internal) and a narrow CI
  gate that fails only on red + side-effectful surfaces.
- Optional repoctx index acceleration, including human-in-loop re-evaluation
  after an index-driven sink promotion.
