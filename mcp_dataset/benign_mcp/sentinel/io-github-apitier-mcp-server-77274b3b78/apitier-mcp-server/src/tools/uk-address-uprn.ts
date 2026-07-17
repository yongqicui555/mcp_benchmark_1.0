import { apitierGet, type ApitierConfig } from "../client.js";

// ── verify_uk_address ─────────────────────────────────────────────────────────

export const verifyUkAddressTool = {
  name: "verify_uk_address",
  geography: ["GB"] as const,
  domain: "address" as const,
  description:
    "Verify a UK address against the Royal Mail PAF (Postal Address File). " +
    "Returns the canonical PAF address, UPRN (Unique Property Reference Number), " +
    "UDPRN, per-delivery-point geocode, and postcode-level admin data " +
    "(district, ward, county, country). " +
    "Use in KYC and onboarding workflows to confirm a UK address is real and " +
    "to obtain the UPRN as a persistent cross-source identity anchor. " +
    "Supply query to filter results to a specific premise when multiple " +
    "addresses exist at the postcode.",
  inputSchema: {
    type: "object",
    properties: {
      postcode: {
        type: "string",
        description:
          "UK postcode (e.g. SW1A 2AA or SW1A2AA). Spaces are optional.",
      },
      query: {
        type: "string",
        description:
          "Optional address fragment to filter results — " +
          "building number, building name, or organisation name " +
          "(e.g. '10', 'Flat 3', 'Barclays'). " +
          "Omit to return all addresses at the postcode.",
      },
    },
    required: ["postcode"],
  },
} as const;

// ── lookup_uprn ───────────────────────────────────────────────────────────────

export const lookupUprnTool = {
  name: "lookup_uprn",
  geography: ["GB"] as const,
  domain: "address" as const,
  description:
    "Look up a UK address by UDPRN (Unique Delivery Point Reference Number) " +
    "and return the full AddressBase record including UPRN, PAF canonical " +
    "address, per-delivery-point geocode (latitude/longitude/easting/northing), " +
    "match type, and Welsh address where applicable. " +
    "UDPRN is returned by verify_uk_address. Use this tool to enrich an " +
    "address with its persistent UPRN identifier and precise geocode " +
    "for cross-source entity resolution.",
  inputSchema: {
    type: "object",
    properties: {
      udprn: {
        type: "string",
        description:
          "UDPRN to look up. Obtain from verify_uk_address (each address " +
          "in the result includes a udprn field).",
      },
    },
    required: ["udprn"],
  },
} as const;

// ── helpers ───────────────────────────────────────────────────────────────────

function matchesQuery(address: Record<string, unknown>, query: string): boolean {
  const q = query.toLowerCase();
  const fields = [
    address.building_number,
    address.building_name,
    address.sub_building_name,
    address.organisation_name,
    address.line_1,
    address.premise,
  ];
  return fields.some(
    (f) => typeof f === "string" && f.toLowerCase().includes(q)
  );
}

// ── runners ───────────────────────────────────────────────────────────────────

export async function runVerifyUkAddress(
  args: { postcode: string; query?: string },
  config: ApitierConfig
): Promise<string> {
  const postcode = args.postcode.replace(/\s+/g, "").toUpperCase();
  const data = await apitierGet(
    `${config.baseUrls.postcode}/postcodes/${postcode}`,
    {},
    config.keys.postcode!
  ) as { result?: { addresses?: Record<string, unknown>[] } };

  if (!args.query || !data.result?.addresses) {
    return JSON.stringify(data, null, 2);
  }

  // Filter to matching addresses, preserve all postcode-level fields.
  const matched = data.result.addresses.filter((a) =>
    matchesQuery(a, args.query!)
  );

  return JSON.stringify(
    { ...data, result: { ...data.result, addresses: matched, matched_count: matched.length } },
    null,
    2
  );
}

export async function runLookupUprn(
  args: { udprn: string },
  config: ApitierConfig
): Promise<string> {
  const data = await apitierGet(
    `${config.baseUrls.postcode}/udprn/${args.udprn}`,
    {},
    config.keys.postcode!
  );
  return JSON.stringify(data, null, 2);
}
