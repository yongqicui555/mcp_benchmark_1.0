# E2E test — step by step

Goal: verify cache hit really fires across two Claude Code sessions, and capture 1-2 screenshots for the launch tweet.

## 1. Register MCP server + hook

Open `~/.claude/settings.json` (create if missing) and **merge** this JSON with your existing settings:

```json
{
  "mcpServers": {
    "claude-webcache": {
      "command": "node",
      "args": ["/absolute/path/to/claude-webcache/scripts/mcp-server.cjs"]
    }
  },
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup|clear|compact",
        "hooks": [
          { "type": "command", "command": "node /absolute/path/to/claude-webcache/scripts/hook-stats.cjs" }
        ]
      }
    ]
  }
}
```

⚠️ If you already have `mcpServers` or `hooks` blocks — add the new keys inside, do not overwrite the whole object.

## 2. Restart Claude Code

Close all sessions and start a fresh one (`claude` in terminal or via the app).

## 3. Verify MCP connected

In the new session, run:

```
/mcp
```

Should list `claude-webcache`. If not, check `claude --debug` logs.

## 4. Test A — CACHE_MISS flow (first session)

Tell Claude:

> Use the `cached_fetch` MCP tool with url=`https://example.com` and prompt=`extract the page title`. If it returns `[CACHE_MISS]`, call WebFetch with the same arguments, then call `cache_store` with url, prompt, and the WebFetch result.

Expected flow:
1. `cached_fetch` → `[CACHE_MISS] https://example.com`
2. `WebFetch(https://example.com, "extract the page title")` → "Example Domain"
3. `cache_store(url, prompt, "Example Domain")` → `stored`

📸 **Screenshot this flow** — all three tool calls visible.

## 5. Test B — HIT flow (second session)

Close the session fully, start a new one (the SessionStart hook needs to fire).

A system line should appear:

```
webcache: 1 pages cached, 0 hits, last fetch ~1m ago
```

Tell Claude:

> Use `cached_fetch` with url=`https://example.com` and prompt=`extract the page title`.

Expected flow:
1. `cached_fetch` → `Example Domain` (instant, no WebFetch call)

📸 **Screenshot this** — visible: hook stats line at top, instant hit, no WebFetch call.

## 6. Verification checklist

- [ ] `/mcp` shows `claude-webcache`
- [ ] CACHE_MISS returned in first session
- [ ] `cache_store` accepted output without error
- [ ] SessionStart hook printed stats line in second session
- [ ] HIT returned cached text without calling WebFetch
- [ ] Hit was actually fast (<1 second)

## 6b. Test C — invalidation + clear (v0.3.0+)

After Test B, exercise the v0.3.0 admin tools:

> Call `cache_invalidate` with url=`https://example.com`. Then call `cached_fetch` with the same url+prompt — it should return `[CACHE_MISS]`.

Expected:
1. `cache_invalidate({ url: "https://example.com" })` → `{ deleted: 1 }`
2. `cached_fetch(...)` → `[CACHE_MISS] https://example.com`

> Now seed two URLs and run `cache_clear` with `older_than_days: 0.0001`. Then call `cache_stats` — `total` should be 0.

Expected: `cache_clear` returns `{ deleted: N }` matching seed count. Subsequent `cache_stats` shows `total: 0`, but `hits` and `misses` counters survive (they live in the separate `meta` table).

> Verify safety: call `cache_clear` with NO arguments — it should error.

Expected: error message about needing `confirm:"YES"` for full wipe.

## 6c. Test D — CLI dashboard (v0.3.0+)

In a terminal (outside Claude Code):

```bash
claude-webcache stats           # JSON dump
claude-webcache list 10         # 10 most-recent URLs
claude-webcache dashboard --port 37789
```

Open `http://localhost:37789/` in a browser. Expected: stats cards (entries, hits, misses, hit rate, db size, evicted, last write), top URLs table, top domains table, recent entries with invalidate buttons. Type a substring in the search box → entries filter.

Click an invalidate × button → confirm dialog → row disappears after reload.

## 7. Troubleshooting

| Symptom | Where to look |
|---|---|
| `/mcp` doesn't see claude-webcache | Wrong path in `args` → check `scripts/mcp-server.cjs` exists at the path |
| `cached_fetch` returns undefined / error | Run `node scripts/mcp-server.cjs` manually — should hang on stdin |
| Hook doesn't print stats | Run `node scripts/hook-stats.cjs` manually — should output JSON |
| ExperimentalWarning in logs | This is `node:sqlite` — should be suppressed by `process.removeAllListeners('warning')` first line in both cjs files |

## After successful test

- Save both screenshots to `docs/screenshots/` (create the folder)
- Move on to `TWEET.md` for the launch copy
