import { z } from "zod";
import type { McpToolDefinition, ToolContext } from "../types.js";

const ListSchema = z.object({ agentId: z.string().min(1) });

const RegisterSchema = z.object({
  agentId: z.string().min(1),
  publicKey: z.string().regex(/^0x[a-fA-F0-9]+$/u, "publicKey must be 0x-prefixed hex"),
  algorithm: z.enum(["secp256k1", "ed25519"]).default("secp256k1"),
  label: z.string().max(120).optional(),
});

const RevokeSchema = z.object({
  agentId: z.string().min(1),
  keyId: z.string().min(1),
  reason: z.string().min(1).max(500),
});

type Action = "list" | "register" | "revoke";

async function call(action: Action, payload: unknown, ctx: ToolContext) {
  if (!ctx.token) {
    return { ok: false as const, error: "missing_auth_token" };
  }
  const fetchImpl = ctx.fetch ?? globalThis.fetch;
  const base = ctx.apiUrl.replace(/\/$/u, "");
  let res: Response;

  if (action === "list") {
    const { agentId } = ListSchema.parse(payload);
    res = await fetchImpl(`${base}/api/v1/agents/${agentId}/signing-keys`, {
      headers: { authorization: `Bearer ${ctx.token}` },
    });
  } else if (action === "register") {
    const body = RegisterSchema.parse(payload);
    res = await fetchImpl(`${base}/api/v1/agents/${body.agentId}/signing-keys`, {
      method: "POST",
      headers: { "content-type": "application/json", authorization: `Bearer ${ctx.token}` },
      body: JSON.stringify({
        publicKey: body.publicKey,
        algorithm: body.algorithm,
        label: body.label,
      }),
    });
  } else {
    const body = RevokeSchema.parse(payload);
    res = await fetchImpl(`${base}/api/v1/agents/${body.agentId}/signing-keys/${body.keyId}`, {
      method: "DELETE",
      headers: { "content-type": "application/json", authorization: `Bearer ${ctx.token}` },
      body: JSON.stringify({ reason: body.reason }),
    });
  }

  if (!res.ok) {
    const text = await res.text();
    return { ok: false as const, status: res.status, error: `gateway_${res.status}`, body: text };
  }
  const json = (await res.json().catch(() => ({}))) as Record<string, unknown>;
  return { ok: true as const, status: res.status, action, ...json };
}

export const signingKeyTool: McpToolDefinition = {
  name: "signing_keys",
  description:
    "Manage an agent's signed-telemetry keys (list / register / revoke). Wraps /api/v1/agents/{id}/signing-keys.",
  inputSchema: {
    type: "object",
    required: ["action", "payload"],
    properties: {
      action: { type: "string", enum: ["list", "register", "revoke"] },
      payload: { type: "object" },
    },
  },
  handler: async (raw, ctx) => {
    const parsed = z
      .object({
        action: z.enum(["list", "register", "revoke"]),
        payload: z.unknown(),
      })
      .parse(raw);
    return call(parsed.action, parsed.payload, ctx);
  },
};
