# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2026-04-27

### Added

- `mcp-name: io.github.andrewmpierce/youfiliate-mcp` marker in README for MCP Registry ownership verification.
- `server.json` describing both the PyPI/stdio package and the hosted streamable-HTTP remote.
- `smithery.yaml` for [Smithery](https://smithery.ai) auto-indexing.

## [0.1.0] - 2026-04-27

### Added

- Initial public release of the Youfiliate MCP server.
- 18 tools across 5 categories: smart link CRUD, analytics, preferences, YouTube OAuth, and migrations.
- 4 resources: `youfiliate://summary`, `youfiliate://preferences`, `youfiliate://smart-link/{id}`, `youfiliate://plan-limits`.
- Stdio transport for local Claude Desktop use.
- Streamable HTTP transport for remote/hosted deployments.
- Bearer-token auth via Youfiliate API keys (`youfiliate_sk_...`).
- Rate limiting (60 req/min per API key).
- Dockerfile for containerised HTTP deployments.
