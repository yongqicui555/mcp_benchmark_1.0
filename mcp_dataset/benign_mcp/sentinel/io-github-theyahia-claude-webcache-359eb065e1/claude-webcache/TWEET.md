# Tweet drafts — claude-webcache

Pick one. All under 280 chars (X free-tier limit). Pair with a screenshot from E2E_TEST.md.

## Variant A — direct utility framing

```
Claude Code's built-in WebFetch caches results for 15 min, then they vanish.

Built claude-webcache: cross-session WebFetch persistence.
SQLite, unlimited TTL by default, MCP plugin.

Open a new session → past fetches are still there.

github.com/theYahia/claude-webcache
```

## Variant B — claude-mem analogy (works if your audience overlaps)

```
claude-mem persists conversation memory across Claude Code sessions.

claude-webcache does the same for WebFetch results.

Same URL + same prompt in any new session = instant cache hit.

MIT, MCP plugin, no native deps.

github.com/theYahia/claude-webcache
```

## Variant C — pain-first

```
If you do research sprints in Claude Code: you re-fetch the same docs across sessions all the time. The 15-min in-session cache evicts before your next sprint.

Built a tiny fix → claude-webcache. SQLite, unlimited TTL by default, ~200 lines.

github.com/theYahia/claude-webcache
```

## Rules

- Do **not** write "save 50% tokens", "10x faster", "mind-blowing" — no measurements, that's fabrication.
- Do **not** promise HN frontpage / mass adoption.
- You **may** mention `caveman` / `claude-mem` if your followers are familiar with them.
- **Image alt-text:** "Two Claude Code sessions side by side. Left: WebFetch + cache_store. Right: new session, cached_fetch returns instantly."

## Optional cross-promo with qsearch

In a **first reply** to your own tweet:

```
Same author behind qsearch (multi-engine search aggregation for Claude Code).
v0.4 ships next week. github.com/theYahia/qsearch
```

Not in the main tweet — funnel in the reply, don't dilute the webcache message.

## After posting

- Watch star yield over the first 24-48 hours.
- If it goes harder than expected (>500 stars day one) → speed up npm publish + MCP Registry submission.
- If it's quiet — review the cause (visual? copy? wrong audience timing?).
