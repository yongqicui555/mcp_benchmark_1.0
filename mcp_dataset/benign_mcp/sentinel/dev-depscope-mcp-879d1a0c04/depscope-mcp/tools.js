/**
 * DepScope MCP — shared tool definitions and dispatcher.
 * Consumed by both the stdio entry point (index.js) and the Streamable HTTP
 * entry point (http-server.js).
 */

const API_BASE = process.env.DEPSCOPE_API_URL || "https://depscope.dev";
const API_KEY = process.env.DEPSCOPE_API_KEY || "";

export const ECOSYSTEMS = [
  "npm", "pypi", "cargo", "go", "composer", "maven", "nuget", "rubygems",
  "pub", "hex", "swift", "cocoapods", "cpan", "hackage", "cran", "conda",
  "homebrew", "jsr", "julia",
];

// Tool list is ordered from highest-value/most-common to long-tail.
// Security gates come first (must run BEFORE install), then cheap lookups,
// then full reports, then specialised analyses, then feedback channels.
export const TOOLS = [

  // ── 1. Security gates (run BEFORE any install suggestion) ───────────
  {
    name: "check_malicious",
    description:
      "Supply-chain malware check against OpenSSF/OSV. USE WHEN: about to suggest install of an unvetted/unfamiliar package; name came from a blog/tutorial. Call BEFORE check_package for untrusted pkgs. RETURNS: {is_malicious, threat_tier, source}.",
    annotations: {
      title: "check_malicious",
      readOnlyHint: true,
      destructiveHint: false,
      idempotentHint: true,
      openWorldHint: true,
    },
    inputSchema: {
      type: "object",
      properties: {
        ecosystem: { type: "string", enum: ECOSYSTEMS },
        package: { type: "string" },
      },
      required: ["ecosystem", "package"],
    },
  },
  {
    name: "check_typosquat",
    description:
      "Typosquat detector. USE WHEN: name differs from a well-known package by 1-2 chars (`lodsh`, `reqeusts`); copy-paste from unreliable source; downloads near zero but name looks familiar. RETURNS: {is_typosquat, likely_target, confidence}.",
    annotations: {
      title: "check_typosquat",
      readOnlyHint: true,
      destructiveHint: false,
      idempotentHint: true,
      openWorldHint: true,
    },
    inputSchema: {
      type: "object",
      properties: {
        ecosystem: { type: "string", enum: ECOSYSTEMS },
        package: { type: "string" },
      },
      required: ["ecosystem", "package"],
    },
  },
  {
    name: "check_bulk",
    description:
      "Fast pre-flight filter for a batch of (ecosystem, package) pairs. DB-only, <100ms for 100 items. USE WHEN: about to emit `npm install a b c …` or `pip install a b c …` — catches hallucinated names, stdlib, typos, and known-bad in ONE call. NOT a dep-tree audit (use scan_project for that). RETURNS: per-item {status: exists|stdlib|malicious|typosquat_suspect|historical_incident|unknown}.",
    annotations: {
      title: "check_bulk",
      readOnlyHint: true,
      idempotentHint: true,
      openWorldHint: true,
    },
    inputSchema: {
      type: "object",
      properties: {
        items: {
          type: "array",
          maxItems: 100,
          items: {
            type: "object",
            properties: {
              ecosystem: { type: "string", enum: ECOSYSTEMS },
              package: { type: "string" },
            },
            required: ["ecosystem", "package"],
          },
        },
      },
      required: ["items"],
    },
  },
  {
    name: "package_exists",
    description:
      "Boolean registry existence check. USE WHEN: about to emit a package name in an install command but unsure it exists; verifying a name generated from training data. RETURNS: {exists}.",
    annotations: {
      title: "package_exists",
      readOnlyHint: true,
      destructiveHint: false,
      idempotentHint: true,
      openWorldHint: true,
    },
    inputSchema: {
      type: "object",
      properties: {
        ecosystem: { type: "string", enum: ECOSYSTEMS },
        package: { type: "string" },
      },
      required: ["ecosystem", "package"],
    },
  },

  // ── 2. Cheap lookups (one specific field) ───────────────────────────
  {
    name: "get_latest_version",
    description:
      "Latest published version + deprecation flag — the cheapest call. USE WHEN: only a version string matters (pinning a dep, answering 'what version of X'). If you also need health/vulns use check_package. RETURNS: {latest, deprecated, published_at}.",
    annotations: {
      title: "get_latest_version",
      readOnlyHint: true,
      destructiveHint: false,
      idempotentHint: true,
      openWorldHint: true,
    },
    inputSchema: {
      type: "object",
      properties: {
        ecosystem: { type: "string", enum: ECOSYSTEMS },
        package: { type: "string" },
      },
      required: ["ecosystem", "package"],
    },
  },
  {
    name: "get_health_score",
    description:
      "Single 0-100 health score — cheapest go/no-go gate (>=70 safe). USE WHEN: CI gating or pkg already screened for malware/typos. NOT a first screen — run check_malicious + check_typosquat first. For a verbal verdict use get_package_prompt. RETURNS: {score, verdict}.",
    annotations: {
      title: "get_health_score",
      readOnlyHint: true,
      destructiveHint: false,
      idempotentHint: true,
      openWorldHint: true,
    },
    inputSchema: {
      type: "object",
      properties: {
        ecosystem: { type: "string", enum: ECOSYSTEMS },
        package: { type: "string" },
      },
      required: ["ecosystem", "package"],
    },
  },
  {
    name: "install_command",
    description:
      "Canonical install command(s) across every package manager of the ecosystem (npm/pnpm/yarn/bun, pip/uv/poetry, cargo, go, composer, maven+gradle, nuget, …). USE WHEN: emitting an install line and you want correct flags. RETURNS: {primary, variants[]}.",
    annotations: {
      title: "install_command",
      readOnlyHint: true,
      idempotentHint: true,
      openWorldHint: true,
    },
    inputSchema: {
      type: "object",
      properties: {
        ecosystem: { type: "string", enum: ECOSYSTEMS },
        package: { type: "string" },
        version: { type: "string", description: "Optional explicit version; defaults to latest." },
      },
      required: ["ecosystem", "package"],
    },
  },

  // ── 3. Full package reports ─────────────────────────────────────────
  {
    name: "get_package_prompt",
    description:
      "LLM-optimised package brief — plain text ~300 tokens (~75% cheaper than JSON). Verdict (SAFE/AVOID/URGENT/MALICIOUS) + health + vulns + alternatives + maintainer alerts. USE WHEN: you want to reason over a package and drop the output directly in context; 'is X safe'. PREFER THIS over check_package in 95% of LLM cases. RETURNS: plain-text brief.",
    annotations: {
      title: "get_package_prompt",
      readOnlyHint: true,
      destructiveHint: false,
      idempotentHint: true,
      openWorldHint: true,
    },
    inputSchema: {
      type: "object",
      properties: {
        ecosystem: { type: "string", enum: ECOSYSTEMS },
        package: { type: "string" },
      },
      required: ["ecosystem", "package"],
    },
  },
  {
    name: "check_package",
    description:
      "Full machine-readable JSON report (~2k tokens). USE WHEN: you need to programmatically parse specific fields (CI gating, UI, sub-field extraction). Otherwise prefer get_package_prompt. RETURNS: {package, health:{score}, vulnerabilities[], latest, deprecated, maintainers, recommendation}.",
    annotations: {
      title: "check_package",
      readOnlyHint: true,
      destructiveHint: false,
      idempotentHint: true,
      openWorldHint: true,
    },
    inputSchema: {
      type: "object",
      properties: {
        ecosystem: { type: "string", enum: ECOSYSTEMS },
        package: { type: "string", description: "Package name (e.g. 'express', 'fastapi', 'serde')." },
        version: { type: "string", description: "Specific version (optional; default = latest)." },
      },
      required: ["ecosystem", "package"],
    },
  },

  // ── 4. Vulnerability / alternative / migration decisions ────────────
  {
    name: "get_vulnerabilities",
    description:
      "CVE/OSV advisories affecting the latest (or specified) version. USE WHEN: security-sensitive project; user asks 'any CVEs in X'; you already know the pkg exists. RETURNS: {vulnerability_count, vulnerabilities[]: {id, severity, cvss, fixed_in}}.",
    annotations: {
      title: "get_vulnerabilities",
      readOnlyHint: true,
      destructiveHint: false,
      idempotentHint: true,
      openWorldHint: true,
    },
    inputSchema: {
      type: "object",
      properties: {
        ecosystem: { type: "string", enum: ECOSYSTEMS },
        package: { type: "string" },
      },
      required: ["ecosystem", "package"],
    },
  },
  {
    name: "find_alternatives",
    description:
      "Curated replacements for deprecated/unhealthy packages, including stdlib built-ins (e.g. `fs.rm` for rimraf). USE WHEN: pkg flagged AVOID/URGENT; 'what to use instead of X'; before guessing a replacement name. RETURNS: {alternatives[]: {name, reason, is_stdlib}}.",
    annotations: {
      title: "find_alternatives",
      readOnlyHint: true,
      destructiveHint: false,
      idempotentHint: true,
      openWorldHint: true,
    },
    inputSchema: {
      type: "object",
      properties: {
        ecosystem: { type: "string", enum: ECOSYSTEMS },
        package: { type: "string" },
      },
      required: ["ecosystem", "package"],
    },
  },
  {
    name: "get_migration_path",
    description:
      "Prescriptive migration plan between DIFFERENT packages — rationale + literal code diff + breaking changes + effort minutes. USE WHEN: replacing `request`→`axios`, `moment`→`dayjs`, `flask`→`fastapi`, etc.; both endpoints known. RETURNS: {rationale, diff, breaking_changes[], estimated_minutes}.",
    annotations: {
      title: "get_migration_path",
      readOnlyHint: true,
      destructiveHint: false,
      idempotentHint: true,
      openWorldHint: true,
    },
    inputSchema: {
      type: "object",
      properties: {
        ecosystem: { type: "string", enum: ECOSYSTEMS },
        from_package: { type: "string", description: "Deprecated/legacy package to migrate away from." },
        to_package: { type: "string", description: "Modern replacement package." },
      },
      required: ["ecosystem", "from_package", "to_package"],
    },
  },
  {
    name: "get_breaking_changes",
    description:
      "Breaking changes between two majors of the SAME package (`next@14`→`15`). USE WHEN: user is bumping a major; before recommending a major upgrade. Different from get_migration_path (same pkg vs. different pkg). RETURNS: {breaking_changes[]: {area, description, hint}}.",
    annotations: {
      title: "get_breaking_changes",
      readOnlyHint: true,
      destructiveHint: false,
      idempotentHint: true,
      openWorldHint: true,
    },
    inputSchema: {
      type: "object",
      properties: {
        ecosystem: { type: "string", enum: ECOSYSTEMS },
        package: { type: "string" },
        from_version: { type: "string" },
        to_version: { type: "string" },
      },
      required: ["ecosystem", "package"],
    },
  },
  {
    name: "pin_safe",
    description:
      "Highest version below the chosen CVE severity tier, respecting a semver constraint. USE WHEN: writing a package.json/requirements.txt line; resolving dependabot by lowest-risk patched version. RETURNS: {recommended_version, walk_log[]}.",
    annotations: {
      title: "pin_safe",
      readOnlyHint: true,
      idempotentHint: true,
      openWorldHint: true,
    },
    inputSchema: {
      type: "object",
      properties: {
        ecosystem: { type: "string", enum: ECOSYSTEMS },
        package: { type: "string" },
        min_severity: {
          type: "string",
          enum: ["critical", "high", "medium", "low"],
          description: "Lowest severity to exclude. Default: high (excludes critical+high).",
        },
        constraint: {
          type: "string",
          description: "npm-style constraint: ^X.Y.Z, ~X.Y.Z, >=X.Y.Z, or exact X.Y.Z.",
        },
        include_prerelease: { type: "boolean", default: false },
      },
      required: ["ecosystem", "package"],
    },
  },

  // ── 5. Multi-package analyses ───────────────────────────────────────
  {
    name: "scan_project",
    description:
      "Audit a project's dependencies in one shot. Returns a single-sentence `verdict` (e.g. \"DO NOT INSTALL — 1 hallucinated: fastapi-turbo\") that an agent can paste into its reply, plus per-package health/vulns/recommendation. Detects hallucinated packages, deprecated, typosquats, critical vulnerabilities. Accepts EITHER {ecosystem, packages:[name@ver, …]} (up to 100, returns JSON) OR {packages:[{ecosystem, package}, …]} (up to 50, mixed ecosystems, returns text brief). USE WHEN: user pastes package.json/requirements.txt/Cargo.toml; agent generated install command; 'is my stack OK'. RETURNS: JSON with `verdict`, `project_risk`, `summary.hallucinated_packages`, `summary.deprecated_packages`, per-package health.",
    annotations: {
      title: "scan_project",
      readOnlyHint: true,
      destructiveHint: false,
      idempotentHint: true,
      openWorldHint: true,
    },
    inputSchema: {
      type: "object",
      properties: {
        ecosystem: { type: "string", enum: ECOSYSTEMS, description: "Required when packages is a string array." },
        packages: {
          description: "Either ['express','lodash@4.17.0'] (single ecosystem, up to 100) or [{ecosystem, package}, …] (mixed, up to 50).",
        },
      },
      required: ["packages"],
    },
  },
  {
    name: "compare_packages",
    description:
      "Side-by-side comparison (health, vulns, downloads, maintainers, last release) of 2-10 packages in the same ecosystem. USE WHEN: 'X vs Y' / 'should I pick X or Y'. RETURNS: table-shaped JSON, one row per package.",
    annotations: {
      title: "compare_packages",
      readOnlyHint: true,
      destructiveHint: false,
      idempotentHint: true,
      openWorldHint: true,
    },
    inputSchema: {
      type: "object",
      properties: {
        ecosystem: { type: "string", enum: ECOSYSTEMS },
        packages: {
          type: "array",
          items: { type: "string" },
          minItems: 2,
          maxItems: 10,
          description: "Package names to compare, e.g. ['express','fastify','hono'].",
        },
      },
      required: ["ecosystem", "packages"],
    },
  },
  {
    name: "check_compatibility",
    description:
      "Is this specific multi-package version combo verified to work together? USE WHEN: pinning a stack (next@15 + react@19 + node@22); before recommending a version matrix. RETURNS: {compatible, conflicts[], notes}.",
    annotations: {
      title: "check_compatibility",
      readOnlyHint: true,
      destructiveHint: false,
      idempotentHint: true,
      openWorldHint: true,
    },
    inputSchema: {
      type: "object",
      properties: {
        packages: {
          type: "object",
          description: "Package -> version map, e.g. {\"next\":\"15\",\"react\":\"19\"}.",
          additionalProperties: { type: "string" },
        },
      },
      required: ["packages"],
    },
  },

  // ── 6. Error / bug knowledge base ───────────────────────────────────
  {
    name: "resolve_error",
    description:
      "Map error OR free-text query to a verified fix. USE WHEN: user pastes a concrete error/stack (ENOENT, ImportError, build failure) — pass `error`. OR user describes a symptom ('webpack slow', 'pip stuck') — pass `query`. Always prefer this over guessing a fix. RETURNS: exact-match {status, solution, confidence, source_url} or search results [{title, summary, source_url}].",
    annotations: {
      title: "resolve_error",
      readOnlyHint: true,
      destructiveHint: false,
      idempotentHint: true,
      openWorldHint: true,
    },
    inputSchema: {
      type: "object",
      properties: {
        error: { type: "string", description: "Concrete error message / stack trace. Triggers exact-match lookup." },
        query: { type: "string", description: "Free-text symptom description. Triggers KB search." },
        context: { type: "object", description: "Optional context for error-mode calls (ecosystem, package, version)." },
        limit: { type: "integer", minimum: 1, maximum: 20, default: 10, description: "Max search results (query mode only)." },
      },
    },
  },
  {
    name: "get_known_bugs",
    description:
      "Non-CVE known bugs for a specific package version. USE WHEN: unexpected behavior that is NOT a security issue; a pinned version misbehaves. RETURNS: {bugs[]: {title, fixed_in, workaround}}.",
    annotations: {
      title: "get_known_bugs",
      readOnlyHint: true,
      destructiveHint: false,
      idempotentHint: true,
      openWorldHint: true,
    },
    inputSchema: {
      type: "object",
      properties: {
        ecosystem: { type: "string", enum: ECOSYSTEMS },
        package: { type: "string" },
        version: { type: "string" },
      },
      required: ["ecosystem", "package"],
    },
  },

  // ── 7. Supply-chain deep signals ────────────────────────────────────
  {
    name: "get_trust_signals",
    description:
      "One-call aggregate of ALL non-CVE supply-chain trust signals: maintainer trust (bus factor, ownership changes), OpenSSF Scorecard, quality (criticality, release velocity, publish security), and SLSA/Sigstore provenance. USE WHEN: deep-vetting a package beyond CVEs (hardened/regulated env, SBOM/compliance, small-pkg ownership review, choosing between healthy candidates). Runs 4 backend endpoints in parallel. RETURNS: {maintainer, scorecard, quality, provenance} — each may be null if its backend call failed.",
    annotations: {
      title: "get_trust_signals",
      readOnlyHint: true,
      destructiveHint: false,
      idempotentHint: true,
      openWorldHint: true,
    },
    inputSchema: {
      type: "object",
      properties: {
        ecosystem: { type: "string", enum: ECOSYSTEMS },
        package: { type: "string" },
      },
      required: ["ecosystem", "package"],
    },
  },
  {
    name: "get_trending",
    description:
      "Live trending packages with rank-delta and weekly growth %. USE WHEN: 'what is rising in npm/PyPI/Cargo right now'; recommendation not biased by training-data cutoff. RETURNS: {items[]: {name, rank, rank_delta, weekly_growth_pct}}.",
    annotations: {
      title: "get_trending",
      readOnlyHint: true,
      destructiveHint: false,
      idempotentHint: true,
      openWorldHint: true,
    },
    inputSchema: {
      type: "object",
      properties: {
        ecosystem: { type: "string", enum: ECOSYSTEMS, description: "Optional. If omitted returns cross-ecosystem trending." },
        scope: { type: "string", enum: ["all","week","day"], description: "Time window. Defaults to week." },
        limit: { type: "integer", description: "Max results, 1-50. Default 20." },
      },
    },
  },

  // ── 8. Feedback channel (NOT idempotent — creates a ticket) ─────────
  {
    name: "contact_depscope",
    description:
      "Inbound ticket: bug/listing/security/anomaly/partnership. USE WHEN: reporting wrong data (`bug`), requesting a new pkg/ecosystem index (`listing`), disclosing a DepScope security issue (`security`), flagging a concrete mismatch in another tool's output vs. authoritative source (`anomaly` — provide tool_called+observed+expected), or partnership/press (`partnership`). RETURNS: {ticket_id} or {anomaly_id}.",
    annotations: {
      title: "contact_depscope",
      readOnlyHint: false,
      destructiveHint: false,
      idempotentHint: false,
      openWorldHint: true,
    },
    inputSchema: {
      type: "object",
      properties: {
        kind: { type: "string", enum: ["bug","listing","security","anomaly","partnership"], description: "Ticket category. `anomaly` routes to structured anomaly triage (requires tool_called/observed/expected)." },
        email: { type: "string", description: "Reply-to email of the requester (required for bug/listing/security/partnership)." },
        subject: { type: "string", description: "Short subject line (3-200 chars)." },
        body: { type: "string", description: "Message body (10-8000 chars). Be specific: include package name, ecosystem, error trace, repro steps when applicable." },
        name: { type: "string", description: "Sender display name (optional)." },
        company: { type: "string", description: "Company / organization (optional)." },
        tool_called: { type: "string", description: "For kind=anomaly: DepScope tool that produced the anomaly (e.g. check_package, get_migration_path)." },
        ecosystem: { type: "string", description: "For kind=anomaly: ecosystem of the involved package, if any." },
        package: { type: "string", description: "For kind=anomaly: package name involved, if any." },
        version: { type: "string", description: "For kind=anomaly: package version involved, if any." },
        observed: { type: "string", description: "For kind=anomaly: what DepScope returned (1-1500 chars)." },
        expected: { type: "string", description: "For kind=anomaly: what you expected to see (1-1500 chars). Be concrete." },
        evidence_url: { type: "string", description: "For kind=anomaly: URL to authoritative source (registry page, GHSA, CVE, repo, ...) supporting your expectation." },
      },
    },
  },
];

