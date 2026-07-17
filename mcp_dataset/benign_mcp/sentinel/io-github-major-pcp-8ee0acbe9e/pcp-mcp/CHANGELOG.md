# Changelog

All notable changes to this project will be documented in this file.

This project uses [Semantic Versioning](https://semver.org/) and [Conventional Commits](https://www.conventionalcommits.org/).

## v1.5.1 (2026-03-26)

### Fix

- **tests**: sort conftest.py imports after removing dead fixture
- **tests**: add type narrowing for structured_content in metric tool tests

### Refactor

- update tools docs to actual patterns, remove dead fixture

## v1.5.0 (2026-02-05)

### Feat

- add Fedora packaging with Packit automation

## v1.4.0 (2026-02-04)

### Feat

- **tools**: migrate system tools to ToolResult with timeout
- **tools**: migrate query_metrics and search_metrics to ToolResult
- **tools**: migrate describe_metric to ToolResult with timeout

### Fix

- resolve class identity issue with module reload in tests
- **tests**: use mock lifespan in smoke tests for CI

### Refactor

- **server**: use FileSystemProvider for tool/prompt discovery
- **prompts**: migrate prompts to standalone @prompt decorator
- **tools**: migrate system.py to standalone @tool decorator
- **tools**: migrate metrics.py to standalone @tool decorator

## v1.3.2 (2026-02-04)

### Refactor

- **server**: remove resources module

## v1.3.1 (2026-01-27)

### Fix

- update deps

## v1.3.0 (2026-01-20)

### Feat

- **tools**: add get_filesystem_usage tool

## v1.2.0 (2026-01-19)

### Feat

- **ci**: add automated MCP Registry publishing

## v1.1.0 (2026-01-19)

### Feat

- add MCP registry support

### Fix

- **ci**: use cz directly after uv tool install

## v1.0.3 (2026-01-19)

### Fix

- make smoke tests work without pmproxy connection
- use quoted forward reference for FastMCP type hint
- remove future annotations import for Python 3.14 compatibility

## v1.0.2 (2026-01-19)

### Fix

- wrap list returns in object types for MCP spec compliance

## v1.0.1 (2026-01-19)

### Bug Fixes

- Add type assertions to narrow context types for ty check
  ([`3ddcc27`](https://github.com/major/pcp-mcp/commit/3ddcc27b14007b43fa4aa78f3042839932ffdb69))

- Disable build in semantic-release, use pypi job instead
  ([`5f6d978`](https://github.com/major/pcp-mcp/commit/5f6d9781e7db6a160ef8aa79ebbb822438e58b4e))

- Remove 'from __future__ import annotations' from tools modules
  ([`e8d90c6`](https://github.com/major/pcp-mcp/commit/e8d90c65661b85a0ea5e6319a45cfa6327668f0f))

- **ci**: Pass CODECOV_TOKEN to codecov action
  ([`7013aaf`](https://github.com/major/pcp-mcp/commit/7013aaf4d13433bc2b244ea4d689397f8744a9cb))

- **security**: Add host allowlist to prevent SSRF via host parameter
  ([#12](https://github.com/major/pcp-mcp/pull/12),
  [`7dc11d2`](https://github.com/major/pcp-mcp/commit/7dc11d294e243da15e472856e0624bff30756032))

- **tools**: Resolve Pydantic annotation evaluation error
  ([`1b1615d`](https://github.com/major/pcp-mcp/commit/1b1615d473d869236db1a84ddb94a9c34d52a121))

### Features

- Add audit logging middleware for MCP requests ([#14](https://github.com/major/pcp-mcp/pull/14),
  [`8199e7e`](https://github.com/major/pcp-mcp/commit/8199e7e1e98f50a4b2f7b788f50c6cc69cf14bc1))

- Add automated semantic versioning and PEP 561 typed package support
  ([`4093790`](https://github.com/major/pcp-mcp/commit/40937908e25908432f1fe43ce00ee056d260c95d))

- Add caching middleware for metric metadata tools ([#17](https://github.com/major/pcp-mcp/pull/17),
  [`22f35a2`](https://github.com/major/pcp-mcp/commit/22f35a2cc5c44a51283b25f0bf900a2b13b9fa1f))

- Add FastMCP 2.0 features (icons, caching, sampling)
  ([#17](https://github.com/major/pcp-mcp/pull/17),
  [`22f35a2`](https://github.com/major/pcp-mcp/commit/22f35a2cc5c44a51283b25f0bf900a2b13b9fa1f))

- Add FastMCP progress reporting and resource templates
  ([#15](https://github.com/major/pcp-mcp/pull/15),
  [`30a0c72`](https://github.com/major/pcp-mcp/commit/30a0c72b4d15fa3c52eb9ba669ccb68f1cdad3da))

- Add icons and tags to MCP tools, resources, and prompts
  ([#17](https://github.com/major/pcp-mcp/pull/17),
  [`22f35a2`](https://github.com/major/pcp-mcp/commit/22f35a2cc5c44a51283b25f0bf900a2b13b9fa1f))

- Add MCP tool annotations for read-only and open-world hints
  ([#16](https://github.com/major/pcp-mcp/pull/16),
  [`441401f`](https://github.com/major/pcp-mcp/commit/441401fb95675a20cdb9eb27cfe7d9246978ce7d))

- Add MCP tool annotations, structured logging, and output schemas
  ([#16](https://github.com/major/pcp-mcp/pull/16),
  [`441401f`](https://github.com/major/pcp-mcp/commit/441401fb95675a20cdb9eb27cfe7d9246978ce7d))

- Add output schemas to MCP tools for LLM introspection
  ([#16](https://github.com/major/pcp-mcp/pull/16),
  [`441401f`](https://github.com/major/pcp-mcp/commit/441401fb95675a20cdb9eb27cfe7d9246978ce7d))

- Add progress reporting to system tools ([#15](https://github.com/major/pcp-mcp/pull/15),
  [`30a0c72`](https://github.com/major/pcp-mcp/commit/30a0c72b4d15fa3c52eb9ba669ccb68f1cdad3da))

- Add quick_health tool for fast CPU/memory checks ([#17](https://github.com/major/pcp-mcp/pull/17),
  [`22f35a2`](https://github.com/major/pcp-mcp/commit/22f35a2cc5c44a51283b25f0bf900a2b13b9fa1f))

- Add resource templates for per-host health and metric info
  ([#15](https://github.com/major/pcp-mcp/pull/15),
  [`30a0c72`](https://github.com/major/pcp-mcp/commit/30a0c72b4d15fa3c52eb9ba669ccb68f1cdad3da))

- Add smart_diagnose tool with LLM sampling ([#17](https://github.com/major/pcp-mcp/pull/17),
  [`22f35a2`](https://github.com/major/pcp-mcp/commit/22f35a2cc5c44a51283b25f0bf900a2b13b9fa1f))

- Upgrade to StructuredLoggingMiddleware for better observability
  ([#16](https://github.com/major/pcp-mcp/pull/16),
  [`441401f`](https://github.com/major/pcp-mcp/commit/441401fb95675a20cdb9eb27cfe7d9246978ce7d))

- **context**: Add get_client_for_host async context manager
  ([`17c46a3`](https://github.com/major/pcp-mcp/commit/17c46a3e07d9b33b7b9971fea0868aae79e764d8))

- **security**: Add TLS verification configuration options
  ([#13](https://github.com/major/pcp-mcp/pull/13),
  [`1c8a307`](https://github.com/major/pcp-mcp/commit/1c8a307b9f744c0dd9d1f2114ab286dc2c5fcfdf))

- **tools**: Add host param to metric tools
  ([`fff887d`](https://github.com/major/pcp-mcp/commit/fff887d307ca7cf052a97c08ab7d87e9db0817d3))

- **tools**: Add host param to system tools
  ([`dc077a2`](https://github.com/major/pcp-mcp/commit/dc077a2ae542b421b3950076395fc62d5326960d))


## v0.1.0 (2026-01-18)

### Feat

- add guided diagnostic prompts for common troubleshooting workflows
- add browsable catalogs for common metrics and namespaces
- add comprehensive LLM guidance to MCP server instructions
- add MCP resources for health and metric discovery
- add clumped system tools (snapshot, process top)
- add fetch_with_rates for counter metric rate calculation
- add snapshot and process response models
- add core metric tools (query, search, describe)
- add tools and resources registration stubs
- add core MCP server framework
- add project configuration and build setup

### Fix

- **docs**: correct module references in API docs
- use Python 3.10 compatible imports for Self and UTC
- add future annotations for Python <3.14 compatibility
- calculate actual memory usage excluding cache/buffers
- handle both float and dict timestamp formats
- use integer keys for load metric instances
- convert instance IDs to strings in query_metrics
- handle pmproxy context expiration with auto-retry
