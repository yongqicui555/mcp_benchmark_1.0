#!/usr/bin/env node
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { runLocalFileRequest } from "./local-file.mjs";

const apiBaseUrl = process.env.UPLOADCHECK_API_BASE_URL || "https://api.uploadcheck.app";
const apiKey = process.env.UPLOADCHECK_API_KEY;

const server = new McpServer({
  name: "uploadcheck",
  version: "0.1.0"
});

server.tool(
  "qc_estimate_cost",
  "Estimate checked minutes and effective QC gates before uploading or running media.",
  {
    minutes: z.number().optional(),
    duration_seconds: z.number().optional(),
    profile: z.string().optional(),
    checks: z.string().optional(),
    plan_id: z.string().optional(),
    plan_price_cents: z.number().optional(),
    included_minutes: z.number().optional(),
    ai_review_seconds: z.number().optional(),
    cost_guardrail: z.enum(["downgrade", "block", "off"]).optional()
  },
  async (input) => jsonTool(await apiFetch("/v1/qc/estimate", { method: "POST", body: input }))
);

server.tool(
  "qc_run_video",
  "Start an UploadCheck quality check from a YouTube URL, upload id, or signed URL.",
  {
    youtube_url: z.string().optional(),
    upload_id: z.string().optional(),
    signed_url: z.string().optional(),
    media_base64: z.string().optional(),
    media_content_type: z.string().optional(),
    media_mime_type: z.string().optional(),
    media_filename: z.string().optional(),
    media_kind: z.enum(["video", "audio", "image"]).optional(),
    video_base64: z.string().optional(),
    video_content_type: z.string().optional(),
    video_mime_type: z.string().optional(),
    video_filename: z.string().optional(),
    audio_base64: z.string().optional(),
    audio_content_type: z.string().optional(),
    audio_mime_type: z.string().optional(),
    audio_filename: z.string().optional(),
    data_url: z.string().optional(),
    filename: z.string().optional(),
    manifest_json: z.any().optional(),
    manifest_base64: z.string().optional(),
    manifest_filename: z.string().optional(),
    manifest_url: z.string().optional(),
    transcript_text: z.string().optional(),
    transcript_json: z.any().optional(),
    transcript_base64: z.string().optional(),
    transcript_filename: z.string().optional(),
    transcript_url: z.string().optional(),
    watchlist_json: z.any().optional(),
    watchlist_base64: z.string().optional(),
    watchlist_filename: z.string().optional(),
    watchlist_url: z.string().optional(),
    expected_script_text: z.string().optional(),
    expected_script_json: z.any().optional(),
    expected_script_base64: z.string().optional(),
    expected_script_filename: z.string().optional(),
    expected_script_url: z.string().optional(),
    chunk_sidecars_url: z.string().optional(),
    profile: z.string().optional(),
    checks: z.string().optional(),
    plan_id: z.string().optional(),
    plan_price_cents: z.number().optional(),
    included_minutes: z.number().optional(),
    ai_review_seconds: z.number().optional(),
    cost_guardrail: z.enum(["downgrade", "block", "off"]).optional(),
    callback_url: z.string().optional(),
    idempotency_key: z.string().optional()
  },
  async (input) => jsonTool(await apiFetch("/v1/qc/jobs", { method: "POST", body: input }))
);

server.tool(
  "qc_run_local_file",
  "Read a local media file from the agent workspace, send it through Render inline when small, and start an UploadCheck run.",
  {
    file_path: z.string(),
    profile: z.string().optional(),
    checks: z.string().optional(),
    manifest_path: z.string().optional(),
    transcript_path: z.string().optional(),
    watchlist_path: z.string().optional(),
    expected_script_path: z.string().optional(),
    sidecar_dir: z.string().optional(),
    max_inline_mb: z.number().optional(),
    upload_mode: z.enum(["auto", "inline", "signed"]).optional(),
    plan_id: z.string().optional(),
    plan_price_cents: z.number().optional(),
    included_minutes: z.number().optional(),
    ai_review_seconds: z.number().optional(),
    cost_guardrail: z.enum(["downgrade", "block", "off"]).optional(),
    callback_url: z.string().optional(),
    idempotency_key: z.string().optional()
  },
  async (input) => jsonTool(await runLocalFileRequest(input, apiKey, apiFetch))
);

server.tool(
  "qc_get_job",
  "Poll QC job status, progress, verdict, and metered minutes.",
  { job_id: z.string() },
  async ({ job_id }) => jsonTool(await apiFetch(`/v1/qc/jobs/${job_id}`))
);

server.tool(
  "qc_get_report",
  "Retrieve timestamped QC report with evidence and artifacts.",
  { job_id: z.string() },
  async ({ job_id }) => jsonTool(await apiFetch(`/v1/qc/jobs/${job_id}/report`))
);

server.tool(
  "qc_get_events",
  "Retrieve lifecycle events for a QC job so an agent can explain what ran.",
  { job_id: z.string() },
  async ({ job_id }) => jsonTool(await apiFetch(`/v1/qc/jobs/${job_id}/events`))
);

server.tool(
  "qc_get_artifacts",
  "List report artifacts generated for a QC job.",
  { job_id: z.string() },
  async ({ job_id }) => jsonTool(await apiFetch(`/v1/qc/jobs/${job_id}/artifacts`))
);

server.tool(
  "qc_get_marker_csv",
  "Download editor marker CSV for a QC job.",
  { job_id: z.string() },
  async ({ job_id }) => textTool(await apiTextFetch(`/v1/qc/jobs/${job_id}/artifacts/markers`))
);

server.tool(
  "qc_create_upload_url",
  "Create a signed upload URL for a local video file.",
  {
    filename: z.string(),
    content_type: z.string(),
    size_bytes: z.number()
  },
  async (input) => jsonTool(await apiFetch("/v1/uploads", { method: "POST", body: input }))
);

const transport = new StdioServerTransport();
await server.connect(transport);

async function apiFetch(path, options = {}) {
  const response = await authedFetch(path, options);
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(`UploadCheck API ${response.status}: ${JSON.stringify(payload)}`);
  }
  return payload;
}

async function publicApiFetch(path, options = {}) {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    method: options.method || "GET",
    headers: {
      "content-type": "application/json"
    },
    body: options.body ? JSON.stringify(options.body) : undefined
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(`UploadCheck API ${response.status}: ${JSON.stringify(payload)}`);
  }
  return payload;
}

async function apiTextFetch(path, options = {}) {
  const response = await authedFetch(path, options);
  const payload = await response.text();
  if (!response.ok) {
    throw new Error(`UploadCheck API ${response.status}: ${payload}`);
  }
  return payload;
}

async function authedFetch(path, options = {}) {
  if (!apiKey) {
    throw new Error("Set UPLOADCHECK_API_KEY before running the MCP server.");
  }

  return fetch(`${apiBaseUrl}${path}`, {
    method: options.method || "GET",
    headers: {
      "content-type": "application/json",
      authorization: `Bearer ${apiKey}`
    },
    body: options.body ? JSON.stringify(options.body) : undefined
  });
}

function jsonTool(payload) {
  return {
    content: [
      {
        type: "text",
        text: JSON.stringify(payload, null, 2)
      }
    ]
  };
}

function textTool(text) {
  return {
    content: [
      {
        type: "text",
        text
      }
    ]
  };
}