function headers(toolName) {
  const h = { "User-Agent": "DepScope-MCP/0.4.1" };
  if (API_KEY) h["X-API-Key"] = API_KEY;
  // MCP tool attribution: forward the MCP tool name so the backend can
  // record which tool originated the HTTP call (see api_usage.source =
  // "mcp:<tool>"). Back-compat: if omitted, source stays "mcp".
  if (toolName) h["X-MCP-Tool"] = String(toolName).slice(0, 64);
  return h;
}

async function getJson(path, toolName) {
  const res = await fetch(`${API_BASE}${path}`, { headers: headers(toolName) });
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
  return res.json();
}
async function getText(path, toolName) {
  const res = await fetch(`${API_BASE}${path}`, { headers: headers(toolName) });
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
  return res.text();
}
async function postJson(path, body, toolName) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { ...headers(toolName), "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
  return res.json();
}

function encodePkg(pkg) {
  if (!pkg || typeof pkg !== "string") {
    throw new Error("required argument 'package' is missing or not a string");
  }
  return pkg.split("/").map(encodeURIComponent).join("/");
}

function requireArgs(args, names) {
  if (!args || typeof args !== "object") {
    throw new Error(`required arguments missing: ${names.join(", ")}`);
  }
  const missing = names.filter(n => !args[n] || (typeof args[n] === "string" && !args[n].trim()));
  if (missing.length > 0) {
    throw new Error(`required argument(s) missing or empty: ${missing.join(", ")}`);
  }
}

