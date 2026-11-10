import { extname, basename, join, relative } from "node:path";
import { statSync, readFileSync, existsSync, readdirSync } from "node:fs";
import { applyProfileToInput } from "./qc-profiles.mjs";

const DEFAULT_API_BASE_URL = "https://api.uploadcheck.app";
const DEFAULT_MAX_INLINE_MB = 128;

const CONTENT_TYPES = new Map([
  [".mp4", "video/mp4"],
  [".mov", "video/quicktime"],
  [".m4v", "video/x-m4v"],
  [".webm", "video/webm"],
  [".mp3", "audio/mpeg"],
  [".m4a", "audio/mp4"],
  [".wav", "audio/wav"],
  [".aac", "audio/aac"],
  [".ogg", "audio/ogg"],
  [".jpg", "image/jpeg"],
  [".jpeg", "image/jpeg"],
  [".png", "image/png"],
  [".webp", "image/webp"]
]);

export function buildJobRequest(target, options = {}) {
  if (!target) throw new Error("qc_run_local_file requires file_path.");
  if (!existsSync(target)) throw new Error(`File not found: ${target}`);

  const apiBaseUrl = trimTrailingSlash(options.apiBaseUrl || process.env.UPLOADCHECK_API_BASE_URL || DEFAULT_API_BASE_URL);
  const maxInlineMb = Number(options.maxInlineMb || process.env.UPLOADCHECK_INLINE_MEDIA_MAX_MB || DEFAULT_MAX_INLINE_MB);
  const fileStat = statSync(target);
  const maxBytes = maxInlineMb * 1024 * 1024;
  const uploadMode = options.uploadMode || "auto";

  if (uploadMode === "signed" || (uploadMode === "auto" && fileStat.size > maxBytes)) {
    return buildSignedUploadPlan(target, options, fileStat, apiBaseUrl);
  }
  if (uploadMode === "inline" && fileStat.size > maxBytes) {
    throw new Error(`File is ${formatMb(fileStat.size)} MB; inline MCP payload limit is ${maxInlineMb} MB. Use signed upload or raise max_inline_mb.`);
  }

  const contentType = inferContentType(target);
  const payload = {
    media_base64: readFileSync(target).toString("base64"),
    media_content_type: contentType,
    media_kind: inferMediaKind(contentType),
    filename: basename(target)
  };
  attachJobOptions(payload, options);

  return {
    apiBaseUrl,
    path: "/v1/qc/jobs",
    method: "POST",
    kind: "job",
    payload
  };
}

function buildSignedUploadPlan(target, options, fileStat, apiBaseUrl) {
  const contentType = inferContentType(target);
  const jobPayload = {};
  attachJobOptions(jobPayload, {
    ...options,
    contentType,
    mediaKind: inferMediaKind(contentType),
    filename: basename(target)
  });

  return {
    apiBaseUrl,
    kind: "signed_upload",
    filePath: target,
    contentType,
    sizeBytes: fileStat.size,
    createUpload: {
      path: "/v1/uploads",
      method: "POST",
      payload: {
        filename: basename(target),
        content_type: contentType,
        size_bytes: fileStat.size
      }
    },
    createJob: {
      path: "/v1/qc/jobs",
      method: "POST",
      payload: jobPayload
    }
  };
}

function attachJobOptions(payload, options) {
  if (options.profile) payload.profile = options.profile;
  if (options.checks) payload.checks = options.checks;
  applyProfilePayload(payload, {
    contentType: options.contentType,
    mediaKind: options.mediaKind,
    filename: options.filename
  });
  attachManifest(payload, options);
  attachTranscript(payload, options);
  attachWatchlist(payload, options);
  attachExpectedScript(payload, options);
  attachChunkSidecars(payload, options);
  if (options.callbackUrl) payload.callback_url = options.callbackUrl;
  if (options.idempotencyKey) payload.idempotency_key = options.idempotencyKey;
  if (options.planId) payload.plan_id = options.planId;
  if (options.planPriceCents) payload.plan_price_cents = Number(options.planPriceCents);
  if (options.includedMinutes) payload.included_minutes = Number(options.includedMinutes);
  if (options.aiReviewSeconds) payload.ai_review_seconds = Number(options.aiReviewSeconds);
  if (options.costGuardrail) payload.cost_guardrail = options.costGuardrail;
}

