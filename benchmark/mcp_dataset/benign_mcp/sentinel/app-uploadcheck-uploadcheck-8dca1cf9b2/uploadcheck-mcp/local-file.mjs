import { createReadStream } from "node:fs";
import { buildJobRequest } from "./request-builder.mjs";

export function buildLocalFileRequest(input = {}) {
  const filePath = input.file_path || input.path;
  if (!filePath) throw new Error("qc_run_local_file requires file_path.");
  return buildJobRequest(filePath, {
    apiBaseUrl: input.api_base_url,
    profile: input.profile,
    checks: input.checks,
    manifestPath: input.manifest_path,
    transcriptPath: input.transcript_path,
    watchlistPath: input.watchlist_path,
    expectedScriptPath: input.expected_script_path,
    sidecarDir: input.sidecar_dir,
    callbackUrl: input.callback_url,
    idempotencyKey: input.idempotency_key,
    planId: input.plan_id,
    planPriceCents: input.plan_price_cents,
    includedMinutes: input.included_minutes,
    aiReviewSeconds: input.ai_review_seconds,
    costGuardrail: input.cost_guardrail,
    maxInlineMb: input.max_inline_mb,
    uploadMode: input.upload_mode
  });
}

export async function runLocalFileRequest(input, apiKey, fetchJson) {
  const request = buildLocalFileRequest(input);
  if (request.kind !== "signed_upload") {
    return fetchJson(request.path, { method: request.method, body: request.payload });
  }

  const upload = await fetchJson(request.createUpload.path, {
    method: request.createUpload.method,
    body: request.createUpload.payload
  });
  const putResponse = await fetch(upload.signedPutUrl, {
    method: "PUT",
    headers: {
      "content-type": request.contentType,
      "content-length": String(request.sizeBytes)
    },
    body: createReadStream(request.filePath),
    duplex: "half"
  });
  if (!putResponse.ok) {
    const text = await putResponse.text();
    throw new Error(`UploadCheck upload ${putResponse.status}: ${text}`);
  }
  return fetchJson(request.createJob.path, {
    method: request.createJob.method,
    body: {
      ...request.createJob.payload,
      upload_id: upload.uploadId
    }
  });
}
