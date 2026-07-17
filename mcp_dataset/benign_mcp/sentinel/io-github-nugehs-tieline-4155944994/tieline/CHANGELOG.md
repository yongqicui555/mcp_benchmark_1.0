# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.4] - 2026-06-10

### Fixed

- MCP Registry publish: `server.json` description trimmed to the registry's
  100-character limit (the 0.1.3 registry publish was rejected on length;
  npm 0.1.3 itself shipped fine).

## [0.1.3] - 2026-06-10

### Added

- `tieline mcp` subcommand on the main bin (same server as `tieline-mcp`), so
  MCP clients can launch it via `npx @nugehs/tieline mcp`.
- MCP Registry manifest (`server.json`), `mcpName` in `package.json`, and a
  registry publish job in the release workflow — first MCP Registry release.
- `version` lifecycle hook keeps `server.json` in sync with `package.json`.
- README: demo GIF showing drift detection against the express example fixtures.

### Changed

- README badges use semantic colors instead of brand red.

## [0.1.1] - 2026-06-09
### Changed
- Genericized example configs and docs: `tieline.config.json` /
  `tieline.openapi.config.json` now point at `../my-frontend` / `../my-api`
  placeholders and the committed `examples/openapi-fixture/spec.json`; the
  `openapi` adapter doc comment and `.gitignore` no longer reference private
  project names.

### Added

- Brand alignment: toolchain footer/badges.
- README: "tieline vs alternatives" comparison table (Pact, openapi-diff, Optic,
  Schemathesis) explaining when to reach for which tool.
- Tag-triggered release workflow (`.github/workflows/release.yml`): runs the test
  suite, creates a GitHub Release with notes extracted from this changelog, then
  publishes to npm.
- This changelog.

## [0.1.0] - 2026-06-09

### Added

- Initial public release on npm as `@nugehs/tieline`.
- Static frontend↔backend contract-drift checker: client adapters (`rtk-query`,
  `axios-fetch`, `angular-http`) matched against server adapters (`nestjs`,
  `express`, `fastify`, `next`, `fastapi`, `flask`, `spring`, `openapi`).
- `tieline init`, `check`, `list`, `orphans`, and `doctor` commands; `--json`,
  `--html`, `--no-fail` flags.
- Self-contained HTML visual report with contract-flow diagram.
- Zero-dependency MCP server (`tieline-mcp`) exposing `tieline_check`,
  `tieline_list`, `tieline_orphans`, `tieline_doctor`, and `tieline_init`.
- 71 tests on Node's built-in runner; CI workflow on Node 20/22.
