# Contributing

## Setup

```bash
git clone https://github.com/theYahia/claude-webcache.git
cd claude-webcache
npm install
```

Requires Node.js 22.5+ (uses built-in `node:sqlite` — no native deps).

## Local plugin install

To test the full plugin flow in Claude Code, install from your local clone:

```
claude --plugin-dir ./plugin
```

Or via marketplace:
```
/plugin install file:///absolute/path/to/claude-webcache
```

Restart the session, then run `/mcp` — you should see `claude-webcache` listed with 8 tools.

## Testing

Three test files run via Node's built-in test runner (`node:test`), ~53 tests, ~7s total:

```bash
npm test                  # all three test files
npm test --watch          # re-run on file change
```

| File | What it covers | Style |
|---|---|---|
| `plugin/test/cache.test.js` | 38 unit tests against `cache.js` directly — canonicalization, validation, redaction, payload cap, namespace isolation, gzip, busy_timeout, statsByDomain, pagination, BC | Sync; uses `freshCache()` helper which monkey-patches `os.homedir()` + env vars for isolation |
| `plugin/test/integration.test.js` | 11 tests spawning `mcp-server.cjs` as a child process — full JSON-RPC stdio round-trip on all 8 MCP tools | Async; `child_process.spawn` + manual JSON-RPC framing |
| `plugin/test/concurrent.test.js` | 4 stress tests with 5-10 parallel Node workers writing/reading the same DB | Async; `child_process.spawn` to `concurrent-worker.cjs`; validates `busy_timeout`, schema-migration race, eviction + writers coexist |

When adding tests:
- For new cache features → extend `cache.test.js` (use `freshCache({ namespace: 'x', compress: true, ... })` to inject env). If you add a new env var to `cache.js`, also add it to `ENV_KEYS` in `plugin/test/helpers.js` so tests don't leak state.
- For new MCP tools → extend `integration.test.js` so the tool is exercised end-to-end through stdio JSON-RPC.
- For changes affecting concurrency or schema → extend `concurrent.test.js`.

## Benchmarks

```bash
npm run bench
```

Writes results to `bench/results/<date>-<commit>.json` with full machine metadata. Compare against `bench/baselines/` after any change touching `cache.js`. If perf regresses >10% on a hot path (write/read_hit/list_50), investigate before merging.

## Manual E2E

The manual checklist in [E2E_TEST.md](E2E_TEST.md) covers the install + hook + dashboard happy path. Run it before each release.

## Release flow

See [MIGRATION.md](MIGRATION.md) for schema-migration notes per version. Release steps:

1. Bump version in `package.json`, `plugin/.claude-plugin/plugin.json`, `server.json`.
2. Sync lockfile: `npm install --package-lock-only --no-audit --no-fund`.
3. Update `CHANGELOG.md` with `Added` / `Changed` / `Schema` / `Tests` sections.
4. `npm test` — all green.
5. `npm run bench` — no regression on hot paths.
6. Commit + annotated tag (`git tag -a vX.Y.Z`) + push main + tag.
7. `npm publish` (manual user step — requires interactive 2FA OTP).
8. `mcp-publisher publish` to refresh Official MCP Registry listing.

## Opening a PR

1. Fork the repo and create a branch from `main`.
2. Make your change. Keep diffs focused — one logical change per PR.
3. `npm test` passes locally.
4. `npm run bench` shows no regression on hot paths.
5. Update `CHANGELOG.md` under an `## Unreleased` heading.
6. Open a PR — describe what and why.
