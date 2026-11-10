# UploadCheck MCP Server

Thin MCP wrapper over the hosted UploadCheck API. It does not run quality checks locally.

Canonical naming:

- MCP server: `uploadcheck`
- CLI/package: `uploadcheck` or `uploadcheck-mcp`
- Tagline: Quality check videos, podcasts, and clips before you upload.

## Environment

```bash
export UPLOADCHECK_API_BASE_URL="https://api.uploadcheck.app"
export UPLOADCHECK_API_KEY="<workspace_api_key>"
```

## Agent Workflow

Use `/check` from Claude Code, Codex, or another slash-command capable workspace to quality check a media asset before upload.

```text
/check ./final-upload.mp4
```

Small and medium local files can be sent through Render without durable storage by base64-encoding the media and passing one of:

- `video_base64` with `video_content_type`
- `audio_base64` with `audio_content_type`
- `media_base64` with `media_content_type` and `media_kind`
- `data_url`

The API writes the payload to a temp file, runs the gate, and deletes the temp file after processing. Use signed URLs or future direct object storage for large files.

The agent should call `qc_run_local_file` for a reachable local export, or `qc_run_video` when it already has a YouTube URL, signed URL, upload id, or base64 payload. Then poll `qc_get_job`, fetch `qc_get_report`, and list timestamped evidence plus source-level issues it can reach.

Use `profile` when the caller knows the media type but does not need to hand-maintain every gate. Supported values are `auto`, `nto_long_form`, `generic_creator_video`, `shorts`, `audio`, `npo_podcast_or_audio`, and `thumbnail`. Explicit `checks` still win when supplied.

For Codex, Claude Code, Cursor, or NTO/NPO production pipelines, call `qc_get_pipeline_handoff` first when you need the complete production runbook. It gives the launch preflight, recipe, cost-basis, estimate, media-ingress, report, marker CSV, repair-loop, and rerun sequence. Then call `qc_get_pipeline_recipes` when you need the current default checks and sidecar arguments, and use `qc_run_local_file` for the selected profile.

For NPO podcast/audio projects, call `qc_get_npo_pipeline_handoff` or run `uploadcheck npo-pipeline-handoff --json` when you need the focused audio handoff without the broader NTO recipe bundle. It includes the cost preflight, default checks, transcript/watchlist/locked-script sidecars, inline/signed media-ingress rules, marker CSV handoff, "Fix now?" prompt, and rerun-before-publish-ready rule:

```json
{
  "file_path": "/path/to/final-upload.mp4",
  "profile": "nto_long_form",
  "manifest_path": "/path/to/storybook.json",
  "transcript_path": "/path/to/transcript.txt",
  "watchlist_path": "/path/to/watchlist.json",
  "expected_script_path": "/path/to/locked-script.txt",
  "sidecar_dir": "/path/to/_dialogue-chunks",
  "plan_id": "creator",
  "cost_guardrail": "downgrade"
}
```

Small files are base64 encoded by the local MCP process and evaluated through Render inline. Larger files use the signed-upload path automatically unless `upload_mode: "inline"` or `upload_mode: "signed"` is specified.

Hosted media ingress can be smoke-tested from the repo before handing the MCP to another production pipeline:

```bash
UPLOADCHECK_MEDIA_INGRESS_BASE_URL=https://api.uploadcheck.app UPLOADCHECK_API_KEY=<private_bearer> npm run media-ingress:verify
```

When a project has a storybook, edit decision list, or visual timeline JSON, pass it as `manifest_json` with `checks: "repeat_fatigue"`. UploadCheck will use it to flag exact visual reuse and source-family dominance even before a final render is reviewed.

When a project has transcript text or a script-sidecar, pass it as `transcript_text` or `transcript_json` with `checks: "spoken_leaks"`. UploadCheck will flag spoken URLs, markdown, prompt text, stage directions, vendor/tool names, and known wrong-name substitutions without running ASR.

For customer-specific terms, pass `watchlist_json` with `checks: "pronunciation_watchlist"` plus transcript text. Watchlist entries can include `terms: [{ expected, banned: [] }]` and top-level `banned: []`.

