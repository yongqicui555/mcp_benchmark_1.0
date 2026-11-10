#!/usr/bin/env node

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { createRequire } from "module";
import path from "path";
import fs from "fs";

const require = createRequire(import.meta.url);
const { Scanner } = require("ai-scanner");

// ─── Server Setup ────────────────────────────────────────────────────────────
const server = new McpServer({
  name: "ai-scanner",
  version: "1.0.0",
});

// ─── Helper: Run scanner with options ────────────────────────────────────────
function runScan(directory, options = {}) {
  const rootDir = path.resolve(directory);

  if (!fs.existsSync(rootDir)) {
    throw new Error(`Directory not found: ${rootDir}`);
  }

  if (!fs.statSync(rootDir).isDirectory()) {
    throw new Error(`Not a directory: ${rootDir}`);
  }

  const scanner = new Scanner({
    rootDir,
    includeEndpoints: options.includeEndpoints !== false,
    includeModels: options.includeModels !== false,
    scanEnv: options.scanEnv === true,
    aiOnly: options.aiOnly === true,
  });

  return scanner.scan();
}

// ─── Tool 1: scan_directory ──────────────────────────────────────────────────
// Full scan — returns all findings grouped by type
server.tool(
  "scan_directory",
  "Scan a directory for LLM SDK usage, AI frameworks, exposed API tokens, and hardcoded secrets. Returns all findings grouped by type (token, secret, sdk, framework, endpoint, model) with file locations and severity levels.",
  {
    directory: z
      .string()
      .describe("Absolute or relative path to the directory to scan"),
    ai_only: z
      .boolean()
      .optional()
      .default(false)
      .describe("If true, only scan for AI-specific patterns (skip generic secrets like Stripe, GitHub tokens, etc.)"),
    scan_env: z
      .boolean()
      .optional()
      .default(false)
      .describe("If true, include .env files in the scan (skipped by default)"),
    include_endpoints: z
      .boolean()
      .optional()
      .default(true)
      .describe("If true, detect LLM API endpoint URLs"),
    include_models: z
      .boolean()
      .optional()
      .default(true)
      .describe("If true, detect model name references (gpt-4, claude, etc.)"),
  },
  async ({ directory, ai_only, scan_env, include_endpoints, include_models }) => {
    try {
      const result = runScan(directory, {
        aiOnly: ai_only,
        scanEnv: scan_env,
        includeEndpoints: include_endpoints,
        includeModels: include_models,
      });

      // Group findings by type
      const grouped = {};
      for (const f of result.findings) {
        if (!grouped[f.type]) grouped[f.type] = [];
        grouped[f.type].push({
          name: f.patternName,
          severity: f.severity,
          file: f.file,
          line: f.line,
          match: f.matchedText,
        });
      }

      const report = {
        summary: {
          filesScanned: result.stats.filesScanned,
          filesSkipped: result.stats.filesSkipped,
          totalFindings: result.stats.totalFindings,
          critical: result.stats.criticalFindings,
          high: result.stats.highFindings,
          info: result.stats.infoFindings,
        },
        findings: grouped,
      };

      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(report, null, 2),
          },
        ],
      };
    } catch (err) {
      return {
        content: [{ type: "text", text: `Error: ${err.message}` }],
        isError: true,
      };
    }
  }
);

