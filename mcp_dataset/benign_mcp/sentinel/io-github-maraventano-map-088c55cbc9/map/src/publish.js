/**
 * MAP — PUBLISH module: Atlas (the publisher)
 *
 * The decoder pointed INWARD. A merchant publishes by reading *itself* with the
 * exact same tool a buyer would use (decode-merchant), then persisting and
 * serving the resulting CleanReads. No new parsing. No per-platform adapters.
 *
 * Boundary (same as the decoder): emits documents, validates shape, persists,
 * serves. It NEVER deploys merchant infrastructure, holds keys, transacts, or
 * stores cards. Teacher, not butler — both halves.
 *
 * Trust boundary (v1): we trust the reads produced here (the merchant ran its
 * own decoder). Independent re-read/diff, merchant-signed manifests, and
 * periodic re-audit are NAMED future work — not built. One safety property
 * already holds: the payment rail enforces the real price at settlement, so a
 * mistaken manifest can't overcharge — it can only misstate soft fields (stock).
 *
 * Pure module: no MCP/server code here. index.js wires these tools into one server.
 *
 * By Lisa Maraventano, with Claude. Clarksdale, Mississippi. Dual-licensed — see LICENSE.
 */

import { promises as fs } from "node:fs";
import path from "node:path";
import { decodeMerchant } from "./read.js";

const SCHEMA_VERSION = "map/v1";
const CATALOG_FILE = "catalog.json";
const WELL_KNOWN_DIR = ".well-known";
const WELL_KNOWN_FILE = "map.json";

// A CleanRead is the only shape we persist — no schema beyond it.
function isCleanRead(o) {
  return (
    o &&
    typeof o === "object" &&
    o.schemaVersion === SCHEMA_VERSION &&
    typeof o.sourceUrl === "string" &&
    typeof o.outcome === "string"
  );
}

// Decode each of the merchant's own product URLs with the SAME engine a buyer
// uses, then persist the CleanReads + write the discovery manifest.
async function publishCatalog(args, dir = process.cwd()) {
  const productUrls = Array.isArray(args && args.productUrls) ? args.productUrls : [];
  const storeUrl = (args && args.storeUrl) || null;
  if (!productUrls.length) {
    throw new Error("publish-catalog requires 'productUrls' (a non-empty array of the merchant's own product URLs).");
  }

  const items = [];
  for (const url of productUrls) {
    if (typeof url !== "string" || !url.trim()) continue;
    const read = await decodeMerchant(url.trim());
    if (isCleanRead(read)) items.push(read);
  }

  // catalog.json IS the collected CleanReads — a list, nothing more.
  await fs.writeFile(path.join(dir, CATALOG_FILE), JSON.stringify(items, null, 2) + "\n", "utf-8");

  // Discovery manifest: a thin pointer registries can crawl. Not a product
  // schema — the products live in catalog.json as CleanReads.
  const manifest = {
    schemaVersion: SCHEMA_VERSION,
    service: "map",
    description:
      "Agent-readable product catalog, self-decoded with MAP (Maraventano Agent Protocol). Each catalog item is a CleanRead.",
    store: storeUrl,
    // Root-absolute, NOT "./" — the manifest lives at /.well-known/map.json, so a
    // relative "./catalog.json" would resolve to /.well-known/catalog.json. The
    // catalog is served from the site root.
    catalog: `/${CATALOG_FILE}`,
    count: items.length,
    generatedAt: new Date().toISOString(),
    tools: ["decode-merchant", "get-catalog", "get-product"],
  };
  await fs.mkdir(path.join(dir, WELL_KNOWN_DIR), { recursive: true });
  await fs.writeFile(
    path.join(dir, WELL_KNOWN_DIR, WELL_KNOWN_FILE),
    JSON.stringify(manifest, null, 2) + "\n",
    "utf-8"
  );

  return {
    published: items.length,
    autonomous: items.filter((i) => i.outcome === "autonomous").length,
    human_checkout: items.filter((i) => i.outcome === "human_checkout").length,
    unreadable: items.filter((i) => i.outcome === "unreadable").length,
    catalogFile: path.join(dir, CATALOG_FILE),
    wellKnownFile: path.join(dir, WELL_KNOWN_DIR, WELL_KNOWN_FILE),
    items,
  };
}

async function readCatalog(dir = process.cwd()) {
  try {
    const raw = await fs.readFile(path.join(dir, CATALOG_FILE), "utf-8");
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return null; // not published yet
  }
}

async function getCatalog(dir = process.cwd()) {
  const items = await readCatalog(dir);
  if (items === null) {
    return { count: 0, items: [], note: "No catalog published yet. Run publish-catalog first." };
  }
  return { count: items.length, items };
}

async function getProduct(url, dir = process.cwd()) {
  if (typeof url !== "string" || !url.trim()) {
    throw new Error("get-product requires a 'url' (the sourceUrl of a published product).");
  }
  const items = await readCatalog(dir);
  if (items === null) {
    return { found: false, note: "No catalog published yet. Run publish-catalog first." };
  }
  const needle = url.trim();
  const hit = items.find((i) => i.sourceUrl === needle);
  if (!hit) {
    return { found: false, note: `No published product with sourceUrl ${needle}.` };
  }
  return hit; // the CleanRead
}

// ---------------------------------------------------------------------------
// Tool surface (wired into the one server by index.js)
// ---------------------------------------------------------------------------

const PUBLISH_TOOLS = [
  {
    name: "publish-catalog",
    description:
      "Publish your own catalog by reading yourself: runs decode-merchant on each of the merchant's product URLs, collects the CleanReads, writes ./catalog.json, and writes a ./.well-known/map.json discovery manifest. Persists and serves; never deploys infrastructure, holds keys, or transacts. Files are written to the server's working directory.",
    inputSchema: {
      type: "object",
      properties: {
        productUrls: {
          type: "array",
          items: { type: "string" },
          description: "The merchant's own product URLs to decode and publish.",
        },
        storeUrl: {
          type: "string",
          description: "Optional: the store's base URL, recorded in the discovery manifest.",
        },
      },
      required: ["productUrls"],
    },
  },
  {
    name: "get-catalog",
    description:
      "Return the published catalog (the persisted CleanReads from ./catalog.json). A tool-callable surface other agents can read.",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "get-product",
    description:
      "Return one published CleanRead by its sourceUrl, from ./catalog.json.",
    inputSchema: {
      type: "object",
      properties: {
        url: { type: "string", description: "The sourceUrl of the published product." },
      },
      required: ["url"],
    },
  },
];

const PUBLISH_HANDLERS = {
  "publish-catalog": async (args) => JSON.stringify(await publishCatalog(args || {}), null, 2),
  "get-catalog": async () => JSON.stringify(await getCatalog(), null, 2),
  "get-product": async (args) => JSON.stringify(await getProduct(args && args.url), null, 2),
};

export {
  PUBLISH_TOOLS,
  PUBLISH_HANDLERS,
  publishCatalog,
  getCatalog,
  getProduct,
};
