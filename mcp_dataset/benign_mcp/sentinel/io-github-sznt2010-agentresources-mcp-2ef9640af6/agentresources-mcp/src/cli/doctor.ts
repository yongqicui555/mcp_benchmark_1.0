import { promises as fs } from "node:fs";
import { spawnSync } from "node:child_process";
import path from "node:path";

export type DoctorOptions = {
  apiUrl: string;
  token?: string;
  fix: boolean;
  offline: boolean;
  quick: boolean;
  json: boolean;
};

type CheckResult = {
  id: string;
  label: string;
  status: "pass" | "fail" | "warn" | "skip";
  detail?: string;
  hint?: string;
};

/**
 * `ar doctor` — self-diagnostic. Six checks, per D21.a + D34.c + D37.a:
 *  1. gateway reachable
 *  2. LiteLLM Tier-1 healthy (skipped offline / when no token)
 *  3. Trust Card signer key configured (env presence; we never print it)
 *  4. Trust Card issuance dry-run (skipped offline)
 *  5. Secrets scan of cwd (no plaintext keys committed near working dir)
 *  6. Dependency vuln check (npm audit / pnpm audit; warn-only by default)
 *
 * Exit code = number of failed checks (0 = healthy). Warns do not contribute to exit.
 */
export async function runDoctor(opts: DoctorOptions): Promise<number> {
  const checks: CheckResult[] = [];

  // 1. gateway reachable
  if (opts.offline) {
    checks.push({ id: "gateway", label: "Gateway reachable", status: "skip", detail: "--offline" });
  } else {
    checks.push(await checkGateway(opts));
  }

  // 2. LiteLLM Tier-1 (only meaningful with a token + online + non-quick)
  if (opts.offline) {
    checks.push({
      id: "litellm",
      label: "LiteLLM Tier-1 responding",
      status: "skip",
      detail: "--offline",
    });
  } else if (opts.quick) {
    checks.push({
      id: "litellm",
      label: "LiteLLM Tier-1 responding",
      status: "skip",
      detail: "--quick",
    });
  } else if (!opts.token) {
    checks.push({
      id: "litellm",
      label: "LiteLLM Tier-1 responding",
      status: "skip",
      detail: "no AR_SESSION_TOKEN — login first to test",
    });
  } else {
    checks.push(await checkLiteLLM(opts));
  }

  // 3. Signer key env presence
  checks.push(checkSignerKeyEnv());

  // 4. Trust Card issuance dry-run
  if (opts.offline || opts.quick) {
    checks.push({
      id: "trust_card_dryrun",
      label: "Trust Card issuance dry-run",
      status: "skip",
      detail: opts.offline ? "--offline" : "--quick",
    });
  } else {
    checks.push(await checkTrustCardDryRun(opts));
  }

  // 5. Secrets scan
  checks.push(await checkSecretsScan(process.cwd()));

  // 6. Dep vuln check
  if (opts.quick || opts.offline) {
    checks.push({
      id: "vuln",
      label: "Dependency vulnerability scan",
      status: "skip",
      detail: "--quick/--offline",
    });
  } else {
    checks.push(await checkVulns());
  }

  const fails = checks.filter((c) => c.status === "fail").length;

  if (opts.json) {
    process.stdout.write(JSON.stringify({ ok: fails === 0, checks }, null, 2) + "\n");
  } else {
    printPretty(checks);
  }
  return fails;
}

async function checkGateway(opts: DoctorOptions): Promise<CheckResult> {
  try {
    const res = await fetch(`${opts.apiUrl.replace(/\/$/u, "")}/api/health`, {
      signal: AbortSignal.timeout(5_000),
    });
    if (res.ok) {
      return { id: "gateway", label: "Gateway reachable", status: "pass", detail: opts.apiUrl };
    }
    return {
      id: "gateway",
      label: "Gateway reachable",
      status: "fail",
      detail: `HTTP ${res.status} from ${opts.apiUrl}/api/health`,
      hint: "Check AR_API_URL and the gateway's /api/health response.",
    };
  } catch (err) {
    return {
      id: "gateway",
      label: "Gateway reachable",
      status: "fail",
      detail: err instanceof Error ? err.message : String(err),
      hint: "Network failure or AR_API_URL is wrong.",
    };
  }
}

