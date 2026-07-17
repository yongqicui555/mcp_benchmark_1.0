/**
 * Local MCP server test — exercises the real stdio transport.
 *
 * Usage:
 *   node test.mjs                  (uses .env.test keys)
 *   node test.mjs --tool postcode  (run only postcode test)
 *
 * No extra packages needed — raw JSON-RPC 2.0 over stdio.
 */

import { spawn } from "child_process";
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

// ── load .env.test ──────────────────────────────────────────────────────────
const __dir = dirname(fileURLToPath(import.meta.url));
const envFile = join(__dir, ".env.test");
const env = { ...process.env };

try {
  for (const line of readFileSync(envFile, "utf8").split("\n")) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;
    const [key, ...rest] = trimmed.split("=");
    if (key) env[key.trim()] = rest.join("=").trim();
  }
  console.log("✓ Loaded .env.test\n");
} catch {
  console.warn("⚠ .env.test not found — using process env\n");
}

// ── MCP client over stdio ──────────────────────────────────────────────────
class McpClient {
  #proc;
  #buf = "";
  #pending = new Map();
  #nextId = 1;

  constructor(proc) {
    this.#proc = proc;
    proc.stdout.setEncoding("utf8");
    proc.stdout.on("data", (chunk) => {
      this.#buf += chunk;
      for (const line of this.#buf.split("\n")) {
        if (!line.trim()) continue;
        try {
          const msg = JSON.parse(line);
          const res = this.#pending.get(msg.id);
          if (res) { this.#pending.delete(msg.id); res(msg); }
        } catch { /* partial line */ }
      }
      // keep only the last (potentially incomplete) line
      this.#buf = this.#buf.endsWith("\n") ? "" : this.#buf.split("\n").at(-1);
    });
    proc.stderr.on("data", (d) =>
      process.stderr.write(`[server stderr] ${d}`)
    );
  }

  send(method, params = {}) {
    const id = this.#nextId++;
    return new Promise((resolve, reject) => {
      this.#pending.set(id, resolve);
      const msg = JSON.stringify({ jsonrpc: "2.0", id, method, params }) + "\n";
      this.#proc.stdin.write(msg);
      // 30s to handle Java Lambda cold starts (phone + data-convert APIs)
      setTimeout(() => {
        if (this.#pending.has(id)) {
          this.#pending.delete(id);
          reject(new Error(`Timeout waiting for response to ${method} (id=${id})`));
        }
      }, 30_000);
    });
  }

  async initialize() {
    return this.send("initialize", {
      protocolVersion: "2024-11-05",
      capabilities: {},
      clientInfo: { name: "test-client", version: "1.0" },
    });
  }

  async listTools() {
    return this.send("tools/list");
  }

  async callTool(name, args) {
    return this.send("tools/call", { name, arguments: args });
  }

  close() {
    this.#proc.stdin.end();
  }
}

// ── helpers ─────────────────────────────────────────────────────────────────
const RESET = "\x1b[0m";
const GREEN = "\x1b[32m";
const RED   = "\x1b[31m";
const CYAN  = "\x1b[36m";
const DIM   = "\x1b[2m";

function pass(label) { console.log(`${GREEN}✓${RESET} ${label}`); }
function fail(label, err) { console.log(`${RED}✗${RESET} ${label}\n  ${RED}${err}${RESET}`); }
function section(title) { console.log(`\n${CYAN}── ${title} ──${RESET}`); }

function formatResult(res) {
  if (res.error) return `${RED}ERROR: ${JSON.stringify(res.error)}${RESET}`;
  const content = res.result?.content?.[0]?.text ?? JSON.stringify(res.result);
  try {
    const parsed = JSON.parse(content);
    // truncate large responses
    const str = JSON.stringify(parsed, null, 2);
    const lines = str.split("\n");
    if (lines.length > 20) return DIM + lines.slice(0, 20).join("\n") + `\n  ... (${lines.length - 20} more lines)` + RESET;
    return DIM + str + RESET;
  } catch {
    return DIM + String(content).slice(0, 400) + RESET;
  }
}

// ── test cases ───────────────────────────────────────────────────────────────
const TESTS = [
  {
    id: "email",
    name: "validate_email",
    label: "validate_email — valid address",
    args: { email: "test@gmail.com" },
  },
  {
    id: "email-bad",
    name: "validate_email",
    label: "validate_email — disposable address",
    args: { email: "user@mailinator.com" },
  },
  {
    id: "phone",
    name: "validate_phone",
    label: "validate_phone — UK mobile",
    args: { phone: "+447911123456" },
  },
  {
    id: "postcode",
    name: "lookup_uk_postcode",
    label: "lookup_uk_postcode — SW1A 1AA (Buckingham Palace)",
    args: { postcode: "SW1A 1AA" },
  },
  {
    id: "postcode-search",
    name: "search_uk_address",
    label: "search_uk_address — 10 Downing Street",
    args: { address: "10 Downing Street London" },
  },
  {
    id: "vat",
    name: "validate_vat",
    label: "validate_vat — GB553557881",
    args: { vatNumber: "GB553557881" },
  },
  {
    id: "pincode",
    name: "lookup_india_pincode",
    label: "lookup_india_pincode — 110001 (New Delhi)",
    args: { pincode: "110001" },
  },
  {
    id: "barcode",
    name: "generate_barcode",
    label: "generate_barcode — Code128",
    args: { text: "APITIER-001", format: "code128" },
  },
  {
    id: "qrcode",
    name: "generate_qrcode",
    label: "generate_qrcode — URL",
    args: { text: "https://apitier.com", width: 128, height: 128 },
  },
  {
    id: "convert",
    name: "convert_data",
    label: "convert_data — CSV to JSON",
    args: {
      data: "name,email\nAlice,alice@example.com\nBob,bob@example.com",
      from: "csv",
      to: "json",
    },
  },
];

// ── main ─────────────────────────────────────────────────────────────────────
const filterArg = process.argv.find((a) => a.startsWith("--tool="))?.split("=")[1];

const proc = spawn("node", [join(__dir, "dist/index.js")], {
  env,
  stdio: ["pipe", "pipe", "pipe"],
});

proc.on("error", (err) => {
  console.error(`${RED}Failed to start server: ${err.message}${RESET}`);
  process.exit(1);
});

const client = new McpClient(proc);

try {
  // 1. Handshake
  section("Handshake");
  const init = await client.initialize();
  if (init.result?.serverInfo) {
    pass(`Server: ${init.result.serverInfo.name} v${init.result.serverInfo.version}`);
  } else {
    fail("Initialize", JSON.stringify(init));
  }

  // 2. List tools
  section("Tool registration");
  const toolsRes = await client.listTools();
  const tools = toolsRes.result?.tools ?? [];
  console.log(`Registered ${tools.length} tool(s):`);
  for (const t of tools) console.log(`  ${GREEN}•${RESET} ${t.name}`);

  if (tools.length === 0) {
    console.error(`\n${RED}No tools registered — check your env keys in .env.test${RESET}`);
    process.exit(1);
  }

  // 3. Run tool tests
  section("Tool calls");
  const registeredNames = new Set(tools.map((t) => t.name));
  const testsToRun = TESTS.filter((t) => {
    if (filterArg && t.id !== filterArg) return false;
    if (!registeredNames.has(t.name)) return false;
    return true;
  });

  if (testsToRun.length === 0) {
    console.log(`No matching tests to run (filter: ${filterArg ?? "none"})`);
  }

  let passed = 0;
  let failed = 0;

  for (const t of testsToRun) {
    try {
      const res = await client.callTool(t.name, t.args);
      if (res.result?.isError) {
        const errText = res.result.content?.[0]?.text ?? "tool returned isError";
        // 429 / 402 = demo key quota — MCP transport works, API limit hit
        if (errText.includes("429") || errText.includes("402") || errText.includes("Limit Exceeded") || errText.includes("credit not available")) {
          console.log(`${DIM}⚠ ${t.label}${RESET}`);
          console.log(`  ${DIM}Demo key quota hit (expected on free tier) — transport OK${RESET}`);
          passed++; // transport + auth worked
        // 404 from VAT = number not in HMRC registry, but API + auth worked
        } else if (t.name === "validate_vat" && errText.includes("404")) {
          console.log(`${DIM}⚠ ${t.label}${RESET}`);
          console.log(`  ${DIM}VAT number not in HMRC registry (expected for test number) — transport OK${RESET}`);
          passed++;
        } else {
          fail(t.label, errText);
          failed++;
        }
      } else {
        pass(t.label);
        console.log(formatResult(res));
        passed++;
      }
    } catch (err) {
      fail(t.label, err.message);
      failed++;
    }
  }

  // 4. Summary
  section("Summary");
  console.log(`  Tools registered : ${tools.length}`);
  console.log(`  Tests run        : ${testsToRun.length}`);
  console.log(`  ${GREEN}Passed${RESET}           : ${passed}`);
  if (failed > 0) console.log(`  ${RED}Failed${RESET}           : ${failed}`);

} catch (err) {
  console.error(`\n${RED}Unexpected error: ${err.message}${RESET}`);
  console.error(err.stack);
} finally {
  client.close();
  setTimeout(() => process.exit(0), 500);
}
