import { apitierGet, type ApitierConfig } from "../client.js";

export const validateEmailTool = {
  name: "validate_email",
  geography: ["GLOBAL"] as const,
  domain: "identity" as const,
  description:
    "Validate an email address. Checks syntax, MX records, SMTP reachability, typos, and disposable domains. " +
    "Use before storing any user-provided email address. Returns isValid flag plus per-check breakdown.",
  inputSchema: {
    type: "object",
    properties: {
      email: {
        type: "string",
        description: "The email address to validate (e.g. user@example.com)",
      },
    },
    required: ["email"],
  },
} as const;

export async function runValidateEmail(
  args: { email: string },
  config: ApitierConfig
): Promise<string> {
  const data = await apitierGet(
    `${config.baseUrls.email}/validate`,
    { email: args.email },
    config.keys.email!
  );
  return JSON.stringify(data, null, 2);
}
