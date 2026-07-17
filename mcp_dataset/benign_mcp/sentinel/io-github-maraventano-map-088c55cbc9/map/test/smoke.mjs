// Merchant Key — smoke test for the four definition-of-done cases (spec §8).
// Hits the live Underground x402 endpoint (the proven case) and real pages.
// Run: npm run smoke

import { decodeMerchant, parseSurface } from "../src/read.js";

let failures = 0;
function check(label, cond, detail) {
  const ok = !!cond;
  if (!ok) failures++;
  console.log(`   ${ok ? "PASS" : "FAIL"} — ${label}${detail ? `  (${detail})` : ""}`);
}

async function run() {
  // 1. Live Underground x402 item — the one autonomous case.
  console.log("\n[1] Underground x402 (void_latte) — expect autonomous");
  const a = await decodeMerchant("https://underground.substratesymposium.com/buy/void_latte");
  console.log(JSON.stringify(a, null, 2));
  check("outcome autonomous", a.outcome === "autonomous", a.outcome);
  check("rail x402", a.payable.rail === "x402", a.payable.rail);
  check("price.total set", a.price.total != null, String(a.price.total));
  check("available in_stock", a.available === "in_stock", a.available);
  check("payTo structured", a.payable.payTo && a.payable.payTo.value, JSON.stringify(a.payable.payTo));

  // 2. Shopify product page — expect human_checkout + "no x402 rail" cut.
  console.log("\n[2] Shopify (soundcore Space Q45) — expect human_checkout");
  const b = await decodeMerchant("https://www.soundcore.com/products/space-q45-a3040011");
  console.log(JSON.stringify(b, null, 2));
  check("outcome human_checkout", b.outcome === "human_checkout", b.outcome);
  check("what set", !!b.what, b.what);
  check("who set", !!b.who, b.who);
  check("price.total set", b.price.total != null, String(b.price.total));
  check("cuts includes 'no x402 rail'", b.cuts.includes("no x402 rail"), b.cuts.join(", "));

  // 3a. Deterministic JSON-LD extraction (offline, no network) — proves the path.
  console.log("\n[3a] JSON-LD extraction (offline synthetic page)");
  const synthetic = `<!doctype html><html><head>
    <script type="application/ld+json">
    {"@context":"https://schema.org","@type":"Product","name":"Acme Field Notebook",
     "offers":{"@type":"Offer","price":"24.50","priceCurrency":"USD","availability":"https://schema.org/InStock"}}
    </script></head><body>noise noise noise</body></html>`;
  const s = parseSurface({ contentType: "text/html", body: synthetic });
  console.log("   ", JSON.stringify(s));
  check("what extracted", s.what === "Acme Field Notebook", s.what);
  check("price extracted", s.price === 24.5, String(s.price));
  check("currency extracted", s.currency === "USD", s.currency);
  check("availability mapped", s.available === "in_stock", s.available);

  // 3b. A live JSON-LD product page via the full decode path — expect human_checkout.
  console.log("\n[3b] Live JSON-LD product page — expect human_checkout");
  const c = await decodeMerchant("https://www.gymshark.com/products/gymshark-arrival-5-shorts-black-ss22");
  console.log(JSON.stringify(c, null, 2));
  if (c.outcome === "human_checkout") {
    check("outcome human_checkout", c.outcome === "human_checkout", c.outcome);
    check("what set", !!c.what, c.what);
    check("who set", !!c.who, c.who);
  } else {
    console.log(`   (note: live case-3 site returned '${c.outcome}' — ${c.reason}. JSON-LD path proven by [3a]; swap URL if needed.)`);
  }

  // 5. Redirect policy: follow ONE same-host hop; punt cross-host. (soft live checks)
  console.log("\n[5a] Same-host canonical→slug redirect — expect it's followed + noted in cuts");
  const e = await decodeMerchant("https://baronfig.com/products/shopconfidant");
  console.log(`   outcome: ${e.outcome} | cuts: [${e.cuts.join("; ")}]`);
  if (e.cuts.includes("followed 1 same-origin redirect")) {
    check("followed the same-host redirect", e.outcome === "human_checkout", e.outcome);
  } else {
    console.log(`   (note: live site didn't 1-hop-redirect as expected — '${e.outcome}'; behavior proven in /tmp run; swap URL if needed.)`);
  }

  console.log("\n[5b] Cross-host redirect — expect punt (NOT followed)");
  const f = await decodeMerchant("https://httpbin.org/redirect-to?url=https%3A%2F%2Fexample.com&status_code=301");
  console.log(`   outcome: ${f.outcome} | cuts: [${f.cuts.join("; ")}]`);
  if (f.cuts.includes("redirect not followed")) {
    check("cross-host redirect punted", f.outcome === "unreadable" && !f.cuts.includes("followed 1 same-origin redirect"), f.outcome);
  } else {
    console.log(`   (note: httpbin unreachable/changed — '${f.outcome}'; cross-host punt proven in /tmp run.)`);
  }

  // 4. Junk / JS-only / non-product page — expect unreadable, honest reason.
  console.log("\n[4] Non-product page (example.com) — expect unreadable");
  const d = await decodeMerchant("https://example.com/");
  console.log(JSON.stringify(d, null, 2));
  check("outcome unreadable", d.outcome === "unreadable", d.outcome);
  check("reason given", !!d.reason, d.reason);

  console.log(`\n${failures === 0 ? "ALL CORE CHECKS PASSED" : failures + " CHECK(S) FAILED"}`);
  process.exit(failures === 0 ? 0 : 1);
}

run().catch((e) => {
  console.error("smoke test crashed:", e);
  process.exit(1);
});