function ok(data) {
  const text = typeof data === "string" ? data : JSON.stringify(data, null, 2);
  return { content: [{ type: "text", text }] };
}
function fail(message) {
  return { content: [{ type: "text", text: `Error: ${message}` }], isError: true };
}

export async function handleToolCall(name, args) {
  // Tool-scoped helpers that auto-forward the MCP tool name to the backend
  // via X-MCP-Tool header (enriches api_usage.source = "mcp:<tool>").
  const gJ = (path) => getJson(path, name);
  const gT = (path) => getText(path, name);
  const pJ = (path, body) => postJson(path, body, name);
  try {
    // Validate common required args for tools that need ecosystem+package
    const _eco_pkg_tools = new Set([
      "check_package", "get_health_score", "get_vulnerabilities", "get_latest_version",
      "package_exists", "get_package_prompt", "ai_brief", "find_alternatives",
      "get_breaking_changes", "get_known_bugs", "check_malicious", "check_typosquat",
      "get_trust_signals", "install_command", "pin_safe",
    ]);
    if (_eco_pkg_tools.has(name)) {
      requireArgs(args, ["ecosystem", "package"]);
    }
    switch (name) {
      // Back-compat alias: ai_brief was merged into get_package_prompt.
      case "ai_brief":
      case "get_package_prompt":
        return ok(await gT(`/api/prompt/${args.ecosystem}/${encodePkg(args.package)}`));

      case "get_migration_path":
        return ok(await gJ(`/api/migration/${args.ecosystem}/${encodeURIComponent(args.from_package)}/${encodeURIComponent(args.to_package)}`));
      // Back-compat alias: report_anomaly was merged into contact_depscope
      // with kind=anomaly. Force the kind here so old callers keep working.
      case "report_anomaly":
        args = { ...args, kind: "anomaly" };
        // fallthrough
      case "contact_depscope": {
        if (args.kind === "anomaly") {
          const body = JSON.stringify({
            tool_called: args.tool_called,
            ecosystem: args.ecosystem || "",
            package: args.package || "",
            version: args.version || "",
            observed: args.observed,
            expected: args.expected,
            evidence_url: args.evidence_url || "",
            source: "mcp",
          });
          const res = await fetch(`${API_BASE}/api/anomaly`, {
            method: "POST",
            headers: { "Content-Type": "application/json", "X-Depscope-Source": "mcp", "X-MCP-Tool": name },
            body,
          });
          if (!res.ok) return fail(`contact_depscope(anomaly) failed: ${res.status} ${await res.text().catch(()=>"")}`);
          return ok(await res.json());
        }
        const body = JSON.stringify({
          email: args.email,
          subject: args.subject,
          body: args.body,
          type: args.kind || args.type || "other",
          name: args.name || "",
          company: args.company || "",
          source: "mcp",
          consent: true,
        });
        const res = await fetch(`${API_BASE}/api/contact`, {
          method: "POST",
          headers: { "Content-Type": "application/json", "X-Depscope-Source": "mcp", "X-MCP-Tool": name },
          body,
        });
        if (!res.ok) return fail(`contact_depscope failed: ${res.status} ${await res.text().catch(()=>"")}`);
        return ok(await res.json());
      }
      case "get_trending": {
        const params = new URLSearchParams();
        if (args.ecosystem) params.set("ecosystem", args.ecosystem);
        if (args.scope) params.set("scope", args.scope);
        if (args.limit) params.set("limit", String(args.limit));
        const qs = params.toString();
        return ok(await gJ(`/api/trending${qs ? "?" + qs : ""}`));
      }
      case "check_package": {
        const pkg = encodePkg(args.package);
        let path = `/api/check/${args.ecosystem}/${pkg}`;
        if (args.version) path += `?version=${encodeURIComponent(args.version)}`;
        return ok(await gJ(path));
      }
      case "get_health_score":
        return ok(await gJ(`/api/health/${args.ecosystem}/${encodePkg(args.package)}`));
      case "get_vulnerabilities":
        return ok(await gJ(`/api/vulns/${args.ecosystem}/${encodePkg(args.package)}`));
      case "get_latest_version":
        return ok(await gJ(`/api/latest/${args.ecosystem}/${encodePkg(args.package)}`));
      case "package_exists":
        return ok(await gJ(`/api/exists/${args.ecosystem}/${encodePkg(args.package)}`));
      case "compare_packages": {
        let pkgs = args.packages;
        if (typeof pkgs === "string") pkgs = pkgs.split(",").map(x => x.trim()).filter(Boolean);
        if (!Array.isArray(pkgs)) return fail("packages must be array or comma-separated string");
        const csv = pkgs.map(encodeURIComponent).join(",");
        return ok(await gJ(`/api/compare/${args.ecosystem}/${csv}`));
      }

      // scan_project: accepts 3 shapes —
      //   a) {ecosystem, packages: ['name','name@ver',...]}        → /api/scan (single-eco)
      //   b) {ecosystem, packages: {name: version}}                 → /api/scan (single-eco)
      //   c) {packages: [{ecosystem, package}, ...]} (mixed ecos)   → /api/ai/stack (text brief)
      // Back-compat: audit_stack was merged into scan_project; callers still
      // passing the mixed-ecosystem shape hit branch (c).
      case "audit_stack":
      case "scan_project": {
        let pkgs = args.packages;
        if (typeof pkgs === "string") { try { pkgs = JSON.parse(pkgs); } catch {} }

        // Mixed-ecosystem list → stack brief
        if (Array.isArray(pkgs) && pkgs.length > 0 && typeof pkgs[0] === "object" && pkgs[0] && "ecosystem" in pkgs[0]) {
          const body = JSON.stringify({ packages: pkgs, format: "text" });
          const res = await fetch(`${API_BASE}/api/ai/stack`, {
            method: "POST",
            headers: { "Content-Type": "application/json", "X-MCP-Tool": name },
            body,
          });
          if (!res.ok) return fail(`scan_project (stack) failed: ${res.status}`);
          return ok(await res.text());
        }

        // Single-ecosystem list → /api/scan; backend expects {name: version}
        if (Array.isArray(pkgs)) {
          pkgs = Object.fromEntries(pkgs.map(e => {
            const at = typeof e === "string" ? e.lastIndexOf("@") : -1;
            return at > 0 ? [e.slice(0, at), e.slice(at + 1)] : [e, "*"];
          }));
        }
        if (!pkgs || typeof pkgs !== "object" || Object.keys(pkgs).length === 0) {
          return fail("\"packages\" must be a non-empty array or {name: version} object");
        }
        if (!args.ecosystem) {
          return fail("\"ecosystem\" is required when packages is a single-ecosystem list");
        }
        return ok(await pJ("/api/scan", { ecosystem: args.ecosystem, packages: pkgs }));
      }

      case "find_alternatives":
        return ok(await gJ(`/api/alternatives/${args.ecosystem}/${encodePkg(args.package)}`));
      case "get_breaking_changes": {
        const pkg = encodePkg(args.package);
        const qs = new URLSearchParams();
        if (args.from_version) qs.set("from_version", args.from_version);
        if (args.to_version) qs.set("to_version", args.to_version);
        const suffix = qs.toString() ? `?${qs}` : "";
        return ok(await gJ(`/api/breaking/${args.ecosystem}/${pkg}${suffix}`));
      }
      case "get_known_bugs": {
        const pkg = encodePkg(args.package);
        const suffix = args.version ? `?version=${encodeURIComponent(args.version)}` : "";
        return ok(await gJ(`/api/bugs/${args.ecosystem}/${pkg}${suffix}`));
      }
      case "check_compatibility": {
        let pkgs = args.packages;
        // Accept multiple input shapes:
        //  - object: {"next":"16","react":"19"} (canonical)
        //  - JSON string: "{\"next\":\"16\"}"
        //  - dep-syntax string: "next@16,react@19" (LLM-friendly)
        if (typeof pkgs === "string") {
          // Try JSON first
          try { pkgs = JSON.parse(pkgs); } catch {
            // Fall back to dep-syntax parser
            const obj = {};
            for (const part of pkgs.split(",")) {
              const trimmed = part.trim();
              if (!trimmed) continue;
              const idx = trimmed.lastIndexOf("@");
              if (idx > 0) {
                const name = trimmed.slice(0, idx).trim();
                const ver = trimmed.slice(idx + 1).trim();
                if (name && ver) obj[name] = ver;
              }
            }
            pkgs = obj;
          }
        }
        if (!pkgs || typeof pkgs !== "object" || Array.isArray(pkgs) || Object.keys(pkgs).length === 0) {
          return fail("\"packages\" must be {\"next\":\"16\",\"react\":\"19\"} OR \"next@16,react@19\"");
        }
        return ok(await pJ("/api/compat", { packages: pkgs }));
      }
      case "resolve_error": {
        // Dual-mode: exact-match on `error` (POST /api/error/resolve) OR
        // free-text search on `query` (GET /api/error?q=...).
        if (args.error) {
          return ok(await pJ(`/api/error/resolve`, { error: args.error, context: args.context }));
        }
        if (args.query) {
          const qs = new URLSearchParams({ q: args.query });
          if (args.limit) qs.set("limit", String(args.limit));
          return ok(await gJ(`/api/error?${qs}`));
        }
        return fail("resolve_error requires either `error` (exact match) or `query` (free-text search)");
      }
      // Back-compat alias: search_errors was merged into resolve_error.
      case "search_errors": {
        const qs = new URLSearchParams({ q: args.query || "" });
        if (args.limit) qs.set("limit", String(args.limit));
        return ok(await gJ(`/api/error?${qs}`));
      }
      case "check_malicious":
        return ok(await gJ(`/api/malicious/${args.ecosystem}/${args.package}`));
      case "check_typosquat":
        return ok(await gJ(`/api/typosquat/${args.ecosystem}/${args.package}`));
      // Back-compat aliases: the 4 trust signals were merged into
      // get_trust_signals, but we still honour old names by hitting their
      // original backend endpoints.
      case "get_scorecard":
        return ok(await gJ(`/api/scorecard/${args.ecosystem}/${args.package}`));
      case "get_maintainer_trust":
        return ok(await gJ(`/api/maintainers/${args.ecosystem}/${args.package}`));
      case "get_quality":
        return ok(await gJ(`/api/quality/${args.ecosystem}/${args.package}`));
      case "get_provenance":
        return ok(await gJ(`/api/provenance/${args.ecosystem}/${args.package}`));
      case "get_trust_signals": {
        const pkg = args.package;
        const eco = args.ecosystem;
        const safe = (p) => gJ(p).catch(() => null);
        const [maintainer, scorecard, quality, provenance] = await Promise.all([
          safe(`/api/maintainers/${eco}/${pkg}`),
          safe(`/api/scorecard/${eco}/${pkg}`),
          safe(`/api/quality/${eco}/${pkg}`),
          safe(`/api/provenance/${eco}/${pkg}`),
        ]);
        return ok({ maintainer, scorecard, quality, provenance });
      }
      case "check_bulk":
        return ok(await pJ(`/api/check_bulk`, { items: args.items || [] }));
      case "install_command": {
        const qs = new URLSearchParams();
        if (args.version) qs.set("version", args.version);
        const q = qs.toString();
        return ok(await gJ(`/api/install/${args.ecosystem}/${args.package}${q ? "?" + q : ""}`));
      }
      case "pin_safe": {
        const qs = new URLSearchParams();
        if (args.min_severity) qs.set("min_severity", args.min_severity);
        if (args.constraint) qs.set("constraint", args.constraint);
        if (args.include_prerelease) qs.set("include_prerelease", "true");
        const q = qs.toString();
        return ok(await gJ(`/api/pin_safe/${args.ecosystem}/${args.package}${q ? "?" + q : ""}`));
      }
      default:
        return fail(`Unknown tool: ${name}`);
    }
  } catch (e) {
    return fail(e.message);
  }
}

