import type { ApitierConfig } from "../client.js";
import { runValidateVat } from "./validate-vat.js";
import { runVerifyUkCompany, runGetCompanyPsc } from "./uk-company.js";
import { runVerifyUkAddress } from "./uk-address-uprn.js";

export const kycOnboardTool = {
  name: "kyc_onboard_uk",
  geography: ["GB"] as const,
  domain: "kyc" as const,
  description:
    "Run a full UK business onboarding check in one call. " +
    "Validates the VAT number against HMRC/EU VIES, verifies the company on Companies House, " +
    "retrieves Persons with Significant Control (PSC / beneficial owners), " +
    "and confirms the registered address against Royal Mail PAF. " +
    "Returns a structured decision (PASS / REVIEW / FAIL), a risk score (0–100), " +
    "a list of risk flags, and the full data bundle from each check. " +
    "Requires postcode, vat, and leadAgent subscriptions.",
  inputSchema: {
    type: "object",
    properties: {
      company_name: {
        type: "string",
        description:
          "Registered company name or Companies House number " +
          "(e.g. 'Vodafone Group Plc' or '01833679'). " +
          "Used to look up the company and retrieve its registered address postcode.",
      },
      vat_number: {
        type: "string",
        description:
          "UK VAT number to validate (e.g. GB123456789). " +
          "Optional — VAT check is skipped if not supplied.",
      },
      postcode: {
        type: "string",
        description:
          "Registered address postcode for PAF address verification (e.g. EC1A 1BB). " +
          "If omitted, address check is skipped.",
      },
    },
    required: ["company_name"],
  },
} as const;

interface CheckResult {
  status: string;
  data: unknown;
}

interface KycResult {
  decision: "PASS" | "REVIEW" | "FAIL";
  risk_score: number;
  flags: string[];
  checks: {
    company: CheckResult;
    psc: CheckResult;
    vat: CheckResult | null;
    address: CheckResult | null;
  };
}

export async function runKycOnboard(
  args: { company_name: string; vat_number?: string; postcode?: string },
  config: ApitierConfig
): Promise<string> {
  const flags: string[] = [];

  // Company lookup is always first — we need the company number for PSC
  const companyRaw = await runVerifyUkCompany({ q: args.company_name }, config);
  const company = JSON.parse(companyRaw);

  const companyStatus: string =
    company?.result?.company_status ??
    company?.company_status ??
    "";

  if (companyStatus && companyStatus !== "active") {
    flags.push(`COMPANY_${companyStatus.toUpperCase().replace(/[^A-Z0-9]/g, "_")}`);
  }
  if (!companyStatus) {
    flags.push("COMPANY_NOT_FOUND");
  }

  // PSC, VAT, address can run in parallel once we have the company number
  const companyNumber: string | undefined =
    company?.result?.company_number ??
    company?.company_number;

  const parallelTasks: Promise<[string, unknown]>[] = [];

  // PSC check
  if (companyNumber) {
    parallelTasks.push(
      runGetCompanyPsc({ company_number: companyNumber }, config)
        .then((raw) => ["psc", JSON.parse(raw)] as [string, unknown])
        .catch((err) => ["psc_error", { error: String(err) }] as [string, unknown])
    );
  }

  // VAT check
  if (args.vat_number && config.keys.vat) {
    parallelTasks.push(
      runValidateVat({ vatNumber: args.vat_number }, config)
        .then((raw) => ["vat", JSON.parse(raw)] as [string, unknown])
        .catch((err) => ["vat_error", { error: String(err) }] as [string, unknown])
    );
  }

  // Address check
  if (args.postcode && config.keys.postcode) {
    parallelTasks.push(
      runVerifyUkAddress({ postcode: args.postcode }, config)
        .then((raw) => ["address", JSON.parse(raw)] as [string, unknown])
        .catch((err) => ["address_error", { error: String(err) }] as [string, unknown])
    );
  }

  const parallelResults = await Promise.all(parallelTasks);
  const resultMap = new Map<string, unknown>(parallelResults);

  // Evaluate PSC
  const pscData = resultMap.get("psc") ?? resultMap.get("psc_error");
  const pscItems = (pscData as { result?: unknown[]; items?: unknown[] })?.result ??
                   (pscData as { items?: unknown[] })?.items ?? [];
  const pscStatus = Array.isArray(pscItems) && pscItems.length > 0 ? "found" : "not_found";
  if (!companyNumber || pscStatus === "not_found") {
    flags.push("NO_PSC_FOUND");
  }

  // Evaluate VAT
  let vatResult: CheckResult | null = null;
  if (resultMap.has("vat") || resultMap.has("vat_error")) {
    const vatData = resultMap.get("vat") ?? resultMap.get("vat_error");
    const vatValid =
      (vatData as { valid?: boolean })?.valid ??
      (vatData as { result?: { valid?: boolean } })?.result?.valid;
    vatResult = { status: vatValid ? "valid" : "invalid", data: vatData };
    if (!vatValid) flags.push("VAT_INVALID");
  }

  // Evaluate address
  let addressResult: CheckResult | null = null;
  if (resultMap.has("address") || resultMap.has("address_error")) {
    const addressData = resultMap.get("address") ?? resultMap.get("address_error");
    const addressCount =
      (addressData as { result?: { addresses?: unknown[] } })?.result?.addresses?.length ?? 0;
    addressResult = {
      status: addressCount > 0 ? "verified" : "not_found",
      data: addressData,
    };
    if (addressCount === 0) flags.push("ADDRESS_NOT_FOUND");
  }

  // Score: start at 100, deduct per flag
  const FLAG_WEIGHTS: Record<string, number> = {
    COMPANY_NOT_FOUND: 60,
    NO_PSC_FOUND: 20,
    VAT_INVALID: 25,
    ADDRESS_NOT_FOUND: 15,
  };
  const deduction = flags.reduce(
    (sum, f) => sum + (FLAG_WEIGHTS[f] ?? 20),
    0
  );
  const riskScore = Math.max(0, 100 - deduction);
  const decision: "PASS" | "REVIEW" | "FAIL" =
    riskScore >= 80 ? "PASS" : riskScore >= 50 ? "REVIEW" : "FAIL";

  const result: KycResult = {
    decision,
    risk_score: riskScore,
    flags,
    checks: {
      company: { status: companyStatus || "not_found", data: company },
      psc: { status: pscStatus, data: pscData },
      vat: vatResult,
      address: addressResult,
    },
  };

  return JSON.stringify(result, null, 2);
}
