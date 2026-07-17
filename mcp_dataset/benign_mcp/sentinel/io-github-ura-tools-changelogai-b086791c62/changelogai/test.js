"use strict";

const { describe, it } = require("node:test");
const assert = require("node:assert/strict");
const { parseConventionalCommit } = require("./lib/git");
const { generateChangelog, suggestVersionBump } = require("./lib/generator");

// --- parseConventionalCommit ---

describe("parseConventionalCommit", () => {
  it("parses standard conventional commit", () => {
    const r = parseConventionalCommit("feat(auth): add login page");
    assert.equal(r.type, "feat");
    assert.equal(r.scope, "auth");
    assert.equal(r.breaking, false);
    assert.equal(r.description, "add login page");
  });

  it("parses commit without scope", () => {
    const r = parseConventionalCommit("fix: resolve crash on startup");
    assert.equal(r.type, "fix");
    assert.equal(r.scope, null);
    assert.equal(r.breaking, false);
    assert.equal(r.description, "resolve crash on startup");
  });

  it("detects breaking change via !", () => {
    const r = parseConventionalCommit("feat!: remove deprecated API");
    assert.equal(r.type, "feat");
    assert.equal(r.breaking, true);
  });

  it("detects breaking change via keyword in subject", () => {
    const r = parseConventionalCommit("feat: BREAKING CHANGE remove old endpoint");
    assert.equal(r.breaking, true);
  });

  it("detects breaking change with scope and !", () => {
    const r = parseConventionalCommit("refactor(core)!: rewrite parser");
    assert.equal(r.type, "refactor");
    assert.equal(r.scope, "core");
    assert.equal(r.breaking, true);
  });

  it("handles all standard types", () => {
    const types = ["feat", "fix", "docs", "refactor", "test", "chore", "style", "perf", "ci", "build"];
    for (const t of types) {
      const r = parseConventionalCommit(`${t}: some change`);
      assert.equal(r.type, t, `expected type "${t}"`);
    }
  });

  // Fallback keyword detection
  it("detects fix from prefix keyword", () => {
    const r = parseConventionalCommit("Fix the broken login flow");
    assert.equal(r.type, "fix");
  });

  it("detects feat from prefix keyword", () => {
    const r = parseConventionalCommit("Add new dashboard widget");
    assert.equal(r.type, "feat");
  });

  it("detects docs from prefix keyword", () => {
    const r = parseConventionalCommit("Update README with examples");
    assert.equal(r.type, "docs");
  });

  it("detects refactor from prefix keyword", () => {
    const r = parseConventionalCommit("Refactor auth module");
    assert.equal(r.type, "refactor");
  });

  it("detects test from prefix keyword", () => {
    const r = parseConventionalCommit("Test the new parser logic");
    assert.equal(r.type, "test");
  });

  it("detects chore from prefix keyword", () => {
    const r = parseConventionalCommit("Bump dependencies to latest");
    assert.equal(r.type, "chore");
  });

  it("detects perf from prefix keyword", () => {
    const r = parseConventionalCommit("Optimize database queries");
    assert.equal(r.type, "perf");
  });

  it("falls back to keyword-anywhere for fix", () => {
    const r = parseConventionalCommit("Resolve authentication bug in production");
    assert.equal(r.type, "fix");
  });

  it("falls back to keyword-anywhere for docs", () => {
    const r = parseConventionalCommit("Typo in the README documentation");
    assert.equal(r.type, "docs");
  });

  it("returns other for unrecognized commits", () => {
    const r = parseConventionalCommit("miscellaneous work");
    assert.equal(r.type, "other");
  });

  it("lowercases the type", () => {
    const r = parseConventionalCommit("FEAT(ui): big feature");
    assert.equal(r.type, "feat");
  });
});

// --- suggestVersionBump ---

describe("suggestVersionBump", () => {
  it("returns major for breaking changes", () => {
    const commits = [
      { type: "feat", breaking: true },
      { type: "fix", breaking: false },
    ];
    assert.equal(suggestVersionBump(commits), "major");
  });

  it("returns minor for features without breaking", () => {
    const commits = [
      { type: "feat", breaking: false },
      { type: "fix", breaking: false },
    ];
    assert.equal(suggestVersionBump(commits), "minor");
  });

  it("returns patch for fixes only", () => {
    const commits = [
      { type: "fix", breaking: false },
      { type: "chore", breaking: false },
    ];
    assert.equal(suggestVersionBump(commits), "patch");
  });

  it("returns patch for empty commits", () => {
    assert.equal(suggestVersionBump([]), "patch");
  });

  it("returns patch for chore-only commits", () => {
    const commits = [{ type: "chore", breaking: false }];
    assert.equal(suggestVersionBump(commits), "patch");
  });

  it("major takes priority over minor", () => {
    const commits = [
      { type: "feat", breaking: true },
      { type: "feat", breaking: false },
    ];
    assert.equal(suggestVersionBump(commits), "major");
  });
});

// --- generateChangelog ---

