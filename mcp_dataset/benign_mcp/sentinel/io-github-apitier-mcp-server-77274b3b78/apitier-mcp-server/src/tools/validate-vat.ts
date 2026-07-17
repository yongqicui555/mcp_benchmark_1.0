import { apitierGet, type ApitierConfig } from "../client.js";

export const validateVatTool = {
  name: "validate_vat",
  geography: ["GB", "EU"] as const,
  domain: "compliance" as const,
  description:
    "Validate a VAT (Value Added Tax) registration number. " +
    "Checks whether the VAT number is registered and returns the registered business name and address. " +
    "Essential for B2B invoicing agents and checkout flows requiring VAT verification.",
  inputSchema: {
    type: "object",
    properties: {
      vatNumber: {
        type: "string",
        description:
          "VAT number to validate. Include country prefix (e.g. GB123456789, DE123456789)",
      },
    },
    required: ["vatNumber"],
  },
} as const;

export async function runValidateVat(
  args: { vatNumber: string },
  config: ApitierConfig
): Promise<string> {
  const data = await apitierGet(
    `${config.baseUrls.vat}/validate`,
    { vat_number: args.vatNumber },   // API uses vat_number, not vatNumber
    config.keys.vat!
  );
  return JSON.stringify(data, null, 2);
}
