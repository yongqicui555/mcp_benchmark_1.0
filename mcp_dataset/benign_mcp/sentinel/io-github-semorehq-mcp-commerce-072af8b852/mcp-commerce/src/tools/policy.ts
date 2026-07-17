// @deprecated — ADR-0062 (2026-04-26): canonical 5-tool 표면에서 제거됨.
// 머천트 약관/배송정책 surface 는 별도 채널로 이전 (FU-0062-5 RFC 진행 중).
// 본 모듈은 backward-compat 만 위해 export 유지.

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
  body: z.string(), // plain text or markdown
  url: z.string().url().optional(),
});

export type GetPolicyOutput = z.infer<typeof GetPolicyOutput>;

export const getPolicyTool = {
  name: "get_policy" as const,
  description: "Fetch a store policy (returns, refunds, shipping, privacy, terms) in the given language.",
  inputSchema: GetPolicyInput,
  outputSchema: GetPolicyOutput,
  handler: async (input: GetPolicyInput): Promise<GetPolicyOutput> => ({
    kind: input.kind,
    lang: input.lang,
    version: "0.0.0-skeleton",
    updatedAt: new Date(0).toISOString(),
    body: `Skeleton ${input.kind} policy. Replace with your real policy text.`,
  }),
};