// ─── Tool 2: check_secrets ───────────────────────────────────────────────────
// Security-focused: only tokens and secrets, returns pass/fail
server.tool(
  "check_secrets",
  "Security check — scan a directory for exposed API tokens and hardcoded secrets only. Returns pass/fail with a list of any exposed credentials found. Use this before committing code or in CI pipelines.",
  {
    directory: z
      .string()
      .describe("Absolute or relative path to the directory to scan"),
    ai_only: z
      .boolean()
      .optional()
      .default(false)
      .describe("If true, only check for AI-specific tokens (skip Stripe, GitHub, etc.)"),
    scan_env: z
      .boolean()
      .optional()
      .default(false)
      .describe("If true, include .env files in the scan"),
  },
  async ({ directory, ai_only, scan_env }) => {
    try {
      const result = runScan(directory, {
        aiOnly: ai_only,
        scanEnv: scan_env,
        includeEndpoints: false,
        includeModels: false,
      });

      // Filter to only tokens and secrets
      const secrets = result.findings.filter(
        (f) => f.type === "token" || f.type === "secret"
      );

      const critical = secrets.filter((f) => f.severity === "critical");
      const high = secrets.filter((f) => f.severity === "high");
      const passed = critical.length === 0 && high.length === 0;

      const report = {
        passed,
        filesScanned: result.stats.filesScanned,
        exposedSecrets: secrets.length,
        critical: critical.length,
        high: high.length,
        findings: secrets.map((f) => ({
          severity: f.severity,
          name: f.patternName,
          file: f.file,
          line: f.line,
          match: f.matchedText,
        })),
      };

      const emoji = passed ? "✅" : "🚨";
      const summary = passed
        ? `${emoji} PASSED — No exposed secrets found across ${result.stats.filesScanned} files.`
        : `${emoji} FAILED — ${secrets.length} exposed secret(s) found (${critical.length} critical, ${high.length} high).`;

      return {
        content: [
          {
            type: "text",
            text: summary + "\n\n" + JSON.stringify(report, null, 2),
          },
        ],
      };
    } catch (err) {
      return {
        content: [{ type: "text", text: `Error: ${err.message}` }],
        isError: true,
      };
    }
  }
);

// ─── Tool 3: ai_inventory ────────────────────────────────────────────────────
// AI stack overview: which SDKs, frameworks, models, endpoints are used
server.tool(
  "ai_inventory",
  "Get an inventory of all AI/LLM technologies used in a codebase — which SDKs are imported, which frameworks are integrated, which models are referenced, and which provider APIs are called. No secret detection, just awareness.",
  {
    directory: z
      .string()
      .describe("Absolute or relative path to the directory to scan"),
  },
  async ({ directory }) => {
    try {
      const result = runScan(directory, {
        aiOnly: true,
        includeEndpoints: true,
        includeModels: true,
      });

      // Filter out tokens — this tool is about awareness, not security
      const aiFindings = result.findings.filter(
        (f) => f.type !== "token" && f.type !== "secret"
      );

      const sdks = [
        ...new Set(
          aiFindings.filter((f) => f.type === "sdk").map((f) => f.patternName)
        ),
      ];
      const frameworks = [
        ...new Set(
          aiFindings
            .filter((f) => f.type === "framework")
            .map((f) => f.patternName)
        ),
      ];
      const models = [
        ...new Set(
          aiFindings
            .filter((f) => f.type === "model")
            .map((f) => f.matchedText.replace(/['"]/g, ""))
        ),
      ];
      const endpoints = [
        ...new Set(
          aiFindings
            .filter((f) => f.type === "endpoint")
            .map((f) => f.matchedText)
        ),
      ];

      // Build file-level inventory
      const fileUsage = {};
      for (const f of aiFindings) {
        if (!fileUsage[f.file]) fileUsage[f.file] = [];
        fileUsage[f.file].push(`${f.patternName} (${f.type})`);
      }
      // Deduplicate per file
      for (const file of Object.keys(fileUsage)) {
        fileUsage[file] = [...new Set(fileUsage[file])];
      }

      const inventory = {
        filesScanned: result.stats.filesScanned,
        sdks,
        frameworks,
        models,
        endpoints,
        fileUsage,
      };

      const summary = [];
      if (sdks.length > 0) summary.push(`SDKs: ${sdks.join(", ")}`);
      if (frameworks.length > 0)
        summary.push(`Frameworks: ${frameworks.join(", ")}`);
      if (models.length > 0) summary.push(`Models: ${models.join(", ")}`);
      if (endpoints.length > 0)
        summary.push(`Endpoints: ${endpoints.join(", ")}`);

      const text =
        summary.length > 0
          ? `AI Stack (${result.stats.filesScanned} files scanned):\n${summary.join("\n")}`
          : `No AI/LLM usage detected across ${result.stats.filesScanned} files.`;

      return {
        content: [
          {
            type: "text",
            text: text + "\n\n" + JSON.stringify(inventory, null, 2),
          },
        ],
      };
    } catch (err) {
      return {
        content: [{ type: "text", text: `Error: ${err.message}` }],
        isError: true,
      };
    }
  }
);

// ─── Start ───────────────────────────────────────────────────────────────────
const transport = new StdioServerTransport();
await server.connect(transport);
