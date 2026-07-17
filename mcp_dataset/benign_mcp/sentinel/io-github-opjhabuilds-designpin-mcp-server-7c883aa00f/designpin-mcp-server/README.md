# DesignPin MCP Server
<!-- mcp-name: io.github.opjhabuilds/designpin-mcp-server -->

> An MCP server that lets any AI assistant push HTML prototypes to **[DesignPin](https://designpin.pro)** for team review and read back reviewer feedback.

## What this does

DesignPin is a tool for reviewing HTML prototypes with DOM-anchored comments. This package wraps the DesignPin REST API as a [Model Context Protocol](https://modelcontextprotocol.io) server, exposing three tools — `createShareLink`, `uploadVersion`, `listComments` — to any MCP-compatible AI client.

Once configured, your AI assistant — Claude Desktop, Cursor, VS Code (Copilot), Gemini CLI, or any other MCP-compatible client — can ship a generated HTML prototype to a shareable review link, pull back reviewer comments to incorporate, and push iterations as new versions, all from inside the same conversation that produced the design.

> **For ChatGPT users:** ChatGPT does not currently support MCP servers. Use the [direct REST API](https://designpin.pro/openapi.json) via Custom GPT Actions instead — no MCP server needed.

## Install + run

The server is invoked by your MCP client; you don't run it directly during normal use. The simplest path is `npx` invocation, which fetches and runs without a global install:

```bash
npx -y @designpin/mcp-server --api-key dp_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx --project-id proj_example_abc123
```

For most workflows you'll set this in your MCP client's config file rather than running it manually — see [Client config examples](#client-config-examples) below.

To verify the install works:

```bash
npx -y @designpin/mcp-server --version
# → 0.1.0

npx -y @designpin/mcp-server --help
# → usage info
```

## Get an API key

1. Open [designpin.pro](https://designpin.pro) and sign in.
2. Open any project (or create one).
3. Click **API & Integrations** in the project header.
4. Click **Generate new key**, give it a name (e.g. "Claude Desktop").
5. **Copy the key immediately** — it's shown once and cannot be retrieved later.

Each key is scoped to a single project. Generate separate keys per client / use case so you can revoke them individually.

## Configuration

Both CLI flags and environment variables are supported. Flags win when both are present.

| CLI flag | Env var | Required | Default | Description |
|---|---|---|---|---|
| `--api-key` | `DESIGNPIN_API_KEY` | for `uploadVersion`, `listComments` | — | Your `dp_live_...` API key |
| `--project-id` | `DESIGNPIN_PROJECT_ID` | for `uploadVersion` | — | Project ID the key is scoped to |
| `--base-url` | `DESIGNPIN_BASE_URL` | no | `https://designpin.pro` | API base URL (override for testing) |
| `--help` | — | no | — | Show usage and exit |
| `--version` | — | no | — | Print version and exit |

> **Security note:** CLI flags are visible in `ps` output on multi-user systems. Prefer environment variables on shared machines.

## Tools

### `createShareLink`

Create a public review link for an HTML prototype. No project setup required — creates a brand-new throwaway project. Rate-limited to 10 requests/hour per IP.

| Input | Type | Required | Description |
|---|---|---|---|
| `html` | string | yes | Complete HTML document to share |
| `title` | string | yes | Display name for the share, max 80 chars |
| `authorName` | string | no | Author name shown on review page |

**Returns:** JSON with `url`, `reviewToken`, `projectId`, `moduleId`, `versionId`.

**Example prompt to your AI assistant:**
> "Take this HTML and create a DesignPin share link titled 'Landing page hero V3'."

### `uploadVersion`

Upload a new HTML version to an existing DesignPin module. Auto-increments `versionNumber`. Requires the API key + `projectId` from configuration plus a `moduleId` from the user.

| Input | Type | Required | Description |
|---|---|---|---|
| `html` | string | yes | Complete HTML for the new version |
| `moduleId` | string | yes | Target module within the configured project |
| `description` | string | no | Version description shown in the sidebar |

**Returns:** JSON with `url`, `versionId`, `versionNumber`.

**Example prompt:**
> "Push this revised HTML as a new version to module `mod_example_def456` with the description 'Address pin #3 contrast feedback'."

### `listComments`

Fetch comments visible on a specific version of a DesignPin module. Uses chronological cutoff semantics matching the web UI: a comment is visible on version V if its origin version is V or any earlier version.

| Input | Type | Required | Description |
|---|---|---|---|
| `moduleId` | string | yes | Module ID |
| `versionId` | string | yes | Specific version to view comments on |

**Returns:** JSON with a `comments` array and a `summary` string like `"3 open, 1 resolved"`.

**Example prompt:**
> "Get the comments on module `mod_example_def456` at version `ver_example_ghi789` and tell me what's blocking approval."

## Client config examples

<details>
<summary><b>Claude Desktop</b></summary>

Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "designpin": {
      "command": "npx",
      "args": ["-y", "@designpin/mcp-server"],
      "env": {
        "DESIGNPIN_API_KEY": "dp_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "DESIGNPIN_PROJECT_ID": "proj_example_abc123"
      }
    }
  }
}
```

Restart Claude Desktop after saving.
</details>

<details>
<summary><b>Cursor</b></summary>

Edit `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "designpin": {
      "command": "npx",
      "args": ["-y", "@designpin/mcp-server"],
      "env": {
        "DESIGNPIN_API_KEY": "dp_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "DESIGNPIN_PROJECT_ID": "proj_example_abc123"
      }
    }
  }
}
```

Reload Cursor after saving.
</details>

<details>
<summary><b>VS Code (Copilot with MCP)</b></summary>

Add to your VS Code user settings JSON or a workspace `.vscode/mcp.json`:

```json
{
  "servers": {
    "designpin": {
      "command": "npx",
      "args": ["-y", "@designpin/mcp-server"],
      "env": {
        "DESIGNPIN_API_KEY": "dp_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "DESIGNPIN_PROJECT_ID": "proj_example_abc123"
      }
    }
  }
}
```
</details>

<details>
<summary><b>Gemini CLI extension</b></summary>

Edit your Gemini CLI config (path varies by version). Both the env-style and the flag-style work; flag-style is shown here:

```json
{
  "mcpServers": {
    "designpin": {
      "command": "npx",
      "args": [
        "-y", "@designpin/mcp-server",
        "--api-key", "dp_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "--project-id", "proj_example_abc123"
      ]
    }
  }
}
```
</details>

## Example conversation

```
You:  Generate a pricing page with three tiers (Free, Pro $12, Team $29).
      Push it to DesignPin so my team can review.

AI:   [generates HTML, calls createShareLink]
      Share link created. Send this to your team:
      https://designpin.pro/review/EXAMPLE_TOKEN_xyz

      Project: proj_example_abc123
      Module:  mod_example_def456
      Version: ver_example_ghi789

[team reviews and leaves 4 comments]

You:  Pull the feedback from module mod_example_def456 at version
      ver_example_ghi789 and address the must-fix comments.

AI:   [calls listComments]
      Open comments (4):
      - P0 Pin #1 "CTA contrast fails WCAG AA on the Pro tier"
      - P1 Pin #2 "Pricing hidden until hover — make always visible"
      - P1 Pin #3 "Annual toggle is ambiguous — show savings %"
      - P2 Pin #4 "Logo could link back to homepage"

      I'll regenerate the HTML with the two P0/P1 issues addressed.

You:  Push the revision.

AI:   [generates updated HTML, calls uploadVersion]
      v2 uploaded. Same review URL — your team can compare versions.
```

## Direct REST API

If you want to call the DesignPin API without an MCP server, the OpenAPI 3.1 spec is published at:

**https://designpin.pro/openapi.json**

Import it into Postman, generate a client SDK, or use it directly with ChatGPT Custom GPT Actions.

## Links

- **DesignPin app:** https://designpin.pro
- **OpenAPI spec:** https://designpin.pro/openapi.json
- **GitHub:** https://github.com/opjhabuilds/designpin-mcp-server
- **Issues:** https://github.com/opjhabuilds/designpin-mcp-server/issues

## License

MIT © 2026 Omprakash Jha
