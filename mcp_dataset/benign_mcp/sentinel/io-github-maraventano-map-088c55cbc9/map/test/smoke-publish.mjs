// MAP — PUBLISH module smoke test (assembly spec §3 DoD).
// publish-catalog on ~3 URLs (incl. live Underground x402 + a Shopify page) →
// catalog.json of correct CleanReads → get-product returns one → .well-known written.
// Runs in a throwaway temp dir so it never pollutes the package. Run: npm run smoke:publish

import { promises as fs } from "node:fs";
import os from "node:os";
import path from "node:path";
import { publishCatalog, getCatalog, getProduct } from "../src/publish.js";

let failures = 0;
function check(label, cond, detail) {
  const ok = !!cond;
  if (!ok) failures++;
  console.log(`   ${ok ? "PASS" : "FAIL"} — ${label}${detail ? `  (${detail})` : ""}`);
}

async function run() {
  const dir = await fs.mkdtemp(path.join(os.tmpdir(), "map-publish-"));
  console.log("temp publish dir:", dir);

  const urls = [
    "https://underground.substratesymposium.com/buy/void_latte", // live x402
    "https://www.soundcore.com/products/space-q45-a3040011", // Shopify
    "https://example.com/", // unreadable
  ];

  console.log("\n[publish-catalog] decoding self + persisting");
  const result = await publishCatalog({ productUrls: urls, storeUrl: "https://underground.substratesymposium.com" }, dir);
  console.log("   summary:", JSON.stringify({ published: result.published, autonomous: result.autonomous, human_checkout: result.human_checkout, unreadable: result.unreadable }));
  check("published all 3", result.published === 3, String(result.published));
  check("1 autonomous (void_latte)", result.autonomous === 1, String(result.autonomous));

  console.log("\n[catalog.json] persisted as an array of CleanReads");
  const raw = JSON.parse(await fs.readFile(path.join(dir, "catalog.json"), "utf-8"));
  check("catalog.json is an array", Array.isArray(raw), typeof raw);
  check("each item is a CleanRead", raw.every((i) => i.schemaVersion === "map/v1" && i.sourceUrl && i.outcome), "schemaVersion/sourceUrl/outcome");

  console.log("\n[.well-known/map.json] discovery manifest written");
  const manifest = JSON.parse(await fs.readFile(path.join(dir, ".well-known", "map.json"), "utf-8"));
  console.log("   ", JSON.stringify(manifest));
  check("manifest count = 3", manifest.count === 3, String(manifest.count));
  check("manifest points to /catalog.json (root-absolute)", manifest.catalog === "/catalog.json", manifest.catalog);
  check("manifest lists the tool surface", Array.isArray(manifest.tools) && manifest.tools.includes("get-product"), (manifest.tools || []).join(","));

  console.log("\n[get-catalog]");
  const cat = await getCatalog(dir);
  check("get-catalog returns 3", cat.count === 3, String(cat.count));

  console.log("\n[get-product] by sourceUrl");
  const one = await getProduct("https://underground.substratesymposium.com/buy/void_latte", dir);
  console.log("   ", JSON.stringify({ what: one.what, outcome: one.outcome, rail: one.payable && one.payable.rail, price: one.price }));
  check("get-product returns the void_latte CleanRead", one.outcome === "autonomous" && one.payable.rail === "x402", `${one.outcome}/${one.payable && one.payable.rail}`);

  console.log("\n[get-product] miss is honest");
  const miss = await getProduct("https://nope.example/x", dir);
  check("missing product → found:false", miss.found === false, JSON.stringify(miss).slice(0, 60));

  await fs.rm(dir, { recursive: true, force: true });
  console.log(`\n${failures === 0 ? "ALL PUBLISH CHECKS PASSED" : failures + " CHECK(S) FAILED"}`);
  process.exit(failures === 0 ? 0 : 1);
}

run().catch((e) => {
  console.error("publish smoke crashed:", e);
  process.exit(1);
});
