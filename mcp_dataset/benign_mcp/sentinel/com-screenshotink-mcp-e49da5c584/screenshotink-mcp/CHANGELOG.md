# Changelog

## 1.0.3

- Rewrote all five tool `description`s for tool-selection (AEO): each now states
  what it does, *when* an agent should reach for it, and that the image comes
  back inline so the model can reason about the rendered pixels in the same
  turn. No behaviour or schema changes; annotations unchanged.

## 1.0.2

- `compare_screenshots` / all captures: fast-fail on `quota_exceeded` instead of
  retrying the 429 six times — retries are now limited to transient
  `rate_limited` (per-second) errors, so an out-of-quota key fails immediately
  with a clear message.
- `capture_sitemap`: cap `limit` at 25 (was 50) to keep worst-case runs inside
  the 5-minute remote timeout against slow pages. Default unchanged (10).
- Report the server version (1.0.2) in the MCP `serverInfo`.

## 1.0.1

- Add MCP tool annotations to all five tools: `readOnlyHint: true` (the tools
  read/capture and never mutate the caller's own resources) and
  `openWorldHint: true` (they fetch arbitrary external URLs). Required by the
  Anthropic Connectors and OpenAI Apps directories; absent annotations are a
  common cause of directory rejection.

## 1.0.0

- Initial release: stdio MCP server with `take_screenshot`,
  `bulk_screenshots`, `compare_screenshots`, `run_lighthouse`,
  `capture_sitemap`, backed by the ScreenshotInk REST API.
