import { apitierGet, type ApitierConfig } from "../client.js";

// ── verify_uk_company ─────────────────────────────────────────────────────────

export const verifyUkCompanyTool = {
  name: "verify_uk_company",
  geography: ["GB"] as const,
  domain: "kyc" as const,
  description:
    "Look up a UK company on Companies House by name or company number. " +
    "Returns the registered name, address, incorporation date, SIC codes, " +
    "company status (active/dissolved/dormant/liquidation), and filing health flags. " +
    "Use in KYC, onboarding, and statement audit workflows to verify UK business identity.",
  inputSchema: {
    type: "object",
    properties: {
      q: {
        type: "string",
        description:
          "Company name or Companies House number. " +
          "Numbers are matched directly (e.g. 01234567, SC123456). " +
          "Names trigger a Companies House search — prefer exact registered names for best results.",
      },
    },
    required: ["q"],
  },
} as const;

// ── get_company_psc ───────────────────────────────────────────────────────────

export const getCompanyPscTool = {
  name: "get_company_psc",
  geography: ["GB"] as const,
  domain: "kyc" as const,
  description:
    "Retrieve the Persons with Significant Control (PSC) register for a UK company. " +
    "Returns each PSC's name, nature of control (e.g. 75–100% share ownership), " +
    "notified date, nationality, and whether they have ceased. " +
    "Required for UK AML beneficial ownership checks.",
  inputSchema: {
    type: "object",
    properties: {
      company_number: {
        type: "string",
        description:
          "Companies House company number (e.g. 01234567 or SC123456). " +
          "Use verify_uk_company first if you only have a company name.",
      },
    },
    required: ["company_number"],
  },
} as const;

// ── runners ───────────────────────────────────────────────────────────────────

export async function runVerifyUkCompany(
  args: { q: string },
  config: ApitierConfig
): Promise<string> {
  const data = await apitierGet(
    `${config.baseUrls.leadAgent}/company`,
    { q: args.q },
    config.keys.leadAgent!
  );
  return JSON.stringify(data, null, 2);
}

export async function runGetCompanyPsc(
  args: { company_number: string },
  config: ApitierConfig
): Promise<string> {
  const data = await apitierGet(
    `${config.baseUrls.leadAgent}/company/psc`,
    { company_number: args.company_number },
    config.keys.leadAgent!
  );
  return JSON.stringify(data, null, 2);
}
