// @deprecated — ADR-0062 (2026-04-26): canonical 5-tool 채택으로 `get_policy`
// 가 commerce action tool 표면에서 제거되었다.
//
// 머천트 약관/배송정책 surface 는 별도 채널로 이전 — MCP `resources/`
// namespace 또는 separate `policy.semore.net` static. 결정은 FU-0062-5
// RFC 에서 진행 중 (legal-agent + cs-agent + mcp-agent 협업).
//
// REMOVAL TIMELINE: FU-0062-5 RFC land 후 1 minor version 추가 유지 →
// 그 후 제거. 본 shim 은 오로지 backward compat (test/tools.test.ts 등) 용.

import { z } from "zod";

export const GetPolicyInput = z.object({
  kind: z.enum(["returns", "refunds", "shipping", "privacy", "terms"]),
  lang: z.enum(["en", "ja", "de", "fr", "es", "ko"]).default("en"),
});

export type GetPolicyInput = z.infer<typeof GetPolicyInput>;

export const GetPolicyOutput = z.object({
  kind: z.string(),
  lang: z.string(),
  version: z.string(),
  updatedAt: z.string(), // ISO 8601
  body: z.string(),
  url: z.string().url().optional(),
});

export type GetPolicyOutput = z.infer<typeof GetPolicyOutput>;

let warned = false;
function warnOnce(): void {
  if (warned) return;
  warned = true;
  console.warn(
    "[@semore/mcp-commerce] get_policy is DEPRECATED (ADR-0062). " +
      "Policy surface is moving to MCP resources/ or policy.semore.net (FU-0062-5 RFC).",
  );
}

/**
 * @deprecated Removal pending FU-0062-5 RFC (policy surface relocation).
 */
export const getPolicyTool = {
  name: "get_policy" as const,
  description:
    "[DEPRECATED — see FU-0062-5 RFC] Fetch a store policy (returns, refunds, shipping, privacy, terms) in the given language.",
  inputSchema: GetPolicyInput,
  outputSchema: GetPolicyOutput,
  handler: async (input: GetPolicyInput): Promise<GetPolicyOutput> => {
    warnOnce();
    return {
      kind: input.kind,
      lang: input.lang,
      version: "0.0.0-skeleton",
      updatedAt: new Date(0).toISOString(),
      body: `Skeleton ${input.kind} policy. Replace with your real policy text.`,
    };
  },
};
