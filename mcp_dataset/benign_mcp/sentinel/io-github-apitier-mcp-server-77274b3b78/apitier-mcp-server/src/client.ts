export interface ApiResponse {
  status: number;
  message: string;
  [key: string]: unknown;
}

// Each API service has its own usage plan and therefore its own API key.
// Keys are optional — if absent, the corresponding tools are not registered.
export interface ServiceKeys {
  email?: string;
  phone?: string;
  vat?: string;
  postcode?: string;
  pincode?: string;
  barcode?: string;
  convertData?: string;
  userAgent?: string;
  leadAgent?: string;
}

export interface ServiceUrls {
  email: string;
  phone: string;
  vat: string;
  postcode: string;
  pincode: string;
  barcode: string;
  convertData: string;
  userAgent: string;
  leadAgent: string;
}

export interface ApitierConfig {
  keys: ServiceKeys;
  baseUrls: ServiceUrls;
}

const BASE_URLS: ServiceUrls = {
  email:       "https://email.apitier.com/v1",
  phone:       "https://phone.apitier.com/v1",
  vat:         "https://vat.apitier.com/v1",
  postcode:    "https://postcode.apitier.com/v1",
  pincode:     "https://pincode.apitier.com/v1",
  barcode:     "https://barcode.apitier.com/v1",
  convertData: "https://data.apitier.com",
  userAgent:   "https://useragent.apitier.com/v1",
  leadAgent:     "https://lead.apitier.com/v1",
};

export function getConfig(): ApitierConfig {
  const keys: ServiceKeys = {
    email:       process.env.APITIER_EMAIL_KEY,
    phone:       process.env.APITIER_PHONE_KEY,
    vat:         process.env.APITIER_VAT_KEY,
    postcode:    process.env.APITIER_POSTCODE_KEY,
    pincode:     process.env.APITIER_PINCODE_KEY,
    barcode:     process.env.APITIER_BARCODE_KEY,
    convertData: process.env.APITIER_CONVERT_DATA_KEY,
    userAgent:   process.env.APITIER_USERAGENT_KEY,
    leadAgent:     process.env.APITIER_LEAD_AGENT_KEY,
  };

  for (const k of Object.keys(keys) as (keyof ServiceKeys)[]) {
    if (!keys[k]) delete keys[k];
  }

  if (Object.keys(keys).length === 0) {
    throw new Error(
      "No APITier API keys configured.\n" +
      "Set APITIER_MCP_KEY (unified portal key) or individual service keys:\n" +
      "APITIER_POSTCODE_KEY, APITIER_EMAIL_KEY, APITIER_PHONE_KEY, etc."
    );
  }

  return { keys, baseUrls: BASE_URLS };
}

/**
 * Resolves a unified MCP token to per-service keys by calling the portal API.
 * Called once at server startup — result is held in memory for the process lifetime.
 */
export async function resolvePortalKeys(mcpToken: string): Promise<ApitierConfig> {
  const portalUrl = process.env.APITIER_PORTAL_URL
    ?? "https://f99m9uxp61.execute-api.eu-west-1.amazonaws.com/prod";
  const portalApiKey = process.env.APITIER_PORTAL_API_KEY
    ?? "DL4teabVaSaRXTwFEi1rE5AB9ZRFfCxc1xASF1tg";

  const url = `${portalUrl}/mcp/keys?token=${encodeURIComponent(mcpToken)}`;
  const response = await fetch(url, { method: "GET", headers: { Accept: "application/json", "x-api-key": portalApiKey } });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(`Portal key resolution failed (${response.status}): ${body}`);
  }

  const { services } = await response.json() as { services: Record<string, string> };

  if (!services || Object.keys(services).length === 0) {
    throw new Error(
      "No subscribed services found for this MCP token.\n" +
      "Subscribe to at least one APITier service at https://apitier.com"
    );
  }

  // Cast: the portal returns keys using the same names as ServiceKeys
  const keys = services as unknown as ServiceKeys;

  return { keys, baseUrls: BASE_URLS };
}

export async function apitierGet(
  url: string,
  params: Record<string, string>,
  apiKey: string
): Promise<ApiResponse> {
  const searchParams = new URLSearchParams({ ...params, "x-api-key": apiKey });
  const response = await fetch(`${url}?${searchParams.toString()}`, {
    method: "GET",
    headers: { Accept: "application/json" },
  });

  const data = (await response.json()) as ApiResponse;

  if (!response.ok) {
    throw new Error(`APITier error ${response.status}: ${data.message ?? "Unknown error"}`);
  }

  return data;
}

export async function apitierPost(
  url: string,
  body: unknown,
  apiKey: string,
  acceptBinary = false,
  rawBody = false
): Promise<ApiResponse | string> {
  const isRaw = rawBody && typeof body === "string";
  const response = await fetch(`${url}?x-api-key=${apiKey}`, {
    method: "POST",
    headers: {
      "Content-Type": isRaw ? "text/plain" : "application/json",
      Accept: acceptBinary ? "image/png" : "application/json",
    },
    body: isRaw ? (body as string) : JSON.stringify(body),
  });

  if (acceptBinary) {
    const buffer = await response.arrayBuffer();
    return Buffer.from(buffer).toString("base64");
  }

  const data = (await response.json()) as ApiResponse;

  if (!response.ok) {
    throw new Error(`APITier error ${response.status}: ${data.message ?? "Unknown error"}`);
  }

  return data;
}
