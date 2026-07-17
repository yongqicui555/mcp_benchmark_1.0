import { apitierGet, type ApitierConfig } from "../client.js";

export const ukPostcodeLookupTool = {
  name: "lookup_uk_postcode",
  geography: ["GB"] as const,
  domain: "address" as const,
  description:
    "Look up a UK postcode to get the full address list, district, ward, county, country, and GPS coordinates. " +
    "Use for address auto-fill, delivery routing, or validating user-entered UK addresses.",
  inputSchema: {
    type: "object",
    properties: {
      postcode: {
        type: "string",
        description:
          "UK postcode to look up. Spaces are optional (e.g. SW1A 1AA or SW1A1AA)",
      },
    },
    required: ["postcode"],
  },
} as const;

export async function runUkPostcodeLookup(
  args: { postcode: string },
  config: ApitierConfig
): Promise<string> {
  const postcode = args.postcode.replace(/\s+/g, "").toUpperCase();
  const data = await apitierGet(
    `${config.baseUrls.postcode}/postcodes/${postcode}`,
    {},
    config.keys.postcode!
  );
  return JSON.stringify(data, null, 2);
}

