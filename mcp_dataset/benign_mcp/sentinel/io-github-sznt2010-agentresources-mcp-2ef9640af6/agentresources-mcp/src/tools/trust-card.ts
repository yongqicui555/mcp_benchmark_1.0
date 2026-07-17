import { z } from "zod";
import type { McpToolDefinition, ToolContext } from "../types.js";
import { WalletSchema } from "../types.js";

const InputSchema = z.object({
  wallet: WalletSchema,
  /**
   * When true, also fetch the latest Merkle anchor entry so the caller can
   * verify the chain anchor is fresh. Default false to keep the call cheap.
   */
  includeAnchor: z.boolean().optional().default(false),
});

type Input = z.input<typeof InputSchema>;

async function lookupTrustCard(input: Input, ctx: ToolContext) {
  const { wallet, includeAnchor } = InputSchema.parse(input);
  const fetchImpl = ctx.fetch ?? globalThis.fetch;
  const url = `${ctx.apiUrl.replace(/\/$/u, "")}/.well-known/trust-card/${wallet}`;
  const res = await fetchImpl(url, { headers: { accept: "application/vc+ld+json" } });

  if (res.status === 404) {
    return { ok: false as const, status: 404, error: "no_trust_card_for_wallet", wallet };
  }
  if (!res.ok) {
    return { ok: false as const, status: res.status, error: `gateway_${res.status}`, wallet };
  }

  const card = (await res.json()) as Record<string, unknown>;

  let anchor: Record<string, unknown> | null = null;
  if (includeAnchor) {
    const anchorRes = await fetchImpl(
      `${ctx.apiUrl.replace(/\/$/u, "")}/api/v1/anchor-proof?wallet=${wallet}`,
    );
    if (anchorRes.ok) {
      anchor = (await anchorRes.json()) as Record<string, unknown>;
    }
  }

  return { ok: true as const, status: 200, wallet, card, anchor };
}

export const trustCardTool: McpToolDefinition = {
  name: "trust_card_lookup",
  description:
    "Fetch the public Trust Card (signed JSON-LD VC) for a wallet from /.well-known/trust-card/{wallet}. Optionally include the latest Merkle anchor proof.",
  inputSchema: {
    type: "object",
    required: ["wallet"],
    properties: {
      wallet: {
        type: "string",
        description: "0x-prefixed 20-byte EVM wallet address (case-insensitive).",
        pattern: "^0x[a-fA-F0-9]{40}$",
      },
      includeAnchor: {
        type: "boolean",
        description: "When true, also include the latest Merkle anchor entry. Default false.",
        default: false,
      },
    },
  },
  handler: (input, ctx) => lookupTrustCard(input as Input, ctx),
};
