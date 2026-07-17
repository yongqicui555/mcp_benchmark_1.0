import { apitierGet, type ApitierConfig } from "../client.js";

export const validatePhoneTool = {
  name: "validate_phone",
  geography: ["GLOBAL"] as const,
  domain: "identity" as const,
  description:
    "Validate and parse a phone number. Returns whether it is valid, the country, carrier, " +
    "line type (mobile/landline), and international format. Accepts numbers in any international format.",
  inputSchema: {
    type: "object",
    properties: {
      phone: {
        type: "string",
        description:
          "Phone number to validate. Include country code prefix (e.g. +447911123456 or +12025550104)",
      },
    },
    required: ["phone"],
  },
} as const;

export async function runValidatePhone(
  args: { phone: string },
  config: ApitierConfig
): Promise<string> {
  const data = await apitierGet(
    `${config.baseUrls.phone}/validate`,
    { phone: args.phone },
    config.keys.phone!
  );
  return JSON.stringify(data, null, 2);
}
