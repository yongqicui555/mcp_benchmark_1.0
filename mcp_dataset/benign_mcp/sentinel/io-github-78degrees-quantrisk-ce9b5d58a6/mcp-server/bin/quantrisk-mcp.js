#!/usr/bin/env node
/**
 * quantrisk-mcp — stdio ⇄ Streamable HTTP bridge.
 *
 * Reads MCP JSON-RPC messages line-by-line from stdin, forwards each one
 * to the QuantRisk hosted MCP endpoint, and writes the JSON-RPC response
 * back to stdout. Lets stdio-only hosts (Claude Desktop, Cursor) consume
 * the remote QuantRisk MCP server without running anything locally.
 *
 * Env:
 *   QUANTRISK_API_KEY   Bearer token (optional — anonymous requests hit
 *                       the free-tier limits on the server).
 *   QUANTRISK_MCP_URL   Override the remote endpoint (default points at
 *                       the production worker).
 *
 * Wire protocol:
 *   stdin  — newline-delimited JSON-RPC 2.0 messages
 *   stdout — newline-delimited JSON-RPC 2.0 messages
 *   stderr — diagnostic logs only (must NEVER carry JSON-RPC traffic)
 */

import { createInterface } from "node:readline";

const REMOTE_URL =
  process.env.QUANTRISK_MCP_URL ||
  "https://quantrisk-mcp.quantrisk.workers.dev/mcp";
const API_KEY = process.env.QUANTRISK_API_KEY;

if (!API_KEY) {
  process.stderr.write(
    "[quantrisk-mcp] QUANTRISK_API_KEY is not set. Anonymous requests will hit " +
      "free-tier rate limits. Get a key at https://quantrisk.dev and add it to " +
      "your MCP client config.\n",
  );
}

// ---------------------------------------------------------------------------
// Output helpers
// ---------------------------------------------------------------------------

function writeStdout(obj) {
  process.stdout.write(JSON.stringify(obj) + "\n");
}

function writeJsonRpcError(id, code, message) {
  writeStdout({
    jsonrpc: "2.0",
    id: id ?? null,
    error: { code, message },
  });
}

// ---------------------------------------------------------------------------
// HTTP forward
// ---------------------------------------------------------------------------

async function forward(message) {
  const isRequest = message && typeof message === "object" && "id" in message;

  let response;
  try {
    response = await fetch(REMOTE_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json, text/event-stream",
        ...(API_KEY ? { Authorization: `Bearer ${API_KEY}` } : {}),
      },
      body: JSON.stringify(message),
    });
  } catch (err) {
    if (isRequest) {
      writeJsonRpcError(message.id, -32603, `Network error: ${err.message}`);
    } else {
      process.stderr.write(`[quantrisk-mcp] Notification dropped (network): ${err.message}\n`);
    }
    return;
  }

  // 202/204 = notification ack; nothing to write back.
  if (response.status === 202 || response.status === 204) {
    if (!response.body?.cancel) return;
    try { await response.body.cancel(); } catch {}
    return;
  }

  const contentType = (response.headers.get("content-type") || "").toLowerCase();

  if (contentType.includes("application/json")) {
    let body;
    try {
      body = await response.json();
    } catch (err) {
      if (isRequest) {
        writeJsonRpcError(
          message.id,
          -32603,
          `Invalid JSON from server (HTTP ${response.status}): ${err.message}`,
        );
      }
      return;
    }
    if (Array.isArray(body)) {
      for (const item of body) writeStdout(item);
    } else {
      writeStdout(body);
    }
    return;
  }

  if (contentType.includes("text/event-stream")) {
    await drainSseStream(response.body, message);
    return;
  }

  // Unexpected content-type. Surface as a JSON-RPC error if this was a request.
  const text = await response.text().catch(() => "");
  if (isRequest) {
    writeJsonRpcError(
      message.id,
      -32603,
      `Server returned HTTP ${response.status} (${contentType || "no content-type"}): ${text.slice(0, 200)}`,
    );
  } else {
    process.stderr.write(
      `[quantrisk-mcp] Unexpected ${response.status} response: ${text.slice(0, 200)}\n`,
    );
  }
}

// ---------------------------------------------------------------------------
// SSE parser — emits one JSON-RPC message per `data:` event
// ---------------------------------------------------------------------------

async function drainSseStream(stream, originalMessage) {
  const reader = stream.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let dataLines = [];

  function flushEvent() {
    if (dataLines.length === 0) return;
    const payload = dataLines.join("\n");
    dataLines = [];
    if (!payload.trim()) return;
    try {
      const parsed = JSON.parse(payload);
      if (Array.isArray(parsed)) {
        for (const item of parsed) writeStdout(item);
      } else {
        writeStdout(parsed);
      }
    } catch {
      process.stderr.write(
        `[quantrisk-mcp] Skipping malformed SSE event: ${payload.slice(0, 160)}\n`,
      );
    }
  }

  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      let nl;
      while ((nl = buffer.indexOf("\n")) !== -1) {
        const line = buffer.slice(0, nl).replace(/\r$/, "");
        buffer = buffer.slice(nl + 1);

        if (line === "") {
          flushEvent();
        } else if (line.startsWith(":")) {
          // SSE comment / heartbeat — ignore
        } else if (line.startsWith("data:")) {
          dataLines.push(line.slice(5).replace(/^ /, ""));
        }
        // event:/id:/retry: are unused by MCP — ignore
      }
    }
    flushEvent();
  } catch (err) {
    const isRequest =
      originalMessage && typeof originalMessage === "object" && "id" in originalMessage;
    if (isRequest) {
      writeJsonRpcError(originalMessage.id, -32603, `SSE stream error: ${err.message}`);
    } else {
      process.stderr.write(`[quantrisk-mcp] SSE stream error: ${err.message}\n`);
    }
  }
}

// ---------------------------------------------------------------------------
// stdin line loop
// ---------------------------------------------------------------------------

const inflight = new Set();
let stdinClosed = false;

function track(promise) {
  inflight.add(promise);
  promise.finally(() => {
    inflight.delete(promise);
    if (stdinClosed && inflight.size === 0) process.exit(0);
  });
}

const rl = createInterface({ input: process.stdin });

rl.on("line", (line) => {
  const trimmed = line.trim();
  if (!trimmed) return;

  let message;
  try {
    message = JSON.parse(trimmed);
  } catch (err) {
    process.stderr.write(
      `[quantrisk-mcp] Skipping non-JSON stdin line: ${trimmed.slice(0, 160)}\n`,
    );
    return;
  }

  // Fire concurrently — JSON-RPC `id` on the host side matches responses,
  // so out-of-order completion is fine.
  track(
    forward(message).catch((err) => {
      const id = message && typeof message === "object" ? message.id : null;
      writeJsonRpcError(id, -32603, `Unexpected bridge error: ${err.message}`);
    }),
  );
});

rl.on("close", () => {
  stdinClosed = true;
  if (inflight.size === 0) process.exit(0);
  // Otherwise wait — track() will exit once the last forward settles.
});

for (const sig of ["SIGINT", "SIGTERM"]) {
  process.on(sig, () => process.exit(0));
}
