# Changelog

All notable changes to the MigratorXpress MCP Server will be documented in this file.

## [0.1.4] - 2026-02-27

### Added
- Rich descriptions for all properties in MCP tool schemas (helps LLMs provide correct parameters)
- Version compatibility check infrastructure in `preview_command` output

## [0.1.3] - 2026-02-24

### Added
- PyPI, License, and MCP Registry badges in README
- GitHub Actions workflow for automated PyPI publishing on release
- Missing environment variables (`MIGRATORXPRESS_LOG_DIR`, `LOG_LEVEL`) in server.json
- GitHub repository topics for MCP Registry discoverability

### Fixed
- Timeout default in server.json (corrected from 1800 to 3600 to match actual code)
- Documentation URL in pyproject.toml

## [0.1.1] - 2026-02-23

### Added

- `server.json` MCP Registry configuration file with package metadata, transport settings, and environment variable definitions

### Changed

- GitHub repository URL updated from `aetperf/migratorxpress-mcp` to `arpe-io/migratorxpress-mcp` in `pyproject.toml`

## [0.1.0] - 2025-02-20

### Added

- Initial release of MigratorXpress MCP Server
- 6 MCP tools: preview_command, execute_command, validate_auth_file, list_capabilities, suggest_workflow, get_version
- Support for MigratorXpress v0.6.24
- Source databases: Oracle, PostgreSQL, SQL Server, Netezza
- Target databases: PostgreSQL, SQL Server
- Migration tasks: translate, create, transfer, diff, copy_pk, copy_ak, copy_fk, all
- License key masking in command display
- Version detection and capabilities registry
- Comprehensive test suite
