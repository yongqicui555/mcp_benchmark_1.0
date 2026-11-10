#!/usr/bin/env bash
# openclaw-jsonl-shim.sh
#
# Wraps a cron job command and emits a JSONL run record on completion to
# the configured cron-runs directory. Use when your scheduler doesn't
# natively emit the JSONL format.
#
# Usage in crontab:
#   0 */1 * * * /path/to/openclaw-jsonl-shim.sh web-search-refresh /path/to/your-job-script.sh
#
# Env vars:
#   SILENTWATCH_OPENCLAW_LOGS — directory to write *.jsonl files (default ~/.openclaw/cron-runs)
#
set -euo pipefail

JOB_ID="${1:?usage: openclaw-jsonl-shim.sh <job_id> <command...>}"
shift

LOGS_DIR="${SILENTWATCH_OPENCLAW_LOGS:-$HOME/.openclaw/cron-runs}"
mkdir -p "$LOGS_DIR"
LOG_FILE="$LOGS_DIR/${JOB_ID}.jsonl"

RUN_ID="run-$(date -u +%Y%m%d%H%M%S)-$$"
STARTED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
START_EPOCH_MS="$(date +%s%3N)"

# Capture stdout + stderr for the run record while still writing them through
TMP_STDOUT="$(mktemp)"
TMP_STDERR="$(mktemp)"
trap 'rm -f "$TMP_STDOUT" "$TMP_STDERR"' EXIT

set +e
"$@" >"$TMP_STDOUT" 2>"$TMP_STDERR"
EXIT_CODE=$?
set -e

COMPLETED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
END_EPOCH_MS="$(date +%s%3N)"
DURATION_MS=$((END_EPOCH_MS - START_EPOCH_MS))

# Use jq if available for robust JSON; otherwise fall back to manual escaping
if command -v jq >/dev/null 2>&1; then
  jq -n \
    --arg run_id "$RUN_ID" \
    --arg job_id "$JOB_ID" \
    --arg started_at "$STARTED_AT" \
    --arg completed_at "$COMPLETED_AT" \
    --argjson duration_ms "$DURATION_MS" \
    --argjson exit_code "$EXIT_CODE" \
    --arg stdout "$(cat "$TMP_STDOUT")" \
    --arg stderr "$(cat "$TMP_STDERR")" \
    '{run_id:$run_id, job_id:$job_id, started_at:$started_at, completed_at:$completed_at, duration_ms:$duration_ms, exit_code:$exit_code, stdout:$stdout, stderr:$stderr}' \
    >> "$LOG_FILE"
else
  # Best-effort manual JSON escaping (jq is recommended for production)
  STDOUT_JSON="$(python3 -c 'import sys, json; print(json.dumps(sys.stdin.read()))' < "$TMP_STDOUT")"
  STDERR_JSON="$(python3 -c 'import sys, json; print(json.dumps(sys.stdin.read()))' < "$TMP_STDERR")"
  printf '{"run_id":"%s","job_id":"%s","started_at":"%s","completed_at":"%s","duration_ms":%d,"exit_code":%d,"stdout":%s,"stderr":%s}\n' \
    "$RUN_ID" "$JOB_ID" "$STARTED_AT" "$COMPLETED_AT" "$DURATION_MS" "$EXIT_CODE" "$STDOUT_JSON" "$STDERR_JSON" \
    >> "$LOG_FILE"
fi

# Forward the original outputs so the caller (cron, systemd) sees them
cat "$TMP_STDOUT"
cat "$TMP_STDERR" >&2

exit "$EXIT_CODE"
