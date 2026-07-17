#!/usr/bin/env node

/**
 * MAP — READ module: Merchant Key (the decoder)
 *
 * Reads ANY product URL on the open web and returns ONE clean shape (CleanRead):
 * what it is, who sells it, what it costs, is it in stock, and the one thing a
 * model fumbles — can an agent buy this itself?
 *
 * Teacher, not butler. It reads, explains, and shuts up. It never signs, pays,
 * holds keys, or stores cards. For *paying*, it points the agent at this kit's
 * own wallet lessons (the PAY module).
 *
 * Rail-agnostic by design; conservative in detection. The CleanRead schema can
 * describe ANY agent-payable rail (x402, ap2, acp, coinbase, stripe, http-json,
 * walletconnect, human_checkout, unknown). v1.0.x detects x402 reliably;
 * ap2/acp/ucp detectors are on the v1.1 roadmap. Other rails remain reserved
 * schema values. MAP never infers a rail from branding, checkout buttons,
 * script tags, marketing copy, or platform names; if no verifiable
 * machine-readable rail is detected, the outcome is human_checkout.
 *
 * False human_checkout is acceptable in v1. False autonomous is dangerous and
 * unacceptable — that is why detection stays conservative.
 *
 * Pure module: no MCP/server code here. The engine (decodeMerchant, parseSurface)
 * is reused by the PUBLISH module. index.js wires the tools into one server.
 *
 * By Lisa Maraventano, with Claude. Clarksdale, Mississippi. Dual-licensed — see LICENSE.
 */

const SCHEMA_VERSION = "map/v1";
const FETCH_TIMEOUT_MS = 15000;
const USER_AGENT = "MAP/1.0 (Maraventano Agent Protocol; open-web merchant decoder; reads, never pays)";

const PAY_HUMAN =
  "Human checkout only. No agent-payable rail was detected — a human (or human-operated checkout) completes this purchase.";
const PAY_X402 =
  "Agent-payable via x402. Re-fetch the live challenge and pay with your own wallet — see this kit's wallet lessons: read-this-challenge, then how-do-i-pay. Merchant Key reads; it never signs or pays.";

// Known USDC token contracts. We report the real quote currency ("USDC"), not
// a relabel to "USD" — payable.rail already carries the on-chain truth, and USDC
// is 1:1 USD by design so an agent sorts the two together anyway.
const USDC_ASSETS = new Set([
  "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913".toLowerCase(), // Base
  "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48".toLowerCase(), // Ethereum
  "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v".toLowerCase(), // Solana
]);

// ---------------------------------------------------------------------------
// CleanRead shape — FIVE things + a verdict. Always this shape. Never omit.
// ---------------------------------------------------------------------------

function blankRead(sourceUrl) {
  return {
    schemaVersion: SCHEMA_VERSION,
    sourceUrl,
    what: null, // name + short identity, ONE string
    who: null, // seller
    price: { total: null, currency: null }, // total if knowable; null if not
    available: "unknown", // "in_stock" | "out_of_stock" | "unknown"
    // rail (rail-agnostic schema): "x402" | "ap2" | "acp" | "coinbase" |
    // "stripe" | "http-json" | "walletconnect" | "human_checkout" | "unknown".
    // v1.0.x DETECTS "x402" only; ap2/acp/ucp detectors on the v1.1 roadmap.
    // Non-x402 reads as "human_checkout".
    payable: { rail: "unknown", payTo: null, instruction: PAY_HUMAN },
    outcome: "unreadable", // "autonomous" | "human_checkout" | "unreadable"
    reason: null, // why, when not autonomous
    cuts: [], // optional 1-line actionable gaps
  };
}

// ---------------------------------------------------------------------------
// Small helpers
// ---------------------------------------------------------------------------

function sellerFromUrl(url) {
  try {
    return new URL(url).hostname.replace(/^www\./i, "");
  } catch {
    return null;
  }
}

function round2(n) {
  return Math.round(n * 100) / 100;
}

