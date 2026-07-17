#!/usr/bin/env node
"use strict";

const { generateChangelog, suggestVersionBump } = require("../lib/generator");
const { getGitLog, getLatestTag, getRemoteUrl } = require("../lib/git");
const { resolve } = require("node:path");

const TOOLS = [
  {
    name: "changelogai_generate",
    description: "Generate a changelog from git history. Returns markdown, JSON, or plain text.",
    inputSchema: {
      type: "object",
      properties: {
        repo: { type: "string", description: "Path to git repository", default: "." },
        from: { type: "string", description: "Start ref (tag/commit). Default: latest tag" },
        to: { type: "string", description: "End ref. Default: HEAD", default: "HEAD" },
        format: { type: "string", enum: ["markdown", "json", "plain"], default: "markdown" },
        group: { type: "boolean", description: "Group commits by type", default: true },
        maxCommits: { type: "number", description: "Max commits to process", default: 500 },
      },
    },
  },
  {
    name: "changelogai_version_bump",
    description: "Analyze git commits and suggest next semver bump (major/minor/patch).",
    inputSchema: {
      type: "object",
      properties: {
        repo: { type: "string", description: "Path to git repository", default: "." },
        from: { type: "string", description: "Start ref (tag/commit). Default: latest tag" },
        to: { type: "string", description: "End ref. Default: HEAD", default: "HEAD" },
      },
    },
  },
];

function handleGenerate(args) {
  const repoPath = resolve(args.repo || ".");
  const fromRef = args.from || getLatestTag(repoPath);
  const toRef = args.to || "HEAD";
  if (!fromRef) throw new Error("No tags or commits found in repository");
  const commits = getGitLog(repoPath, fromRef, toRef, args.maxCommits || 500);
  if (commits.length === 0) return { content: [{ type: "text", text: "No commits found in range." }] };
  const repoUrl = getRemoteUrl(repoPath);
  return generateChangelog(commits, {
    format: args.format || "markdown",
    group: args.group !== false,
    ai: false,
    versionBump: false,
    repoUrl,
    fromRef,
    toRef,
  }).then((text) => ({ content: [{ type: "text", text }] }));
}

function handleVersionBump(args) {
  const repoPath = resolve(args.repo || ".");
  const fromRef = args.from || getLatestTag(repoPath);
  const toRef = args.to || "HEAD";
  if (!fromRef) throw new Error("No tags or commits found in repository");
  const commits = getGitLog(repoPath, fromRef, toRef, 500);
  if (commits.length === 0) return { content: [{ type: "text", text: "No commits found." }] };
  const bump = suggestVersionBump(commits);
  return { content: [{ type: "text", text: `Suggested bump: ${bump} (${commits.length} commits analyzed)` }] };
}

// JSON-RPC over stdio
let buffer = "";
process.stdin.setEncoding("utf8");
process.stdin.on("data", (chunk) => {
  buffer += chunk;
  let newline;
  while ((newline = buffer.indexOf("\n")) !== -1) {
    const line = buffer.slice(0, newline).trim();
    buffer = buffer.slice(newline + 1);
    if (line) processMessage(line);
  }
});

function send(msg) {
  process.stdout.write(JSON.stringify(msg) + "\n");
}

async function processMessage(line) {
  let req;
  try {
    req = JSON.parse(line);
  } catch {
    send({ jsonrpc: "2.0", error: { code: -32700, message: "Parse error" }, id: null });
    return;
  }

  const { method, params, id } = req;

  try {
    if (method === "initialize") {
      send({
        jsonrpc: "2.0",
        id,
        result: {
          protocolVersion: "2024-11-05",
          capabilities: { tools: {} },
          serverInfo: { name: "changelogai", version: require("../package.json").version },
        },
      });
    } else if (method === "notifications/initialized") {
      // no response needed
    } else if (method === "tools/list") {
      send({ jsonrpc: "2.0", id, result: { tools: TOOLS } });
    } else if (method === "tools/call") {
      const { name, arguments: args } = params;
      let result;
      if (name === "changelogai_generate") result = await handleGenerate(args || {});
      else if (name === "changelogai_version_bump") result = handleVersionBump(args || {});
      else throw new Error(`Unknown tool: ${name}`);
      send({ jsonrpc: "2.0", id, result });
    } else if (id !== undefined) {
      send({ jsonrpc: "2.0", id, error: { code: -32601, message: `Unknown method: ${method}` } });
    }
  } catch (e) {
    if (id !== undefined) {
      send({ jsonrpc: "2.0", id, result: { content: [{ type: "text", text: `Error: ${e.message}` }], isError: true } });
    }
  }
}
