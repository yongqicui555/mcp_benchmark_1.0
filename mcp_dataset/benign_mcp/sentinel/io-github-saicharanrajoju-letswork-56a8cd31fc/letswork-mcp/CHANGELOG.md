# Changelog

All notable changes to LetsWork are documented here.

## [2.1.1] - 2026-04-08

### Changed
- Added PyPI classifiers for improved search visibility
- Added project URLs (Homepage, Repository, Issues) to package metadata

## [2.1.0]

### Added
- Separate host and guest tokens — guest token printed in session info box
- Stdio proxy (`letswork-proxy`) for guest connections — bypasses Cloudflare SSE unreliability
- Chat window (`letswork/tui/chat_app.py`) — standalone Textual app, polls events every 1s
- Host shown in blue, guest shown in green in chat

### Fixed
- MCP connection reliability for remote guests via stdio proxy

## [2.0.0]

### Added
- `letswork start` — starts MCP server + Cloudflare tunnel, opens Claude Code + chat window
- `letswork join <URL> --token <TOKEN>` — guest joins session via stdio proxy
- File operations: `read_file`, `write_file`, `lock_file`, `unlock_file`
- Approval queue for guest file writes (`approve_change`, `reject_change`)
- Path traversal prevention via `safe_resolve()`
- 1MB file size limit and text-only enforcement
- 30-minute lock auto-expiry
- Event log for all file and session activity
