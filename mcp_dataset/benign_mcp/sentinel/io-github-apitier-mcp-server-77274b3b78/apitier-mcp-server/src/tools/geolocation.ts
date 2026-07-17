// Stashed — not yet released. Wire into index.ts + client.ts when ready to ship.
import { apitierGet } from "../client.js";

const GEO_BASE = "https://geo.apitier.com/v1";

// Minimal config shape used by this module only
interface GeoConfig { geoKey: string }

// ── geocode_address ───────────────────────────────────────────────────────────

export const geocodeAddressTool = {
  name: "geocode_address",
  description:
    "Convert a free-text address into coordinates and a structured canonical address. " +
    "Global coverage — 120+ countries (OpenStreetMap / Geoapify). " +
    "Returns displayName, line1, town, county, postcode, country, countryCode, " +
    "lat/lng, result type, and confidence score. " +
    "Use countrycode to restrict results to a specific country.",
  inputSchema: {
    type: "object",
    properties: {
      address: {
        type: "string",
        description: "Free-text address to geocode (e.g. '10 Downing Street, London' or '1600 Amphitheatre Parkway, Mountain View, CA').",
      },
      countrycode: {
        type: "string",
        description: "ISO 3166-1 alpha-2 country code to restrict results (e.g. 'gb', 'us', 'de'). Omit for global search.",
      },
      limit: {
        type: "number",
        description: "Max results to return (1–10, default 1).",
      },
      lang: {
        type: "string",
        description: "ISO 639-1 language code for result labels (default 'en').",
      },
    },
    required: ["address"],
  },
} as const;

// ── autocomplete_address ──────────────────────────────────────────────────────

export const autocompleteAddressTool = {
  name: "autocomplete_address",
  description:
    "Get ranked address suggestions for a partial address string. " +
    "Global coverage — 120+ countries (OpenStreetMap / Geoapify). " +
    "Designed for real-time typeahead input fields. " +
    "Use countrycode to restrict to a specific country, bias to prefer one country without hard-filtering.",
  inputSchema: {
    type: "object",
    properties: {
      text: {
        type: "string",
        description: "Partial address string to autocomplete (e.g. '10 Down' or 'Rue de la P'). Minimum 2 characters.",
      },
      countrycode: {
        type: "string",
        description: "ISO 3166-1 alpha-2 to restrict results to one country (e.g. 'gb', 'us').",
      },
      bias: {
        type: "string",
        description: "ISO 3166-1 alpha-2 to prefer results from this country without hard-filtering — useful for international checkout forms.",
      },
      limit: {
        type: "number",
        description: "Max suggestions to return (1–10, default 5).",
      },
      lang: {
        type: "string",
        description: "ISO 639-1 language code for result labels (default 'en').",
      },
    },
    required: ["text"],
  },
} as const;

// ── reverse_geocode ───────────────────────────────────────────────────────────

export const reverseGeocodeTool = {
  name: "reverse_geocode",
  description:
    "Convert GPS coordinates (latitude/longitude) into a structured address. " +
    "Global coverage — 120+ countries (OpenStreetMap / Geoapify). " +
    "Returns displayName, line1, town, county, postcode, country, countryCode, result type, and confidence score.",
  inputSchema: {
    type: "object",
    properties: {
      lat: {
        type: "number",
        description: "Latitude (-90 to 90), e.g. 51.5034.",
      },
      lng: {
        type: "number",
        description: "Longitude (-180 to 180), e.g. -0.1276.",
      },
      lang: {
        type: "string",
        description: "ISO 639-1 language code for result labels (default 'en').",
      },
    },
    required: ["lat", "lng"],
  },
} as const;

// ── geolocate_ip ──────────────────────────────────────────────────────────────

export const geolocateIpTool = {
  name: "geolocate_ip",
  description:
    "Geolocate an IPv4 or IPv6 address — returns country, region, city, coordinates, timezone, and ISP. " +
    "Use to detect country mismatches with a shipping/billing address (fraud signal) " +
    "or to pre-fill address fields based on the visitor's location.",
  inputSchema: {
    type: "object",
    properties: {
      ip: {
        type: "string",
        description: "IPv4 or IPv6 address to geolocate (e.g. '8.8.8.8').",
      },
    },
    required: ["ip"],
  },
} as const;

