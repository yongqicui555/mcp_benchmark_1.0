# Changelog

All notable changes to this project will be documented in this file.

## [0.3.3] - 2026-02-13

### Fixed

- **Timezone-aware datetime comparison** — RFM analysis now correctly handles timezone-aware datetimes from HubSpot API. Fixes `TypeError: can't compare offset-naive and offset-aware datetimes` when using live HubSpot data.

### Added

- **CI/CD workflows** — Automated testing on push/PR and PyPI publishing on version tags via GitHub Actions.
- **Smithery marketplace listing** — Fleshed out `smithery.yaml` with full metadata for Smithery marketplace discovery.

## [0.3.2] - 2026-02-13

### Fixed

- **Closed stage detection for custom labels** — Pipeline health now correctly identifies closed stages when HubSpot uses custom stage labels (e.g., "Closed - Won" vs "closedwon"). Matches on both internal IDs and display labels.

## [0.3.1] - 2026-02-13

### Fixed

- **Open deals filter** — Pipeline health scoring now uses HubSpot pipeline metadata (`isClosed` flag + label matching) to filter out closed deals instead of hardcoding stage names. Works correctly with any custom pipeline configuration.

## [0.3.0] - 2026-02-13

### Added

- **Signal Detection** (`detect_signals`) — 6-type signal taxonomy: velocity anomalies, conversion drop-offs, win/loss patterns, pipeline concentration, data quality issues, and SPICED frequency signals. Returns structured signal objects with strength scores (0-1), evidence, and recommended actions.
- **Constraint Analysis** (`identify_constraint`) — Identifies dominant scaling constraint (Lead Generation, Conversion, Delivery, Profitability) with Revenue Formula breakdown (Traffic × CR1 × CR2 × CR3 × ACV) and gap-to-benchmark analysis.
- **Value Engine Analysis** (`analyze_engine`) — Health scoring for Growth, Fulfillment, and Innovation engines with stage-specific metrics and integrated signal detection.
- **GTM Commit Drafting** (`propose_gtm_change`) — AI agents can propose structured GTM changes with intent, diff, impact surface, risk level, evidence, and measurement plans. Supports 8 entity types.
- **6 new methodology resources** — `value-engines`, `exit-criteria`, `constraints`, `signal-taxonomy`, `revenue-formula`, `gtm-commit-anatomy`.
- **Exit criteria testing** for `score_pipeline_health` — Pass/fail per criterion per deal.
- **Signal framing** for `run_rfm` — Win/loss pattern signals, revenue concentration detection.
- **Constraint context** for `qualify` — Maps prospect fit to dominant scaling constraint.
- **108 tests passing** (44 new + 64 existing).

### Changed

- Server now exposes **7 tools** (up from 3) and **11 methodology resources** (up from 4).
- README rewritten to reflect GTM Operating System positioning.

## [0.2.3] - 2026-02-10

### Added

- **Python installation method** — Added `python3 -m artefact_mcp` as recommended installation method for Claude Desktop (more reliable than `uvx` for sandboxed apps).
- **Comprehensive troubleshooting** — Added troubleshooting section for common issues (uvx PATH, HubSpot API key, import errors).

### Security

- **Dev bypass hardening** — License bypass for internal testing uses SHA-256 hash verification only (key not stored in source code).

## [0.2.2] - 2026-02-10

### Fixed

- **ICP incomplete score warning** — When qualifying a company by HubSpot ID only, the output now clearly warns that Behavioral and Strategic Fit scored 0 due to missing fields, lists the missing fields, and shows how to provide them alongside the company_id.
- **Scoring config discoverability** — ICP qualification results now include a `_scoring_note` hint about the `scoring_config` parameter when using default scoring. Server instructions also mention scoring customization.
- **Version/health resource** — New `server://version` resource returns server version, license tier, HubSpot connection status, and available tools/resources.
- **LemonSqueezy error clarity** — License validation errors now include a direct purchase link instead of a generic "does not belong to this product" message.

