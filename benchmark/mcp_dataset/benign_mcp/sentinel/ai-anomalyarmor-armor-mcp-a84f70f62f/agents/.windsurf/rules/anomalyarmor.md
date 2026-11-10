---
trigger: model_decision
description: When the user's task involves data quality, data freshness, schema drift, pipeline failures, or data observability — especially for Snowflake, BigQuery, Databricks, PostgreSQL, MySQL, Redshift, ClickHouse, SQL Server, or AWS Athena warehouses.
---

# AnomalyArmor MCP server

AnomalyArmor is a data observability platform. When connected, the `armor-mcp` MCP server exposes 53 tools to query alerts, monitor freshness, inspect schema drift, configure validity rules, and trace lineage across the user's data warehouse.

## Connecting

Hosted server (recommended) uses OAuth 2.1 (Clerk). Add to `~/.codeium/windsurf/mcp_config.json`:

```json
{
  "mcpServers": {
    "anomalyarmor": {
      "serverUrl": "https://mcp.anomalyarmor.ai/mcp"
    }
  }
}
```

Local stdio fallback for air-gapped environments:

```bash
pip install armor-mcp
ARMOR_API_KEY=aa_live_... armor-mcp
```

## When to use these tools

Invoke AnomalyArmor tools when the user:

- Asks "is my data healthy?", "what broke?", "any issues right now?"
- Reports a stale table, missing data, or a failing dashboard
- Wants to set up freshness SLAs, schema drift detection, or data quality checks
- Needs to trace upstream/downstream impact of a pipeline change
- Asks "what tables contain X?" or wants data discovery across their warehouse

Do **not** use these tools for general SQL queries against customer data; AnomalyArmor is metadata-only and never reads row-level data.

## Tool categories

| Category | Examples | Confirmation |
|---|---|---|
| Read-only | `health_summary`, `list_alerts`, `check_freshness`, `get_lineage` | Auto-invoke |
| Mutating | `create_metric`, `setup_freshness`, `enable_schema_monitoring` | Confirm with user |
| Destructive | `delete_*`, `dismiss_alert` | Always confirm and list affected entities |
| Expensive | `generate_intelligence`, `trigger_asset_discovery` | Confirm — queues background job |

Every tool carries `ToolAnnotations` (`readOnlyHint`, `destructiveHint`, `idempotentHint`). Respect them.

## Common workflows

**Triage** — `health_summary` → `list_alerts` → for each critical, `check_freshness` + `get_lineage` before recommending fix.

**Onboarding a schema** — `explore` to enumerate → `setup_freshness` bulk → `enable_schema_monitoring` bulk → `create_metric` on ID/email columns. Confirm table list before bulk ops.

**Investigation** — `check_freshness` on the reported table → `list_schema_changes` (7d window) → `get_lineage` to scope impact.

## Multi-tenancy

The server is scoped to the OAuth-authenticated user's company. Do not invent `company_id` or `tenant` arguments; they are ignored. You cannot access other tenants' data.

## Install via skills.sh

For 14 `/armor:*` slash commands across Windsurf, Cursor, Claude Code, Codex, and 40+ other agents:

```bash
npx skills add anomalyarmor/agents
```

## More

- Docs: https://docs.anomalyarmor.ai/integrations/mcp-server
- Source: https://github.com/anomalyarmor/agents
- Pricing: https://www.anomalyarmor.ai/pricing (free tier available)
