# bench/

Single-process latency + storage benchmarks for `claude-webcache`. Uses the same Node runtime + `node:sqlite` driver the plugin ships with — numbers reflect what real users see.

## Run

```bash
npm run bench                          # default N=10000, M=10000
node bench/run.js --n=5000             # smaller run
node bench/run.js --label=after-hw     # tag the result file
```

## What it measures

| Phase | What | How |
|---|---|---|
| `write` | `cache.set()` × N synthetic rows | populated `url=https://example.com/page/<i>`, `output` = N-byte payload (default 1KB) |
| `read_hit` | `cache.get()` × M, all keys exist | random index into populated set |
| `read_miss` | `cache.get()` × K on non-existent keys | exercises the `WHERE key = ?` index miss path |
| `list_50` | `cache.list(50)` × K | `ORDER BY cached_at DESC LIMIT 50` over populated DB |
| `storage` | `db_bytes`, `wal_bytes`, `bytes_per_entry` | `fs.statSync` after populate phase |

Each phase reports `p50/p95/p99 ms` and `ops/sec`.

## Expected numbers (reference)

On commodity hardware (modern CPU, NVMe SSD), at `N=10000`:

- `read_hit` p50 < 5ms — typical SQLite indexed point query
- `read_miss` p50 < 5ms — same path, just no row
- `write` p50 < 5ms — WAL append, `synchronous=NORMAL`
- `list_50` p50 < 1ms — in-memory after first call
- `bytes_per_entry` ≈ 1100-1300B for default 1KB output (overhead = key + url + prompt_hash + indexes)

If `read_hit` p50 > 50ms, suspect: cold disk cache, missing WAL pragma, antivirus interference (Windows Defender on `~/.webcache`), or HDD instead of SSD.

## Output

Each run writes `bench/results/<date>-<label>-<commit>.json` with full metadata (CPU model, RAM, OS, Node version, git commit). `bench/results/` is gitignored — those files are ephemeral local runs.

**Canonical baselines** that are committed to the repo live in `bench/baselines/`. Use them as fixed reference points for before/after comparisons (hardware swaps, perf regressions). Add a new baseline manually when you want to lock in a measurement that future runs should compare against.

## Caveats

- **Single process, single thread.** Real Claude Code workload is single-process too, so this matches.
- **Synthetic URL distribution.** Hit-rate from real workloads (repeated docs/arxiv URLs across sprints) is workload-dependent — see Phase B replay harness when it ships.
- **Not run in CI.** Shared GitHub runners produce flaky perf numbers. Run locally, commit baseline JSON.
