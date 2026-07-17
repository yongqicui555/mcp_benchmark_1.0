import { apitierGet, type ApitierConfig } from "../client.js";

export const indiaPincodeTool = {
  name: "lookup_india_pincode",
  geography: ["IN"] as const,
  domain: "address" as const,
  description:
    "Look up an Indian PIN code (postal index number) to get the state, district, sub-district, " +
    "and town/village information. Use for Indian e-commerce checkout, address validation, and delivery routing.",
  inputSchema: {
    type: "object",
    properties: {
      pincode: {
        type: "string",
        description: "6-digit Indian PIN code to look up (e.g. 110001 for New Delhi)",
      },
    },
    required: ["pincode"],
  },
} as const;

export async function runIndiaPincodeLookup(
  args: { pincode: string },
  config: ApitierConfig
): Promise<string> {
  const data = await apitierGet(
    `${config.baseUrls.pincode}/in/places/pincode`,
    { pincode: args.pincode },
    config.keys.pincode!
  );
  return JSON.stringify(data, null, 2);
}
