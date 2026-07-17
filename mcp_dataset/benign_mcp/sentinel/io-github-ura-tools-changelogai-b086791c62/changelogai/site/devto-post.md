---
title: "I built a changelog generator that works on any repo — no conventional commits needed"
published: false
description: "Zero config CLI that parses any git history into grouped, linked changelogs. Optional AI mode rewrites commits into user-facing release notes. Ships with an MCP server."
tags: cli, devtools, ai, opensource
---

Every changelog tool I tried had the same problem: they only work if your team writes perfect conventional commits. Most teams don't.

So I built **changelogai** — a CLI that generates professional changelogs from *any* git history.

## What makes it different

**It works on messy repos.** The parser detects commit types from 24 keyword patterns, not just `type(scope):` prefixes. Commits like "fixed the auth bug" or "Updated dashboard layout" get classified correctly.

**Clickable commit links.** Auto-detects your GitHub/GitLab remote and generates linked hashes. No config needed.

**AI mode** (optional). Pass `--ai` and it rewrites technical commit messages into user-facing release notes using Claude. Costs ~$0.001 per changelog.

**MCP server included.** Other AI agents can call `changelogai_generate` and `changelogai_version_bump` as tools. Add it to your Claude Code or Cursor config in one line.

## Quick start

```bash
npm install -g @ura-dev/changelogai

# Grouped changelog since last tag
changelogai --group

# AI-enhanced
changelogai --ai --group --output CHANGELOG.md

# JSON for CI/CD
changelogai --format json

# Suggest next version
changelogai --version-bump
```

## Use as a library

```javascript
const { generateChangelog, getGitLog, getLatestTag } = require('changelogai');

const commits = getGitLog('.', 'v1.0.0', 'HEAD', 500);
const md = await generateChangelog(commits, {
  format: 'markdown',
  group: true
});
```

## MCP server (for AI agents)

```json
{
  "mcpServers": {
    "changelogai": { "command": "changelogai-mcp" }
  }
}
```

Any MCP client (Claude Code, Cursor, Dapr Agents) can now generate changelogs autonomously.

## Sample output

```markdown
## [v1.1.0](https://github.com/you/repo/compare/v1.0.0...v1.1.0) — 2026-03-28

### Features
- Add dark mode toggle (abc123)
- Support custom themes (def456)

### Bug Fixes
- Fix login redirect on mobile (789abc)
```

## The boring details

- Zero dependencies — pure Node.js
- Works with Node 18+
- Markdown, JSON, or plain text output
- Prepend mode for existing CHANGELOG.md files
- MIT license

Built by [ura](https://github.com/ura-tools/changelogai) — developer tools that go deeper.
