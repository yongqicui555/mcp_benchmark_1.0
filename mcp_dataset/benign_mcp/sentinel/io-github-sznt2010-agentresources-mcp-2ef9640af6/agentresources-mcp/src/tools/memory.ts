import { z } from "zod";
import type { McpToolDefinition, ToolContext } from "../types.js";

/**
 * Memory verbs (D2 / D13 / D14): remember, recall, forget, improve.
 *
 * Backed by `/api/v1/memory/*` on the gateway, which writes into the unified
 * telemetry_raw_events table — there is no separate memory store.
 */

const RememberSchema = z.object({
  agentId: z.string().min(1),
  content: z.string().min(1).max(8000),
  chunkType: z
    .enum([
      "fact",
      "decision",
      "instruction",
      "observation",
      "outcome",
      "preference",
      "skill_call",
      "user_message",
      "agent_message",
      "tool_result",
      "error",
      "reflection",
      "summary",
    ])
    .default("fact"),
  salience: z.number().min(0).max(1).optional(),
  sessionId: z.string().optional(),
});

const RecallSchema = z.object({
  agentId: z.string().min(1),
  query: z.string().min(1).max(2000),
  k: z.number().int().min(1).max(50).default(8),
  chunkTypes: z.array(z.string()).optional(),
});

const ForgetSchema = z.object({
  agentId: z.string().min(1),
  chunkId: z.string().min(1),
  reason: z.string().min(1).max(500),
});

const ImproveSchema = z.object({
  agentId: z.string().min(1),
  chunkId: z.string().min(1),
  replacement: z.string().min(1).max(8000),
  reason: z.string().min(1).max(500),
});

type Verb = "remember" | "recall" | "forget" | "improve";

async function callMemory(verb: Verb, payload: unknown, ctx: ToolContext) {
  if (!ctx.token) {
    return {
      ok: false as const,
      error: "missing_auth_token",
      hint: "supply ctx.token via wallet session login",
    };
  }
  const fetchImpl = ctx.fetch ?? globalThis.fetch;
  const url = `${ctx.apiUrl.replace(/\/$/u, "")}/api/v1/memory/${verb}`;
  const res = await fetchImpl(url, {
    method: "POST",
    headers: { "content-type": "application/json", authorization: `Bearer ${ctx.token}` },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const body = await res.text();
    return { ok: false as const, status: res.status, error: `gateway_${res.status}`, body };
  }
  const json = (await res.json()) as Record<string, unknown>;
  return { ok: true as const, status: res.status, verb, ...json };
}

export const memoryTool: McpToolDefinition = {
  name: "memory",
  description:
    "Memory verbs (remember, recall, forget, improve). Reads and writes go through the unified telemetry-as-memory store; recall is a multi-stage retrieval (cosine + cross-encoder + MMR + tail prune) handled server-side.",
  inputSchema: {
    type: "object",
    required: ["verb", "payload"],
    properties: {
      verb: { type: "string", enum: ["remember", "recall", "forget", "improve"] },
      payload: { type: "object", description: "Verb-specific payload; see schemas." },
    },
  },
  handler: async (rawInput, ctx) => {
    const parsed = z
      .object({
        verb: z.enum(["remember", "recall", "forget", "improve"]),
        payload: z.unknown(),
      })
      .parse(rawInput);

    let payload: unknown;
    switch (parsed.verb) {
      case "remember":
        payload = RememberSchema.parse(parsed.payload);
        break;
      case "recall":
        payload = RecallSchema.parse(parsed.payload);
        break;
      case "forget":
        payload = ForgetSchema.parse(parsed.payload);
        break;
      case "improve":
        payload = ImproveSchema.parse(parsed.payload);
        break;
    }
    return callMemory(parsed.verb, payload, ctx);
  },
};