async function checkLiteLLM(opts: DoctorOptions): Promise<CheckResult> {
  try {
    const res = await fetch(`${opts.apiUrl.replace(/\/$/u, "")}/api/v1/llm/health`, {
      headers: { authorization: `Bearer ${opts.token!}` },
      signal: AbortSignal.timeout(8_000),
    });
    if (res.ok) {
      const j = (await res.json().catch(() => ({}))) as { tier1?: string };
      const tier1 = j.tier1 ?? "unknown";
      return {
        id: "litellm",
        label: "LiteLLM Tier-1 responding",
        status: tier1 === "healthy" ? "pass" : "warn",
        detail: `tier1=${tier1}`,
        ...(tier1 === "healthy"
          ? {}
          : { hint: "Tier-1 is degraded; falling through to Tier-2 (paid)." }),
      };
    }
    return {
      id: "litellm",
      label: "LiteLLM Tier-1 responding",
      status: "fail",
      detail: `HTTP ${res.status}`,
    };
  } catch (err) {
    return {
      id: "litellm",
      label: "LiteLLM Tier-1 responding",
      status: "fail",
      detail: err instanceof Error ? err.message : String(err),
    };
  }
}

function checkSignerKeyEnv(): CheckResult {
  const trustKey = process.env["AR_TRUST_CARD_SIGNER_KEY"];
  const erc8004Key = process.env["ERC8004_SIGNER_KEY"];
  if (trustKey || erc8004Key) {
    return {
      id: "signer_key",
      label: "Trust Card signer key configured",
      status: "pass",
      detail: trustKey
        ? "AR_TRUST_CARD_SIGNER_KEY present"
        : "ERC8004_SIGNER_KEY present (fallback)",
    };
  }
  return {
    id: "signer_key",
    label: "Trust Card signer key configured",
    status: "warn",
    detail: "no AR_TRUST_CARD_SIGNER_KEY or ERC8004_SIGNER_KEY in env",
    hint: "Required only on the issuer. Verifier-only or read-only setups can ignore this.",
  };
}

async function checkTrustCardDryRun(opts: DoctorOptions): Promise<CheckResult> {
  try {
    const res = await fetch(
      `${opts.apiUrl.replace(/\/$/u, "")}/.well-known/trust-card/0x0000000000000000000000000000000000000000`,
      {
        signal: AbortSignal.timeout(5_000),
      },
    );
    if (res.status === 404) {
      return {
        id: "trust_card_dryrun",
        label: "Trust Card issuance endpoint responsive",
        status: "pass",
        detail: "404 for zero-wallet — endpoint reachable and behaving",
      };
    }
    if (res.ok) {
      return {
        id: "trust_card_dryrun",
        label: "Trust Card issuance endpoint responsive",
        status: "pass",
        detail: `HTTP ${res.status}`,
      };
    }
    return {
      id: "trust_card_dryrun",
      label: "Trust Card issuance endpoint responsive",
      status: "fail",
      detail: `HTTP ${res.status}`,
    };
  } catch (err) {
    return {
      id: "trust_card_dryrun",
      label: "Trust Card issuance endpoint responsive",
      status: "fail",
      detail: err instanceof Error ? err.message : String(err),
    };
  }
}

const SECRET_PATTERNS: ReadonlyArray<{ name: string; re: RegExp }> = [
  { name: "AWS access key", re: /AKIA[0-9A-Z]{16}/u },
  {
    name: "Generic secret",
    re: /(api[-_]?key|secret|token|password)\s*[:=]\s*["'][^"']{16,}["']/i,
  },
  { name: "Hex private key", re: /\b(?:0x)?[0-9a-fA-F]{64}\b/u },
  { name: "Slack token", re: /xox[abps]-[0-9a-zA-Z-]{10,}/u },
  { name: "GitHub PAT", re: /ghp_[0-9a-zA-Z]{36}/u },
];

const SCAN_EXTS = new Set([
  ".env",
  ".ts",
  ".tsx",
  ".js",
  ".mjs",
  ".cjs",
  ".py",
  ".sh",
  ".yaml",
  ".yml",
  ".json",
]);
const SCAN_SKIP_DIRS = new Set([
  "node_modules",
  ".git",
  "dist",
  ".next",
  "build",
  "coverage",
  "playwright-report",
  "test-results",
]);