function applyProfilePayload(payload, context = {}) {
  const resolved = applyProfileToInput({
    ...payload,
    media_kind: payload.media_kind || context.mediaKind,
    mediaKind: payload.media_kind || context.mediaKind,
    filename: payload.filename || context.filename,
    media_content_type: payload.media_content_type || context.contentType
  });
  if (resolved.profile) payload.profile = resolved.profile;
  if (resolved.requested_profile) payload.requested_profile = resolved.requested_profile;
  if (resolved.checks) payload.checks = resolved.checks;
}

function attachManifest(payload, options) {
  if (!options.manifestPath) return;
  if (!existsSync(options.manifestPath)) throw new Error(`Manifest not found: ${options.manifestPath}`);
  payload.manifest_json = JSON.parse(readFileSync(options.manifestPath, "utf8"));
  payload.manifest_filename = basename(options.manifestPath);
}

function attachTranscript(payload, options) {
  if (!options.transcriptPath) return;
  if (!existsSync(options.transcriptPath)) throw new Error(`Transcript not found: ${options.transcriptPath}`);
  const text = readFileSync(options.transcriptPath, "utf8");
  if (options.transcriptPath.toLowerCase().endsWith(".json")) payload.transcript_json = JSON.parse(text);
  else payload.transcript_text = text;
  payload.transcript_filename = basename(options.transcriptPath);
}

function attachWatchlist(payload, options) {
  if (!options.watchlistPath) return;
  if (!existsSync(options.watchlistPath)) throw new Error(`Watchlist not found: ${options.watchlistPath}`);
  payload.watchlist_json = JSON.parse(readFileSync(options.watchlistPath, "utf8"));
  payload.watchlist_filename = basename(options.watchlistPath);
}

function attachExpectedScript(payload, options) {
  if (!options.expectedScriptPath) return;
  if (!existsSync(options.expectedScriptPath)) throw new Error(`Expected script not found: ${options.expectedScriptPath}`);
  const text = readFileSync(options.expectedScriptPath, "utf8");
  if (options.expectedScriptPath.toLowerCase().endsWith(".json")) payload.expected_script_json = JSON.parse(text);
  else payload.expected_script_text = text;
  payload.expected_script_filename = basename(options.expectedScriptPath);
}

function attachChunkSidecars(payload, options) {
  if (!options.sidecarDir) return;
  if (!existsSync(options.sidecarDir)) throw new Error(`Sidecar dir not found: ${options.sidecarDir}`);
  if (!statSync(options.sidecarDir).isDirectory()) throw new Error(`Sidecar dir is not a directory: ${options.sidecarDir}`);
  const files = collectJsonFiles(options.sidecarDir).slice(0, 200);
  payload.chunk_sidecars_json = files.map((filePath) => ({
    relative_path: relative(options.sidecarDir, filePath),
    filename: basename(filePath),
    json: JSON.parse(readFileSync(filePath, "utf8"))
  }));
  payload.chunk_sidecar_dirname = basename(options.sidecarDir);
}

function collectJsonFiles(dir) {
  const out = [];
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const filePath = join(dir, entry.name);
    if (entry.isDirectory()) out.push(...collectJsonFiles(filePath));
    else if (entry.isFile() && entry.name.toLowerCase().endsWith(".json")) out.push(filePath);
  }
  return out.sort();
}

function trimTrailingSlash(value) {
  return value.replace(/\/+$/, "");
}

function inferContentType(filePath) {
  return CONTENT_TYPES.get(extname(filePath).toLowerCase()) || "application/octet-stream";
}

function inferMediaKind(contentType) {
  if (contentType.startsWith("audio/")) return "audio";
  if (contentType.startsWith("image/")) return "image";
  return "video";
}

function formatMb(bytes) {
  return (bytes / 1024 / 1024).toFixed(1);
}
