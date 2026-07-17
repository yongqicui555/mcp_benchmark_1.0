# changelogai

Generate professional changelogs from your git history — instantly.

Works out of the box with conventional commits. Optional AI mode uses Claude to rewrite technical commit messages into user-facing release notes.

## Install

```bash
npm install -g @ura-dev/changelogai
```

## Quick Start

```bash
# Run without installing
npx @ura-dev/changelogai

# Generate changelog since last tag
changelogai

# Grouped by category
changelogai --group

# AI-enhanced (requires ANTHROPIC_API_KEY)
changelogai --ai --group

# Write to file
changelogai --group --output CHANGELOG.md

# Prepend new release to existing changelog
changelogai --group --output CHANGELOG.md --prepend

# JSON output for CI/CD
changelogai --format json

# Suggest semver bump
changelogai --version-bump
```

## Features

- **Zero config** — auto-detects latest tag, parses conventional commits
- **Smart grouping** — categorizes commits into Features, Bug Fixes, Performance, etc.
- **AI mode** — rewrites commit messages into clear, user-facing descriptions using Claude
- **Multiple formats** — Markdown, JSON, plain text
- **Version bump suggestion** — analyzes changes and suggests major/minor/patch
- **Prepend mode** — add new releases to the top of existing CHANGELOG.md
- **No dependencies** — pure Node.js, works everywhere

## Options

| Flag | Description | Default |
|---|---|---|
| `--from <ref>` | Start ref (tag/commit) | Latest tag |
| `--to <ref>` | End ref | HEAD |
| `--output <file>` | Write to file | stdout |
| `--format <fmt>` | markdown, json, plain | markdown |
| `--group` | Group by commit type | false |
| `--ai` | AI-enhanced descriptions | false |
| `--model <model>` | Claude model for AI mode | claude-haiku-4-5-20251001 |
| `--prepend` | Prepend to existing file | false |
| `--version-bump` | Suggest semver bump | false |
| `--repo <path>` | Git repo path | . |
| `--max-commits <n>` | Max commits to process | 500 |

## MCP Server

changelogai includes a Model Context Protocol server for AI agents and IDE integrations (Claude Desktop, Cursor, VS Code, etc.).

```json
{
  "mcpServers": {
    "changelogai": {
      "command": "npx",
      "args": ["-y", "-p", "@ura-dev/changelogai", "changelogai-mcp"]
    }
  }
}
```

Or if installed globally:
```json
{
  "mcpServers": {
    "changelogai": {
      "command": "changelogai-mcp"
    }
  }
}
```

### Available Tools

| Tool | Description |
|---|---|
| `changelogai_generate` | Generate a changelog from git history. Returns markdown, JSON, or plain text. |
| `changelogai_version_bump` | Analyze git commits and suggest next semver bump (major/minor/patch). |

## AI Mode

Set your Anthropic API key:
```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

Then run with `--ai`:
```bash
changelogai --ai --group --output CHANGELOG.md
```

AI mode rewrites technical commit messages into clear, user-facing release notes. Uses Claude Haiku by default (fast and cheap — ~$0.001 per changelog).

## License

MIT