function decodeEntities(s) {
  if (s == null) return s;
  return String(s)
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&#0*39;|&apos;/g, "'")
    .replace(/&#x27;/gi, "'")
    .replace(/&nbsp;/g, " ")
    .replace(/&#(\d+);/g, (_, d) => String.fromCodePoint(Number(d)))
    .trim();
}

// ---------------------------------------------------------------------------
// x402 reading — logic mirrors First Dollar's read-this-challenge
// (tryParseChallenge / network family / base-unit math), narrowed to a CleanRead.
// ---------------------------------------------------------------------------

function tryParseChallenge(input) {
  if (!input) return null;
  const raw = String(input).trim();
  // header value form (base64-encoded JSON)
  try {
    const decoded = Buffer.from(raw, "base64").toString("utf-8");
    if (decoded.trim().startsWith("{")) return JSON.parse(decoded);
  } catch {}
  // response body form (raw JSON)
  try {
    if (raw.startsWith("{")) return JSON.parse(raw);
  } catch {}
  return null;
}

// A parsed challenge only counts as "usable" if it carries a non-empty accepts[]
// array. Some servers return a truthy-but-empty body like `{}` or `{"error":...}`
// while putting the real x402 challenge in the PAYMENT-REQUIRED header — without
// this guard the body would short-circuit a `||` selector and the header would
// be silently ignored.
function usableChallenge(ch) {
  return ch && Array.isArray(ch.accepts) && ch.accepts.length ? ch : null;
}

function networkFamily(network) {
  if (!network) return "unknown";
  if (network.startsWith("eip155:")) return "evm";
  if (network.startsWith("solana:")) return "solana";
  return "unknown";
}

// Prefer Base (highest x402 coverage, First Dollar's default chain), then any
// EVM, then whatever is first. The live challenge is re-read at pay time, so
// this is a pointer, not the authoritative destination.
function pickPrimaryAccept(accepts) {
  if (!Array.isArray(accepts) || !accepts.length) return null;
  return (
    accepts.find((a) => a && a.network === "eip155:8453") ||
    accepts.find((a) => a && networkFamily(a.network) === "evm") ||
    accepts[0]
  );
}

function payToFromAccept(a) {
  if (!a || !a.payTo) return null;
  const fam = networkFamily(a.network);
  const kind =
    fam === "evm" ? "evm-address" : fam === "solana" ? "solana-address" : "address";
  return { kind, value: a.payTo, chain: a.network || null };
}

function isUsdc(a) {
  if (!a) return false;
  if (a.asset && USDC_ASSETS.has(String(a.asset).toLowerCase())) return true;
  if (a.extra && a.extra.name === "USD Coin") return true;
  return false;
}

function currencyFromAccept(a) {
  if (!a) return null;
  if (isUsdc(a)) return "USDC";
  if (a.extra && a.extra.name) return a.extra.name; // informative label; total stays null
  return null;
}

function buildX402Read(read, ch) {
  const accepts = Array.isArray(ch.accepts) ? ch.accepts : [];
  const a = pickPrimaryAccept(accepts);

  // what — prefer the resource description; fall back to the bazaar example title.
  const desc = ch.resource && ch.resource.description;
  const ex =
    ch.extensions &&
    ch.extensions.bazaar &&
    ch.extensions.bazaar.info &&
    ch.extensions.bazaar.info.output &&
    ch.extensions.bazaar.info.output.example;
  if (desc) {
    read.what = decodeEntities(desc);
  } else if (ex && ex.title) {
    read.what = decodeEntities(ex.content ? `${ex.title} — ${ex.content}` : ex.title);
  } else {
    read.what = read.who ? `${read.who} item` : null;
  }

  // price — only decode when the asset is KNOWN USDC (6 base-unit decimals).
  // We never guess decimals for an unknown token; unknown asset → total null + a
  // cut, which degrades the verdict to human_checkout (a false price is worse).
  if (a && a.amount != null) {
    if (isUsdc(a)) {
      const n = Number(a.amount);
      const total = Number.isFinite(n) ? round2(n / 1e6) : null;
      read.price = { total, currency: total != null ? "USDC" : null };
    } else {
      read.price = { total: null, currency: currencyFromAccept(a) };
      read.cuts.push("non-USDC x402 asset; price not decoded (token decimals unknown)");
    }
  }

  // A live x402 challenge means the merchant will sell it right now → in stock.
  read.available = "in_stock";

  read.payable = { rail: "x402", payTo: payToFromAccept(a), instruction: PAY_X402 };

  // Verdict: machine rail + known price + not out-of-stock → autonomous.
  if (read.price.total != null && read.available !== "out_of_stock") {
    read.outcome = "autonomous";
    read.reason = null;
  } else {
    read.outcome = "human_checkout";
    read.reason =
      "x402 rail present but price could not be totaled from the challenge";
    read.cuts.push("price not found in challenge");
  }
  return read;
}

// ---------------------------------------------------------------------------
// HTML / JSON product reading — JSON-LD first, then OpenGraph.
// ---------------------------------------------------------------------------

function extractJsonLd(html) {
  const out = [];
  const re =
    /<script\b[^>]*type=["']application\/ld\+json["'][^>]*>([\s\S]*?)<\/script>/gi;
  let m;
  while ((m = re.exec(html))) {
    try {
      out.push(JSON.parse(m[1].trim()));
    } catch {
      // malformed block — skip, not fatal
    }
  }
  return out;
}

function isProductType(t) {
  const types = Array.isArray(t) ? t : [t];
  return types.some((x) => typeof x === "string" && /product/i.test(x));
}

function collectProducts(node, acc) {
  if (!node || typeof node !== "object") return;
  if (Array.isArray(node)) {
    node.forEach((n) => collectProducts(n, acc));
    return;
  }
  if (isProductType(node["@type"]) && node.offers) acc.push(node);
  for (const k of Object.keys(node)) collectProducts(node[k], acc);
}

function readOffer(offers) {
  const o = Array.isArray(offers) ? offers[0] : offers;
  if (!o || typeof o !== "object")
    return { price: null, currency: null, availability: null };
  let price = o.price != null ? o.price : o.lowPrice != null ? o.lowPrice : null;
  price = price != null ? Number(price) : null;
  return {
    price: Number.isFinite(price) ? round2(price) : null,
    currency: o.priceCurrency || null,
    availability: o.availability || null,
  };
}

function mapAvailability(av) {
  if (!av) return "unknown";
  const s = String(av).toLowerCase();
  if (/(^|\/|_)instock|in_stock|onlineonly|limitedavailability|presale|backorder/.test(s))
    return "in_stock";
  if (/outofstock|out_of_stock|soldout|discontinued/.test(s)) return "out_of_stock";
  return "unknown";
}

function metaMap(html) {
  const map = {};
  const re = /<meta\b[^>]*>/gi;
  let m;
  while ((m = re.exec(html))) {
    const tag = m[0];
    const key = (tag.match(/(?:property|name)=["']([^"']+)["']/i) || [])[1];
    const val = (tag.match(/content=["']([^"']*)["']/i) || [])[1];
    if (key) map[key.toLowerCase()] = decodeEntities(val || "");
  }
  return map;
}

// Returns extracted product fields from an already-fetched surface (no network).
// Pure on purpose: same engine could later back an offline explain tool.
function parseSurface({ contentType, body }) {
  const ctype = (contentType || "").toLowerCase();
  const found = { what: null, price: null, currency: null, available: "unknown" };

  // If the URL itself returns JSON, try schema.org-ish / common product keys.
  if (ctype.includes("application/json")) {
    try {
      const j = JSON.parse(body);
      const acc = [];
      collectProducts(j, acc);
      if (acc.length) {
        const p = acc[0];
        const off = readOffer(p.offers);
        found.what = decodeEntities(p.name) || null;
        found.price = off.price;
        found.currency = off.currency;
        found.available = mapAvailability(off.availability);
        return found;
      }
      // bare-ish product object
      if (j && typeof j === "object") {
        found.what = decodeEntities(j.name || j.title) || null;
        const price = j.price != null ? Number(j.price) : null;
        found.price = Number.isFinite(price) ? round2(price) : null;
        found.currency = j.priceCurrency || j.currency || null;
      }
    } catch {}
    return found;
  }

  // HTML path: JSON-LD Product → OpenGraph.
  const blocks = extractJsonLd(body);
  const products = [];
  for (const b of blocks) collectProducts(b, products);
  if (products.length) {
    const p = products[0];
    const off = readOffer(p.offers);
    found.what = decodeEntities(p.name) || null;
    found.price = off.price;
    found.currency = off.currency;
    found.available = mapAvailability(off.availability);
  }

  // Fill gaps from OpenGraph / product meta tags.
  const meta = metaMap(body);
  if (!found.what) found.what = meta["og:title"] || null;
  if (found.price == null) {
    const amt = meta["product:price:amount"] || meta["og:price:amount"];
    const n = amt != null ? Number(amt) : null;
    if (Number.isFinite(n)) found.price = round2(n);
  }
  if (!found.currency)
    found.currency =
      meta["product:price:currency"] || meta["og:price:currency"] || null;
  if (found.available === "unknown") {
    const av = meta["product:availability"] || meta["og:availability"];
    if (av) found.available = mapAvailability(av);
  }

  return found;
}

function applySurface(read, found) {
  read.what = found.what || null;
  read.price = { total: found.price != null ? found.price : null, currency: found.currency || null };
  read.available = found.available || "unknown";

  const hasIdentity = !!read.what;
  const hasPrice = read.price.total != null;

  if (!hasIdentity && !hasPrice) {
    read.outcome = "unreadable";
    read.reason =
      "No product data found: no JSON-LD Product, no OpenGraph price, and no x402 payment challenge. (No headless browser in v1, so JS-only pages read as unreadable.)";
    read.cuts.push("no structured product data");
    return read;
  }

  // Readable, but no agent-payable rail was DETECTED → human checkout.
  // The schema is rail-agnostic, but v1 only detects x402; we never infer
  // ap2/acp/coinbase/stripe/walletconnect from branding, buttons, scripts, or
  // platform names. A false human_checkout is fine; a false autonomous is not.
  read.outcome = "human_checkout";
  read.payable = { rail: "human_checkout", payTo: null, instruction: PAY_HUMAN };
  read.reason = "Readable product page, but no agent-payable rail (e.g. x402) was found.";
  read.cuts.push("no x402 rail");
  if (!hasPrice) read.cuts.push("price not found");
  if (!hasIdentity) read.cuts.push("product name not found");
  return read;
}

// ---------------------------------------------------------------------------
// Fetch (read-only GET, manual redirect) + orchestration
// ---------------------------------------------------------------------------

async function fetchSurface(url) {
  return fetch(url, {
    method: "GET",
    redirect: "manual",
    headers: { "user-agent": USER_AGENT, accept: "application/json, text/html;q=0.9, */*;q=0.8" },
    signal: AbortSignal.timeout(FETCH_TIMEOUT_MS),
  });
}

// Fetch, then follow AT MOST ONE same-host redirect (recorded in cuts). This is
// a refinement of "never silently follow", not a betrayal of it: the anti-
// bait-and-switch guarantee is that you can't be bounced off the merchant's own
// host. So a cross-host redirect, a second hop, or a 3xx without a Location is
// NOT followed — the caller punts and asks for a re-run on the destination.
async function fetchSurfaceOneHop(url, read) {
  const res = await fetchSurface(url);
  if (res.status < 300 || res.status >= 400) return res;

  const loc = res.headers.get("location");
  if (!loc) return res; // 3xx with no Location → caller punts
  let dest;
  try {
    dest = new URL(loc, url); // resolves relative Locations against the original
  } catch {
    return res; // unparseable Location → caller punts
  }
  if (dest.host !== new URL(url).host) return res; // cross-host → caller punts

  // One same-host hop, recorded. The destination's own response governs from
  // here: if IT redirects again, status stays 3xx and the caller punts — no chains.
  const res2 = await fetchSurface(dest.toString());
  read.cuts.push("followed 1 same-origin redirect");
  return res2;
}

async function decodeMerchant(url) {
  const read = blankRead(url);

  let parsed;
  try {
    parsed = new URL(url);
  } catch {
    read.reason = "Not a valid URL.";
    read.cuts.push("invalid url");
    return read;
  }
  if (parsed.protocol !== "http:" && parsed.protocol !== "https:") {
    read.reason = "URL must be http(s).";
    read.cuts.push("unsupported scheme");
    return read;
  }

  read.who = sellerFromUrl(url);

  let res;
  try {
    res = await fetchSurfaceOneHop(url, read);
  } catch (e) {
    read.reason = `Fetch failed: ${e && e.message ? e.message : String(e)}`;
    read.cuts.push("fetch failed");
    return read;
  }

  const status = res.status;

  // Still a redirect after our one allowed same-host hop → punt. Reached only
  // for a cross-host redirect, a second hop (chain), or a 3xx with no Location.
  if (status >= 300 && status < 400) {
    const loc = res.headers.get("location");
    read.reason = `Redirected (HTTP ${status})${loc ? ` to ${loc}` : ""}; not followed (cross-origin or a second hop). Re-run decode-merchant on the destination URL.`;
    read.cuts.push("redirect not followed");
    return read;
  }

  const headerChallenge = res.headers.get("payment-required");
  let body = "";
  try {
    body = await res.text();
  } catch {
    /* body may be empty/binary */
  }

  // x402 payment challenge (the autonomous path).
  // Pick whichever of body / PAYMENT-REQUIRED header actually carries a usable
  // accepts[] array. CDP-facilitated endpoints often return an empty `{}` body
  // and put the real challenge in the base64 header — a plain `||` would
  // short-circuit on the truthy-but-unusable parsed body and lose the header.
  if (status === 402 || headerChallenge) {
    const bodyCh = usableChallenge(tryParseChallenge(body));
    const headerCh = usableChallenge(tryParseChallenge(headerChallenge));
    const ch = bodyCh || headerCh;
    if (ch) {
      return buildX402Read(read, ch);
    }
    read.reason = "Got a 402 / payment challenge but couldn't parse a usable x402 'accepts' array.";
    read.cuts.push("unparseable payment challenge");
    return read;
  }

  if (status >= 400) {
    read.reason = `Merchant returned HTTP ${status}; no readable product data.`;
    read.cuts.push(`http ${status}`);
    return read;
  }

  const found = parseSurface({ contentType: res.headers.get("content-type"), body });
  return applySurface(read, found);
}

// ---------------------------------------------------------------------------
// Tool surface (wired into the one server by index.js)
// ---------------------------------------------------------------------------

const READ_TOOLS = [
  {
    name: "decode-merchant",
    description:
      "Read any product URL on the open web and return ONE clean shape (CleanRead): what it is, who sells it, what it costs, whether it's in stock, and the verdict — can an agent pay this autonomously (x402) or is it human checkout? Reads only; never signs or pays. To pay an autonomous result, use this kit's wallet lessons (read-this-challenge, how-do-i-pay).",
    inputSchema: {
      type: "object",
      properties: {
        url: {
          type: "string",
          description: "The product URL to read (http or https).",
        },
      },
      required: ["url"],
    },
  },
];

const READ_HANDLERS = {
  "decode-merchant": async (args) => {
    if (!args || typeof args.url !== "string" || !args.url.trim()) {
      throw new Error("decode-merchant requires a 'url' string.");
    }
    const read = await decodeMerchant(args.url.trim());
    return JSON.stringify(read, null, 2);
  },
};

export {
  READ_TOOLS,
  READ_HANDLERS,
  decodeMerchant,
  parseSurface,
  applySurface,
  buildX402Read,
  tryParseChallenge,
  blankRead,
};