## [0.2.1] - 2026-02-10

### Fixed

- **Smart source defaults** — `run_rfm` and `score_pipeline_health` now default to `source="auto"`, which uses HubSpot if `HUBSPOT_API_KEY` is set, otherwise falls back to sample data. Free users no longer hit a license error on first use.
- **Realistic sample data** — Replaced toy company names ("Acme SaaS Inc.") with believable anonymized names ("Nextera Systems", "Precision Components Group"). Sample dates are now relative (always fresh) instead of hardcoded timestamps that go stale.
- **Actionable HubSpot error messages** — 401/403/429 errors now include step-by-step fix instructions (which scopes to enable, where to find Private Apps in HubSpot settings).
- **Sample data hint** — When results come from sample data, output includes a `_note` explaining how to connect live HubSpot data.

## [0.2.0] - 2026-02-10

### Added

- **ICP inline scoring overrides** — Pro users can now pass `scoring_config` to the `qualify` tool to customize scoring parameters per call: primary/adjacent/excluded industries, revenue range, employee range, primary/secondary geography. AI assistants translate natural language ICP descriptions into config automatically.
- **Pipeline stage auto-detection** — When using live HubSpot data, pipeline stages are now fetched from HubSpot's API instead of using hardcoded defaults. Works with any custom pipeline configuration.
- **`fetch_pipeline_stages()` HubSpot client method** — New method to retrieve pipeline stage definitions in display order.

### Changed

- `ICPScorer` now accepts optional `scoring_config` dict in constructor for parameter overrides.
- `_calculate_velocity()` and `_find_at_risk_deals()` accept optional stage order/labels for dynamic pipelines.
- `score_pipeline()` auto-detects stages when HubSpot client is available, falls back to defaults gracefully.

## [0.1.2] - 2026-02-10

### Fixed

- Fixed `mcp-name` case mismatch in README for Official MCP Registry validation.
- Added `.mcpregistry_*` to `.gitignore` to prevent token file leaks.

## [0.1.1] - 2026-02-10

### Added

- **Tool safety annotations** — All 3 tools now declare `readOnlyHint`, `destructiveHint`, `idempotentHint`, and `openWorldHint` per MCP spec. Required for Claude Desktop Extensions approval.
- **COMPARISON.md** — Detailed comparison vs HubSpot Official MCP, CData, Zapier, and generic wrappers.
- **ARCHITECTURE.md** — System diagram, data flow documentation, scoring engine reference.
- **CHANGELOG.md** — Release history.
- **GitHub Discussions** — Community engagement with seed topics.

## [0.1.0] - 2026-02-10

### Added

- **RFM Analysis tool** (`run_rfm`) — Scores clients on Recency, Frequency, and Monetary value. Segments into 11 categories. Extracts ICP patterns from top performers. Supports B2B service, SaaS, and manufacturing presets.
- **ICP Qualification tool** (`qualify`) — 14.5-point scoring model across Firmographic Fit (5 pts), Behavioral Fit (5 pts), and Strategic Fit (4.5 pts). Returns tier classification and engagement strategy.
- **Pipeline Health tool** (`score_pipeline_health`) — Calculates 0-100 health score with velocity metrics, stage-to-stage conversion rates, bottleneck identification, and at-risk deal detection.
- **4 methodology resources** — Scoring model, tier definitions, RFM segments, SPICED framework.
- **HubSpot integration** — Pull live CRM data for all 3 tools via HubSpot API v3.
- **Built-in sample data** — All tools work without an API key using `source="sample"`.
- **License gating** — Free tier (sample data), Pro ($149/mo), Enterprise ($499/mo) via LemonSqueezy.
- **4 industry presets** — Default, B2B Service, SaaS, Manufacturing (different RFM thresholds).
- **64 unit tests** — Full test coverage for all scoring engines, tools, and license module.
