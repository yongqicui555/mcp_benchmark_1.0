import { z } from "zod";
import type { McpToolDefinition, ToolContext } from "../types.js";

const SpanSchema = z.object({
  spanId: z.string().min(1),
  parentSpanId: z.string().nullable().optional(),
  agentId: z.string().min(1),
  name: z.string().min(1),
  startTimeUnixNano: z.string().min(1),
  endTimeUnixNano: z.string().min(1),
  attributes: z.record(z.unknown()).optional(),
  /** Signed envelope is opt-in; the SDK will compute it for callers. */
  envelope: z
    .object({
      signature: z.string(),
      signingPubkey: z.string(),
      prevChainHash: z.string().optional(),
      chainHash: z.string(),
      chainSeq: z.number().int().nonnegative(),
    })
    .optional(),
});

const InputSchema = z.object({
  agentId: z.string().min(1, "agentId is required"),
  spans: z.array(SpanSchema).min(1, "at least one span required"),
});

type Input = z.input<typeof InputSchema>;

async function ingestSpans(input: Input, ctx: ToolContext) {
  if (!ctx.token) {
    return {
      ok: false as const,
      error: "missing_auth_token",
      hint: "supply ctx.token via wallet session login",
    };
  }
  const { agentId, spans } = InputSchema.parse(input);
  const fetchImpl = ctx.fetch ?? globalThis.fetch;
  const url = `${ctx.apiUrl.replace(/\/$/u, "")}/api/v1/ingest/spans`;
  const res = await fetchImpl(url, {
    method: "POST",
    headers: {
      "content-type": "application/json",
      authorization: `Bearer ${ctx.token}`,
    },
    body: JSON.stringify({ agentId, spans }),
  });

  if (!res.ok) {
    const body = await res.text();
    return { ok: false as const, status: res.status, error: `gateway_${res.status}`, body };
  }
  const json = (await res.json()) as Record<string, unknown>;
  return { ok: true as const, status: res.status, ingested: spans.length, ...json };
}

export const telemetryTool: McpToolDefinition = {
  name: "telemetry_ingest",
  description:
    "Submit a batch of telemetry spans (optionally signed envelope) to the AR gateway. Requires an authenticated session token.",
  inputSchema: {
    type: "object",
    required: ["agentId", "spans"],
    properties: {
      agentId: { type: "string", description: "The AR agent UUID this span batch belongs to." },
      spans: {
        type: "array",
        minItems: 1,
        items: {
          type: "object",
          required: ["spanId", "agentId", "name", "startTimeUnixNano", "endTimeUnixNano"],
          properties: {
            spanId: { type: "string" },
            parentSpanId: { type: ["string", "null"] },
            agentId: { type: "string" },
            name: { type: "string" },
            startTimeUnixNano: { type: "string" },
            endTimeUnixNano: { type: "string" },
            attributes: { type: "object" },
            envelope: {
              type: "object",
              description:
                "Signed envelope; SDK computes this when signingPrivateKey is configured.",
            },
          },
        },
      },
    },
  },
  handler: (input, ctx) => ingestSpans(input as Input, ctx),
};