// ── search_nearby_places ──────────────────────────────────────────────────────

export const searchNearbyPlacesTool = {
  name: "search_nearby_places",
  description:
    "Find points of interest (POIs) near a coordinate — restaurants, hospitals, banks, hotels, and more. " +
    "Global coverage (OpenStreetMap / Geoapify). Returns name, address, distance in metres, " +
    "opening hours, website, and contact details. " +
    "Filter by category (e.g. 'catering.restaurant', 'healthcare', 'service', 'accommodation').",
  inputSchema: {
    type: "object",
    properties: {
      lat: {
        type: "number",
        description: "Centre latitude for the search (-90 to 90).",
      },
      lng: {
        type: "number",
        description: "Centre longitude for the search (-180 to 180).",
      },
      radius: {
        type: "number",
        description: "Search radius in metres (default 1000, max 50000).",
      },
      categories: {
        type: "string",
        description:
          "Comma-separated Geoapify category codes to filter by. " +
          "Common values: accommodation, catering, catering.restaurant, catering.cafe, catering.bar, " +
          "commercial, commercial.supermarket, healthcare, tourism, public_transport, service, sport, education. " +
          "Omit to return all place types.",
      },
      limit: {
        type: "number",
        description: "Max results to return (1–100, default 20).",
      },
      lang: {
        type: "string",
        description: "ISO 639-1 language code for result labels (default 'en').",
      },
    },
    required: ["lat", "lng"],
  },
} as const;

// ── runners ───────────────────────────────────────────────────────────────────

export async function runGeocodeAddress(
  args: { address: string; countrycode?: string; limit?: number; lang?: string },
  config: GeoConfig
): Promise<string> {
  const params: Record<string, string> = { address: args.address };
  if (args.countrycode) params.countrycode = args.countrycode;
  if (args.limit)       params.limit       = String(args.limit);
  if (args.lang)        params.lang        = args.lang;
  const data = await apitierGet(`${GEO_BASE}/geolocate`, params, config.geoKey);
  return JSON.stringify(data, null, 2);
}

export async function runAutocompleteAddress(
  args: { text: string; countrycode?: string; bias?: string; limit?: number; lang?: string },
  config: GeoConfig
): Promise<string> {
  const params: Record<string, string> = { text: args.text };
  if (args.countrycode) params.countrycode = args.countrycode;
  if (args.bias)        params.bias        = args.bias;
  if (args.limit)       params.limit       = String(args.limit);
  if (args.lang)        params.lang        = args.lang;
  const data = await apitierGet(`${GEO_BASE}/autocomplete`, params, config.geoKey);
  return JSON.stringify(data, null, 2);
}

export async function runReverseGeocode(
  args: { lat: number; lng: number; lang?: string },
  config: GeoConfig
): Promise<string> {
  const params: Record<string, string> = { lat: String(args.lat), lng: String(args.lng) };
  if (args.lang) params.lang = args.lang;
  const data = await apitierGet(`${GEO_BASE}/reverse`, params, config.geoKey);
  return JSON.stringify(data, null, 2);
}

export async function runGeolocateIp(
  args: { ip: string },
  config: GeoConfig
): Promise<string> {
  const data = await apitierGet(`${GEO_BASE}/ip`, { address: args.ip }, config.geoKey);
  return JSON.stringify(data, null, 2);
}

export async function runSearchNearbyPlaces(
  args: { lat: number; lng: number; radius?: number; categories?: string; limit?: number; lang?: string },
  config: GeoConfig
): Promise<string> {
  const params: Record<string, string> = { lat: String(args.lat), lng: String(args.lng) };
  if (args.radius)     params.radius     = String(args.radius);
  if (args.categories) params.categories = args.categories;
  if (args.limit)      params.limit      = String(args.limit);
  if (args.lang)       params.lang       = args.lang;
  const data = await apitierGet(`${GEO_BASE}/places`, params, config.geoKey);
  return JSON.stringify(data, null, 2);
}
