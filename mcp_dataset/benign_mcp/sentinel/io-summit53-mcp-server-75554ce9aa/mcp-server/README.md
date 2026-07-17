# Summit53 MCP Server

**Bring Summit53's Revenue Engine into the AI workflows your team already uses.**

This package connects MCP-compatible assistants to Summit53's hosted Revenue Engine. Assistants can help diagnose pipeline and forecast gaps, decide the next best action, execute permitted workflows, and preserve value evidence around the Figure-Eight revenue loop — from acquisition through expansion and back into acquisition.

[![npm version](https://img.shields.io/npm/v/@summit53/mcp-server)](https://www.npmjs.com/package/@summit53/mcp-server)
[![MCP Compatible](https://img.shields.io/badge/MCP-compatible-brightgreen)](https://modelcontextprotocol.io)
[![License](https://img.shields.io/badge/license-Proprietary-blue)](https://summit53.io/terms)

## Quick start

Add the package to a stdio-based MCP client such as Claude Desktop, Claude Code, Cursor, Windsurf, or Codex:

```json
{
  "mcpServers": {
    "summit53": {
      "command": "npx",
      "args": ["-y", "@summit53/mcp-server"]
    }
  }
}
```

On first use, your browser opens the Summit53 OAuth flow. Sign in, review the requested access, and authorize the client. Tokens are cached by the local MCP bridge and refreshed automatically.

For a web client that supports custom remote MCP connections, add:

- **Name:** `Summit53`
- **URL:** `https://api.summit53.io/mcp`

Client availability and labels vary by plan and workspace. Use the custom server URL instead of relying on a public app-directory listing.

See the [MCP setup guide](https://www.summit53.com/docs/mcp-setup-guide?utm_source=github&utm_medium=referral&utm_campaign=mcp_server) for client-specific instructions.

## What the Revenue Engine enables

Ask in natural language to:

- diagnose pipeline risk, deal drag, forecast confidence, gaps, and capacity;
- prepare opportunity strategy, account reviews, weekly action plans, and coaching;
- research accounts and inspect notes, activity, outreach, value impact, and methodology knowledge;
- write permitted notes, outreach updates, value evidence, and coaching outcomes;
- track long-running work through a durable job lifecycle.

The current release gate freezes **75 externally published functions across 15 categories**. That count is a compatibility fact, not the product proposition. Tool visibility depends on the client's granted scopes and the user's Summit53 organization permissions; call `list_available_tools` to discover the surface available in the current session.

| Category | Published functions |
| --- | ---: |
| Search | 3 |
| Opportunity Strategy | 5 |
| Account Intelligence | 3 |
| Pipeline & Risk | 4 |
| RevOps | 2 |
| Forecasting | 9 |
| Activity | 3 |
| Research | 1 |
| Notes & Activities | 5 |
| Outreach | 17 |
| Value Impact | 11 |
| Coaching | 3 |
| Knowledge Base | 5 |
| Job Lifecycle | 3 |
| Discovery | 1 |

The exact machine-readable surface is maintained in [`tool-catalog.json`](./tool-catalog.json). The registry-compatible connection manifest is [`server.json`](./server.json). The [tool reference](https://www.summit53.com/docs/mcp-tool-reference?utm_source=github&utm_medium=referral&utm_campaign=mcp_server) explains inputs, outputs, access requirements, and async behavior.

## Authentication and permissions

Interactive connections use OAuth 2.1-style authorization with PKCE. Access tokens last one hour; rotating refresh tokens last seven days. Access can be revoked from `/admin/integrations/mcp` in Summit53.

The published scope set is:

- read: `crm:read`, `pipeline:read`, `revenue:read`, `actions:read`, `jobs:read`;
- write and operations: `crm:write`, `outreach:write`, `outreach:send`, `coaching:write`, `value:write`, `automation:manage`, `jobs:manage`.

Business write tools always require their explicit write scopes. Job lifecycle tools always enforce `jobs:read` or `jobs:manage`. Read-scope enforcement for the remaining catalogue is being rolled out behind a production gate. Summit53's organization, ownership, and role permissions remain authoritative in every case.

Some approved service integrations can use scoped static API keys, but API keys are not part of the normal interactive setup. A scope authorizes an operation; it does not itself prove human approval. Broader high-risk write workflows remain gated until portable approval controls are available.

## Async jobs

Long-running tools return a durable job response rather than asking the client to hold an HTTP request open. Use:

- `get_job` to inspect status and results;
- `list_jobs` to find recent work;
- `cancel_job` to request cancellation when the job is still cancellable.

Job records are retained for 30 days. Every published function uses the same versioned response envelope so clients can handle success, partial results, queued work, and errors consistently.

## Architecture

- **Transport:** Streamable HTTP through the hosted Summit53 service
- **Endpoint:** `https://api.summit53.io/mcp`
- **Tenant boundaries:** Summit53 authentication and application permissions
- **Rate limiting and caching:** enforced by the hosted service, with tool-specific policies
- **Metrics:** usage and errors tracked per organization and tool

## Join the Founding 50

Summit53 is working with a small group of B2B SaaS revenue teams to shape the Revenue Engine in production. [Apply to the Founding 50](https://www.summit53.com/founding-50?utm_source=github&utm_medium=referral&utm_campaign=mcp_server).

## Support

- Documentation: [summit53.com/docs](https://www.summit53.com/docs?utm_source=github&utm_medium=referral&utm_campaign=mcp_server)
- Email: support@summit53.io
- Issues: [github.com/Summit53/mcp-server/issues](https://github.com/Summit53/mcp-server/issues)

## License

Proprietary. See [summit53.io/terms](https://summit53.io/terms) for details.
