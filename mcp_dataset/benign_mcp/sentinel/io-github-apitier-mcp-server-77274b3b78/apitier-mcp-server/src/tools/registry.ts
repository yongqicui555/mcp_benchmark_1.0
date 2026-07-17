import type { Tool } from "@modelcontextprotocol/sdk/types.js";
import type { ApitierConfig, ServiceKeys } from "../client.js";
import {
  validateEmailTool,    runValidateEmail,
  validatePhoneTool,    runValidatePhone,
  validateVatTool,      runValidateVat,
  ukPostcodeLookupTool, runUkPostcodeLookup,
  verifyUkAddressTool,  runVerifyUkAddress,
  lookupUprnTool,       runLookupUprn,
  indiaPincodeTool,     runIndiaPincodeLookup,
  generateBarcodeTool,  runGenerateBarcode,
  generateQrCodeTool,   runGenerateQrCode,
  convertDataTool,      runConvertData,
  validateSortCodeTool, runValidateSortCode,
  verifyUkCompanyTool,  runVerifyUkCompany,
  getCompanyPscTool,    runGetCompanyPsc,
  kycOnboardTool,       runKycOnboard,
} from "./index.js";

type ToolRunner = (args: Record<string, unknown>, config: ApitierConfig) => Promise<string> | string;

interface RegistryEntry {
  tool: Tool;
  runner: ToolRunner;
}

// Maps each service subscription key to the tools it enables.
// To add a new tool: add a new entry here — no changes to src/index.ts or lambda/mcp.js required.
const SERVICE_REGISTRY: Partial<Record<keyof ServiceKeys, RegistryEntry[]>> = {
  email: [
    {
      tool: validateEmailTool as unknown as Tool,
      runner: (args, cfg) => runValidateEmail(args as { email: string }, cfg),
    },
  ],
  phone: [
    {
      tool: validatePhoneTool as unknown as Tool,
      runner: (args, cfg) => runValidatePhone(args as { phone: string }, cfg),
    },
  ],
  vat: [
    {
      tool: validateVatTool as unknown as Tool,
      runner: (args, cfg) => runValidateVat(args as { vatNumber: string }, cfg),
    },
  ],
  postcode: [
    {
      tool: ukPostcodeLookupTool as unknown as Tool,
      runner: (args, cfg) => runUkPostcodeLookup(args as { postcode: string }, cfg),
    },
    {
      tool: verifyUkAddressTool as unknown as Tool,
      runner: (args, cfg) => runVerifyUkAddress(args as { postcode: string; query?: string }, cfg),
    },
    {
      tool: lookupUprnTool as unknown as Tool,
      runner: (args, cfg) => runLookupUprn(args as { udprn: string }, cfg),
    },
  ],
  pincode: [
    {
      tool: indiaPincodeTool as unknown as Tool,
      runner: (args, cfg) => runIndiaPincodeLookup(args as { pincode: string }, cfg),
    },
  ],
  barcode: [
    {
      tool: generateBarcodeTool as unknown as Tool,
      runner: (args, cfg) => runGenerateBarcode(args as Parameters<typeof runGenerateBarcode>[0], cfg),
    },
    {
      tool: generateQrCodeTool as unknown as Tool,
      runner: (args, cfg) => runGenerateQrCode(args as Parameters<typeof runGenerateQrCode>[0], cfg),
    },
  ],
  convertData: [
    {
      tool: convertDataTool as unknown as Tool,
      runner: (args, cfg) => runConvertData(args as Parameters<typeof runConvertData>[0], cfg),
    },
  ],
  leadAgent: [
    {
      tool: verifyUkCompanyTool as unknown as Tool,
      runner: (args, cfg) => runVerifyUkCompany(args as { q: string }, cfg),
    },
    {
      tool: getCompanyPscTool as unknown as Tool,
      runner: (args, cfg) => runGetCompanyPsc(args as { company_number: string }, cfg),
    },
  ],
};

// Sort code is always available — no subscription key required.
const ALWAYS_ON: RegistryEntry[] = [
  {
    tool: validateSortCodeTool as unknown as Tool,
    runner: (args) => runValidateSortCode(args as { sortCode: string; accountNumber?: string }),
  },
];

// KYC onboarding composite tool — requires all three data services.
const KYC_COMPOSITE: RegistryEntry = {
  tool: kycOnboardTool as unknown as Tool,
  runner: (args, cfg) => runKycOnboard(
    args as { company_name: string; vat_number?: string; postcode?: string },
    cfg
  ),
};

function collectEntries(config: ApitierConfig): RegistryEntry[] {
  const entries = [...ALWAYS_ON];
  for (const key of Object.keys(config.keys) as (keyof ServiceKeys)[]) {
    entries.push(...(SERVICE_REGISTRY[key] ?? []));
  }
  // Composite tool appears only when all three required services are subscribed.
  if (config.keys.vat && config.keys.leadAgent && config.keys.postcode) {
    entries.push(KYC_COMPOSITE);
  }
  return entries;
}

export function buildActiveTools(config: ApitierConfig): Tool[] {
  return collectEntries(config).map((e) => e.tool);
}

export function buildRunners(config: ApitierConfig): Map<string, ToolRunner> {
  const map = new Map<string, ToolRunner>();
  for (const { tool, runner } of collectEntries(config)) {
    map.set(tool.name, runner);
  }
  return map;
}