// ────────────────────────────────────────────────────────────────────────
// Server-level instructions injected into client system prompt at handshake.
// These tell the model WHEN to invoke DepScope proactively. Without this,
// the MCP tools sit dormant until the user explicitly asks for them.
// ────────────────────────────────────────────────────────────────────────
export const SERVER_INSTRUCTIONS = `DepScope: dependency safety & intelligence MCP for AI agents. Covers 19 package ecosystems: npm, PyPI, Cargo, Go, Maven, NuGet, RubyGems, Composer, Pub, Hex, Swift, CocoaPods, CPAN, Hackage, CRAN, Conda, Homebrew, JSR, Julia.

INVOKE PROACTIVELY — before suggesting any package install, version bump, lockfile change, or when a 'module not found' / 'package broken' error appears. Do NOT wait for the user to ask.

Three pillars:
- TOKEN-SAVING: one DepScope call replaces a web search + readme fetch + npm/pypi page browse.
- ENERGY-SAVING: skip installs of malicious, typosquatted, deprecated or hallucinated packages — no wasted CI cycles or rollbacks.
- SECURITY: stop supply-chain attacks (malware, typosquats, hostile takeovers, known CVEs) BEFORE the install command leaves your reply.

Standard flow for any new package:
1. check_malicious + check_typosquat — security gate (~50ms)
2. check_package OR get_health_score — verdict
3. install_command — returns the safe pinned command

Batch installs (>=2 packages): use check_bulk in ONE call (≤100 items, <100ms).
Lockfile / requirements.txt / package.json change: use scan_project.
Version bumps (X@1 → X@2): use get_breaking_changes + get_migration_path.
Diagnose 'module not found' / 'X.Y broken' errors: use resolve_error and get_known_bugs.
Choosing between libraries: use find_alternatives and compare_packages.

All tools are read-only, zero-auth, free. Never destructive. Latency typically 50-300ms per call.`;
