# Changelog

All notable changes to `hn-tech-signal-mcp` will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.1] — 2026-05-12

First successful PyPI publish after the 2026-05-12 audit. Contents are the same as the `v0.2.0` GitHub release tag; the `v0.2.0` PyPI upload failed because `version` in `pyproject.toml` and `__init__.py` was not bumped, so the build produced `0.1.0` artefacts that PyPI rejected with `400 File already exists`. This release re-publishes the audit-closure baseline under the correct version.

### Security
- **SEC-001:** `GITHUB_TOKEN` is now only attached to requests targeting `api.github.com`. Previously, the token was sent as `Authorization: Bearer` to **all** upstream APIs (HackerNews, Algolia, arXiv, Lobste.rs) due to a shared header builder, leaking the credential to third-party hosts.
- **SEC-002:** The `streamable_http` transport now defaults to binding `127.0.0.1`. Non-loopback values for `MCP_HOST` require `MCP_BEARER_TOKEN` to be set; otherwise the server refuses to start. Prevents accidental public exposure of the unauthenticated HTTP endpoint.
- **SEC-003:** arXiv XML responses are now parsed with `defusedxml` instead of `xml.etree.ElementTree`. Mitigates XXE and billion-laughs class of XML attacks.
- **SEC-004:** `arxiv_search.category` is now validated against the same `ARXIV_AI_CATEGORIES` whitelist as `arxiv_latest.categories`. Empty string normalises to `None`.

### Changed
- **ARCH-001:** Replaced the stale `fastmcp>=2.0.0` dependency with `mcp>=1.2.0` — the actually imported package. Added `defusedxml>=0.7.1` as a direct dependency.
- **SDK-001:** Replaced six occurrences of deprecated `datetime.utcnow()` with a timezone-aware `_now_iso()` helper. Removes `DeprecationWarning` noise on Python 3.12+.
- **SDK-002:** Renamed the module-level FastMCP instance from `mcp` to `server` to stop shadowing the `mcp` SDK package import.
- **SCALE-001:** The in-memory TTL cache is now an `OrderedDict` with LRU eviction at `_CACHE_MAX_ENTRIES = 512` entries. Prevents unbounded memory growth in long-running `streamable_http` mode.
- **OBS-001:** Activated the previously-declared `hn-tech-signal-mcp` logger. `_handle_error` emits a `WARNING` per upstream failure, individual HN item fetch failures are logged at `DEBUG`, and `main()` initialises `logging.basicConfig` (controlled by `LOG_LEVEL`, default `INFO`).
- Long error and cache-key strings reformatted for the new `ruff format` gate.

### Added
- `MCP_HOST` environment variable (default `127.0.0.1`).
- `MCP_BEARER_TOKEN` environment variable (required for public bind).
- `LOG_LEVEL` environment variable (default `INFO`).
- `SECURITY.md` describing the vulnerability reporting process.
- `.github/dependabot.yml` for weekly pip and monthly github-actions updates.
- `.github/CODEOWNERS` for review routing.
- CI now runs `ruff check`, `ruff format --check` and `pytest --cov` with a 45 % floor.
- Regression tests for all 11 audit findings in `tests/test_server.py` (30 unit tests total).

### Fixed
- Bumped `version` to `0.2.1` in `pyproject.toml`, `src/hn_tech_signal_mcp/__init__.py` and the version assertion in `tests/test_server.py`. Root cause of the v0.2.0 PyPI failure.

## [0.1.0] — 2026-03-22

### Added
- `hn_top_stories` — HackerNews top/best/new/ask/show/job stories with optional AI keyword filter
- `hn_search` — HackerNews full-text search via Algolia (full history, date range filter)
- `arxiv_latest` — Latest arXiv papers by category (cs.AI, cs.LG, cs.CL, cs.CV, cs.RO, stat.ML)
- `arxiv_search` — arXiv paper search by keyword, title (`ti:`), author (`au:`), abstract (`abs:`)
- `lobsters_hot` — Lobste.rs hottest stories with tag filter
- `github_trending_ai` — GitHub repository search by topic, stars, sort order
- `tech_signal_digest` — Aggregated cross-source Markdown briefing (anchor demo tool)
- Dual transport: stdio (Claude Desktop) + Streamable HTTP (cloud/Render.com)
- Optional `GITHUB_TOKEN` support for higher GitHub rate limits
- 21 unit tests + 5 live integration tests
- README.md (English) + README.de.md (German / Schweizer Rechtschreibung)
- CONTRIBUTING.md