const MOCK_COMMITS = [
  {
    hash: "abc123def456", hashShort: "abc123d",
    author: "dev", email: "dev@test.com", date: "2026-03-28",
    subject: "feat(ui): add dark mode", body: "",
    type: "feat", scope: "ui", breaking: false, description: "add dark mode",
  },
  {
    hash: "def456abc789", hashShort: "def456a",
    author: "dev", email: "dev@test.com", date: "2026-03-27",
    subject: "fix: resolve memory leak", body: "",
    type: "fix", scope: null, breaking: false, description: "resolve memory leak",
  },
  {
    hash: "ghi789jkl012", hashShort: "ghi789j",
    author: "dev", email: "dev@test.com", date: "2026-03-26",
    subject: "feat!: remove legacy API", body: "",
    type: "feat", scope: null, breaking: true, description: "remove legacy API",
  },
];

describe("generateChangelog", () => {
  it("generates JSON format", async () => {
    const result = await generateChangelog(MOCK_COMMITS, {
      format: "json", group: false, ai: false, versionBump: false,
      fromRef: "v1.0.0", toRef: "v2.0.0", repoUrl: null,
    });
    const parsed = JSON.parse(result);
    assert.equal(parsed.range.from, "v1.0.0");
    assert.equal(parsed.range.to, "v2.0.0");
    assert.equal(parsed.commits.length, 3);
    assert.equal(parsed.commits[0].type, "feat");
    assert.equal(parsed.commits[2].breaking, true);
  });

  it("generates JSON with version bump", async () => {
    const result = await generateChangelog(MOCK_COMMITS, {
      format: "json", group: false, ai: false, versionBump: true,
      fromRef: "v1.0.0", toRef: "v2.0.0", repoUrl: null,
    });
    const parsed = JSON.parse(result);
    assert.equal(parsed.suggestedBump, "major");
  });

  it("generates plain format", async () => {
    const result = await generateChangelog(MOCK_COMMITS, {
      format: "plain", group: false, ai: false, versionBump: false,
      fromRef: "v1.0.0", toRef: "v2.0.0", repoUrl: null,
    });
    assert.ok(result.includes("abc123d"));
    assert.ok(result.includes("feat(ui): add dark mode"));
    assert.ok(result.includes("dev"));
  });

  it("generates flat markdown", async () => {
    const result = await generateChangelog(MOCK_COMMITS, {
      format: "markdown", group: false, ai: false, versionBump: false,
      fromRef: "v1.0.0", toRef: "v2.0.0", repoUrl: null,
    });
    assert.ok(result.includes("## v2.0.0"));
    assert.ok(result.includes("BREAKING CHANGES"));
    assert.ok(result.includes("remove legacy API"));
    assert.ok(result.includes("### Changes"));
  });

  it("generates grouped markdown", async () => {
    const result = await generateChangelog(MOCK_COMMITS, {
      format: "markdown", group: true, ai: false, versionBump: false,
      fromRef: "v1.0.0", toRef: "v2.0.0", repoUrl: null,
    });
    assert.ok(result.includes("### Features"));
    assert.ok(result.includes("### Bug Fixes"));
    assert.ok(result.includes("BREAKING CHANGES"));
  });

  it("includes repo links when repoUrl provided", async () => {
    const result = await generateChangelog(MOCK_COMMITS, {
      format: "markdown", group: false, ai: false, versionBump: false,
      fromRef: "v1.0.0", toRef: "v2.0.0", repoUrl: "https://github.com/test/repo",
    });
    assert.ok(result.includes("https://github.com/test/repo/commit/"));
    assert.ok(result.includes("https://github.com/test/repo/compare/"));
  });

  it("appends version bump suggestion", async () => {
    const result = await generateChangelog(MOCK_COMMITS, {
      format: "markdown", group: false, ai: false, versionBump: true,
      fromRef: "v1.0.0", toRef: "v2.0.0", repoUrl: null,
    });
    assert.ok(result.includes("Suggested version bump"));
    assert.ok(result.includes("major"));
  });

  it("handles scope display in markdown", async () => {
    const result = await generateChangelog(MOCK_COMMITS, {
      format: "markdown", group: false, ai: false, versionBump: false,
      fromRef: "v1.0.0", toRef: "v2.0.0", repoUrl: null,
    });
    assert.ok(result.includes("**ui:**"));
  });

  it("shows commit count", async () => {
    const result = await generateChangelog(MOCK_COMMITS, {
      format: "markdown", group: false, ai: false, versionBump: false,
      fromRef: "v1.0.0", toRef: "v2.0.0", repoUrl: null,
    });
    assert.ok(result.includes("3 commits"));
  });
});

// --- MCP Server Protocol ---

describe("MCP server protocol", () => {
  it("exports correct tool definitions", () => {
    // Validate tool schema structure without running the server
    const serverPath = require.resolve("./bin/mcp-server.js");
    const serverCode = require("node:fs").readFileSync(serverPath, "utf8");

    // Check tool names are defined
    assert.ok(serverCode.includes('"changelogai_generate"'));
    assert.ok(serverCode.includes('"changelogai_version_bump"'));

    // Check MCP protocol version
    assert.ok(serverCode.includes('"2024-11-05"'));

    // Check JSON-RPC methods handled
    assert.ok(serverCode.includes('"initialize"'));
    assert.ok(serverCode.includes('"tools/list"'));
    assert.ok(serverCode.includes('"tools/call"'));
  });
});
