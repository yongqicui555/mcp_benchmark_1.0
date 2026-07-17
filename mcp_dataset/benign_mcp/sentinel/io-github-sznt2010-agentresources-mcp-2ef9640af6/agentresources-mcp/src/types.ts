import { z } from "zod";

/**
 * Shared runtime context passed to every operational tool. Lets the CLI and
 * MCP server load env-derived defaults once and inject them, so tool handlers
 * never read process.env directly (easier to test, easier to unit-spy).
 */
export type ToolContext = {
  /** Base URL for the AR gateway, e.g. https://api.agentresources.xyz. */
  apiUrl: string;
  /**
   * Bearer token for authenticated routes. Either a Supabase JWT (legacy
   * dashboard path) or a wallet session token (recommended for autonomous
   * agents — see @agentresources/sdk walletLogin).
   */
  token?: string;
  /**
   * Optional fetch implementation override. Defaults to globalThis.fetch.
   * Provided so tests can inject a stub without monkey-patching globals.
   */
  fetch?: typeof fetch;
};

export const WalletSchema = z
  .string()
  .regex(/^0x[a-fA-F0-9]{40}$/u, "wallet must be a 0x-prefixed 20-byte hex address")
  .transform((w) => w.toLowerCase() as `0x${string}`);

export type Wallet = z.infer<typeof WalletSchema>;

export type McpToolDefinition = {
  name: string;
  description: string;
  inputSchema: Record<string, unknown>;
  handler: (input: unknown, ctx: ToolContext) => Promise<unknown>;
};