async function checkSecretsScan(root: string): Promise<CheckResult> {
  const findings: string[] = [];
  await walk(root, root, findings, 0);
  if (findings.length === 0) {
    return { id: "secrets", label: "No plaintext secrets in cwd", status: "pass" };
  }
  return {
    id: "secrets",
    label: "No plaintext secrets in cwd",
    status: "warn",
    detail: `${findings.length} suspicious match(es)`,
    hint:
      `Review:\n    ${findings.slice(0, 8).join("\n    ")}` +
      (findings.length > 8 ? `\n    …and ${findings.length - 8} more` : ""),
  };
}

async function walk(
  start: string,
  current: string,
  findings: string[],
  depth: number,
): Promise<void> {
  if (depth > 6) return;
  let entries: import("node:fs").Dirent[];
  try {
    entries = await fs.readdir(current, { withFileTypes: true });
  } catch {
    return;
  }
  for (const entry of entries) {
    if (entry.name.startsWith(".") && entry.name !== ".env" && entry.name !== ".env.local")
      continue;
    const full = path.join(current, entry.name);
    if (entry.isDirectory()) {
      if (SCAN_SKIP_DIRS.has(entry.name)) continue;
      await walk(start, full, findings, depth + 1);
    } else if (entry.isFile()) {
      const ext = path.extname(entry.name);
      if (!SCAN_EXTS.has(ext) && entry.name !== ".env" && !entry.name.startsWith(".env.")) continue;
      try {
        const stat = await fs.stat(full);
        if (stat.size > 1_000_000) continue; // skip large files
        const content = await fs.readFile(full, "utf8");
        for (const pat of SECRET_PATTERNS) {
          if (pat.re.test(content)) {
            findings.push(`${path.relative(start, full)} (${pat.name})`);
            break;
          }
        }
      } catch {
        /* ignore unreadable */
      }
    }
  }
}

async function checkVulns(): Promise<CheckResult> {
  // Prefer pnpm audit (this repo's package manager). Fall back to npm audit.
  const tool = whichOf(["pnpm", "npm"]);
  if (!tool) {
    return {
      id: "vuln",
      label: "Dependency vulnerability scan",
      status: "skip",
      detail: "no pnpm or npm on PATH",
    };
  }
  const args = tool === "pnpm" ? ["audit", "--json"] : ["audit", "--json"];
  const res = spawnSync(tool, args, { encoding: "utf8", timeout: 30_000 });
  if (res.status === 0) {
    return {
      id: "vuln",
      label: "Dependency vulnerability scan",
      status: "pass",
      detail: `${tool} audit clean`,
    };
  }
  // npm audit returns non-zero when vulnerabilities found; surface as warn (don't fail the doctor by default).
  let summary = "vulnerabilities found";
  try {
    const json = JSON.parse(res.stdout || "{}");
    const counts = (json.metadata?.vulnerabilities ?? json.vulnerabilities ?? {}) as Record<
      string,
      number
    >;
    summary =
      Object.entries(counts)
        .filter(([_, n]) => typeof n === "number" && n > 0)
        .map(([k, n]) => `${k}: ${n}`)
        .join(", ") || summary;
  } catch {
    /* ignore */
  }
  return {
    id: "vuln",
    label: "Dependency vulnerability scan",
    status: "warn",
    detail: summary,
    hint: `Run \`${tool} audit\` for details.`,
  };
}

function whichOf(cands: ReadonlyArray<string>): string | null {
  for (const c of cands) {
    const r = spawnSync(process.platform === "win32" ? "where" : "which", [c], {
      encoding: "utf8",
    });
    if (r.status === 0 && r.stdout.trim()) return c;
  }
  return null;
}

function printPretty(checks: ReadonlyArray<CheckResult>): void {
  const ICONS: Record<CheckResult["status"], string> = {
    pass: "✓",
    fail: "✗",
    warn: "!",
    skip: "·",
  };
  process.stdout.write("\nar doctor\n─────────\n");
  for (const c of checks) {
    process.stdout.write(`  ${ICONS[c.status]}  ${c.label.padEnd(42)} ${c.status.toUpperCase()}\n`);
    if (c.detail) process.stdout.write(`       ${c.detail}\n`);
    if (c.hint) process.stdout.write(`       hint: ${c.hint}\n`);
  }
  const fails = checks.filter((c) => c.status === "fail").length;
  const warns = checks.filter((c) => c.status === "warn").length;
  process.stdout.write(
    `\n${fails === 0 ? "OK" : "FAIL"}  ${checks.length} checks  (${fails} fail, ${warns} warn)\n\n`,
  );
}
