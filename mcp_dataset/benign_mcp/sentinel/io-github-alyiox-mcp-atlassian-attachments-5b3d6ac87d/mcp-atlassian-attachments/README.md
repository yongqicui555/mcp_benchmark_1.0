# MCP Atlassian Attachments

<!-- mcp-name: io.github.alyiox/mcp-atlassian-attachments -->

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server for downloading Jira Cloud attachments by attachment ID to local disk.

> **Supplement to the official Atlassian MCP server.**
> The [official Atlassian MCP server](https://mcp.atlassian.com/v1/mcp) covers search, issue management, and content operations but does not support downloading attachment files to disk. This server fills that gap.

**Requirements:** Python 3.13+, an Atlassian Cloud account, and an API token with at least the `read:jira-work` scope.

## Authentication

Scoped tokens are recommended to limit access to exactly the permissions needed.

> **Note:** The granular `read:attachment:jira` scope is not sufficient — Jira's attachment metadata endpoint (`/rest/api/3/attachment/{id}`) requires `read:jira-work` to resolve issue-level permissions. A classic (unscoped) API token also works.

### Create an API token

1. Go to [id.atlassian.com/manage-profile/security/api-tokens](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Click **Create API token**
3. Choose **"Create API token with scopes"** and select the `read:jira-work` scope, **or** choose **"Classic API token"** for full access
4. Copy the generated token

## Quick start

The fastest way to try the server is with the [MCP Inspector](https://github.com/modelcontextprotocol/inspector). Set the three required environment variables and run:

**From the published package** (no clone needed):

```bash
ATLASSIAN_SITE_URL=https://yourorg.atlassian.net \
ATLASSIAN_EMAIL=your.email@example.com \
ATLASSIAN_API_TOKEN=your-api-token \
npx -y @modelcontextprotocol/inspector uvx mcp-atlassian-attachments
```

**From a local clone:**

```bash
ATLASSIAN_SITE_URL=https://yourorg.atlassian.net \
ATLASSIAN_EMAIL=your.email@example.com \
ATLASSIAN_API_TOKEN=your-api-token \
npx -y @modelcontextprotocol/inspector uv run mcp-atlassian-attachments
```

## Configuration

Set environment variables or create a config file. Environment variables take priority.

**Environment variables:**

```bash
export ATLASSIAN_SITE_URL="https://yourorg.atlassian.net"
export ATLASSIAN_EMAIL="your.email@example.com"
export ATLASSIAN_API_TOKEN="your-api-token"
```

**Config file** (`~/.config/mcp-atlassian-attachments/config.json`):

```json
{
  "site_url": "https://yourorg.atlassian.net",
  "email": "your.email@example.com",
  "api_token": "your-api-token"
}
```

## Tools

| Tool | Description | Required params |
|------|-------------|-----------------|
| **`download_jira_attachment`** | Download a Jira attachment by ID. | `attachment_id`, `output_dir` |

### Common parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `attachment_id` | string | Jira attachment ID |
| `output_dir` | string | Local directory for the saved file. Created automatically if it does not exist. |
| `filename` | string (optional) | Override filename. Uses metadata filename when omitted. |
| `overwrite` | bool (optional) | Replace an existing file. Defaults to `false`. |

### Output

The tool returns a JSON object:

```json
{
  "product": "jira",
  "attachmentId": "439535",
  "filename": "screenshot.png",
  "mimeType": "image/png",
  "size": 496724,
  "path": "/your/output/dir/screenshot.png",
  "sourceUrl": "https://yourorg.atlassian.net/rest/api/3/attachment/content/439535"
}
```

## MCP host configuration

Add the following to your MCP host's config file. The JSON is the same for Cursor (`.cursor/mcp.json`), Claude Desktop (`claude_desktop_config.json`), and Claude Code (`.claude.json`).

```json
{
  "mcpServers": {
    "atlassian": {
      "command": "uvx",
      "args": ["mcp-atlassian-attachments"],
      "env": {
        "ATLASSIAN_SITE_URL": "https://yourorg.atlassian.net",
        "ATLASSIAN_EMAIL": "your.email@example.com",
        "ATLASSIAN_API_TOKEN": "your-api-token"
      }
    }
  }
}
```

## Security

- `ATLASSIAN_API_TOKEN` is never logged or included in error messages.
- The computed `Authorization` header is never exposed in tool output or errors.
- File writes are confined to the provided `output_dir`.
- Filenames are sanitized to prevent path traversal.

## Tests

```bash
uv run pytest tests/ -v
```

## Roadmap

- **`download_confluence_attachment_tool`** — Confluence Cloud uses a different API (`/wiki/api/v2/`) and a different identifier model. Planned for a future release.

## License

MIT. See [LICENSE](LICENSE).