When a project has a locked narration script and final transcript, pass `expected_script_text` or `expected_script_json` plus transcript text with `checks: "script_faithfulness"`. UploadCheck compares word error rate model-free, so agents can catch narration drift without paying for full multimodal review.

When a project has local chunk QC reports, pass `sidecar_dir` with `checks: "chunk_sidecar_failures"`. The local MCP process packages JSON sidecars such as `*.garble-report.json`, Render evaluates them from memory/temp storage, and failed chunk reports become BLOCK flags before upload.

For queued Render worker jobs, do not use inline sidecar payloads because they are deleted after the create request. Use HTTPS sidecar URLs instead: `manifest_url`, `transcript_url`, `watchlist_url`, `expected_script_url`, and `chunk_sidecars_url`. UploadCheck fetches them only when the worker drains the job, stores them in temporary server storage for that run, and redacts the URLs from public job/report responses.

For thumbnail candidates, call `qc_run_local_file` on the image with `checks: "thumbnail_text_readability"`. The same inline Render path evaluates OCR contrast and edge/safe-area readability without model spend.

Use `qc_get_cost_basis` before pricing, plan, or model-backed review decisions. Use `plan_id`, `ai_review_seconds`, and `cost_guardrail` when an agent is asking for paid AI review beyond deterministic checks. The default guardrail is `downgrade`: margin-breaking AI review is removed and the job runs deterministic checks. Use `block` to reject unsafe requests, or `off` only for internal experiments/deep-review add-ons.

Checked minutes mean deterministic publish-readiness QC minutes. Deep model review stays internal for engine backtesting, roadmap generation, and deterministic capture-rate measurement rather than being sold as a public minute allowance.

Call `qc_get_launch_status` before launch-sensitive production workflows when an agent needs the live Product Hunt go/no-go state, remaining blockers, and operator commands. Call `qc_get_launch_handoff` when the agent needs blocker-specific required actions, proof commands, launchDoctorCommands, and the no-launch rule. Call `qc_get_launch_doctor` when the agent needs the `/v1/launch-doctor` blocker fix plan plus normalized launch-doctor command coverage, including the hosted Render media-ingress proof command. Call `qc_get_launch_evidence` when the agent needs a redacted evidence bundle from `/v1/launch-evidence` without local npm scripts. These launch endpoints are public; the other QC tools still require an API key.

Call `qc_estimate_cost` before uploading large media or asking for model-backed checks. It returns the effective checks, removed checks, margin safety, and cost estimate without creating a job.

## Tools

- `qc_estimate_cost`
- `qc_get_launch_status`
- `qc_get_launch_handoff`
- `qc_get_launch_doctor`
- `qc_get_launch_evidence`
- `qc_get_pipeline_handoff`
- `qc_get_npo_pipeline_handoff`
- `qc_get_pipeline_recipes`
- `qc_get_cost_basis`
- `qc_run_video`
- `qc_run_local_file`
- `qc_get_job`
- `qc_get_report`
- `qc_get_events`
- `qc_get_artifacts`
- `qc_get_marker_csv`
- `qc_submit_gate_verdict`
- `qc_list_recent_jobs`
- `qc_create_upload_url`

Use `idempotency_key` with `qc_run_video` when an agent may retry the same asset. The hosted API returns the existing job instead of creating a duplicate run.
Use `qc_submit_gate_verdict` after running `scripts/qc-engine/run_gate.py` so the hosted job report reflects the full-video gate result.
Internal Gemini capture-rate backtests are not part of the public MCP package. Run them only from the private UploadCheck repo with `scripts/qc-engine/gemini_watch.py`.

## Codex Install Shape

```bash
cd mcp-server
npm install
node index.mjs
```

## Client Config Snippets

Machine-readable install snippets for Codex, Claude Desktop, Cursor, and generic
stdio MCP clients are published in `mcp-install.json`. Keep this file aligned
with the package name `uploadcheck-mcp`, binary `uploadcheck-mcp`, current
hosted API base URL, and first-call sequence for NPO/NTO production pipelines.
The current MCP install path is a public GitHub clone or local checkout with a workspace API key tied to included plan minutes or an operator-created account. The `npx -y @drantoniou/uploadcheck-mcp` snippets in `mcp-install.json` are future-package snippets for after `uploadcheck-mcp` is published to npm.
