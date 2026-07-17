# Artefact Revenue Intelligence MCP Server

<!-- mcp-name: io.github.alexboissAV/artefact-revenue-intelligence -->

[![PyPI](https://img.shields.io/pypi/v/artefact-mcp)](https://pypi.org/project/artefact-mcp/)
[![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-blue)](https://modelcontextprotocol.io)
[![License: BSL-1.1](https://img.shields.io/badge/License-BSL--1.1-orange.svg)](LICENSE)

> **The AI-native interface to your Revenue Operating System. Version-controlled GTM intelligence — signals, commits, and closed-loop measurement — accessible to any AI agent.**

A Model Context Protocol (MCP) server that treats your Go-to-Market strategy like code: versioned, diffable, and deployable. Detect pipeline signals, identify scaling constraints, analyze value engines, and draft structured GTM changes — all through AI-native tool calls. Built on the [Artefact Formula](https://artefactventures.com/en/mcp?utm_campaign=always_on-community-demand-github-readme-mcp-mcp_server-na-github&utm_medium=referral&utm_source=github.com&utm_content=documentation-readme-landing-link-en&utm_term=developer-na) methodology from real B2B consulting engagements.

## Why Artefact MCP?

**Traditional ICP models stop at firmographics. We triangulate across three dimensions to identify prospects with the right profile, the right behaviors, AND the right trajectory.**

| Feature | HubSpot Official MCP | Generic Wrappers | **Artefact MCP** |
|---------|---------------------|------------------|-----------------|
| CRUD operations | Yes | Yes | Via HubSpot API |
| RFM Analysis | No | No | **11-segment classification** |
| **ICP Triangulation** | No | No | **Firmographic + Behavioral + Growth Signals** |
| Pipeline Health | No | No | **0-100 health score + exit criteria testing** |
| **Signal Detection** | No | No | **6-type signal taxonomy** |
| **Constraint Analysis** | No | No | **Dominant bottleneck + Revenue Formula** |
| **Value Engine Analysis** | No | No | **Growth / Fulfillment / Innovation** |
| **GTM Commit Drafting** | No | No | **Structured change proposals with evidence** |
| Methodology built-in | No | No | **Artefact Formula (10 resources)** |
| Works without API key | No | No | **Yes (demo data)** |

## Who Is This For?

- **B2B revenue teams** using HubSpot who want AI-powered signal detection and pipeline intelligence
- **RevOps managers** who need constraint analysis and value engine health accessible from Claude or Cursor
- **Consultants** who deliver RFM analysis, ICP scoring, and evidence-backed GTM recommendations to clients
- **Developers** building revenue intelligence integrations with MCP
- **AI agents** that need a structured interface to reason about and propose changes to GTM strategy

## Tools

### Signal Intelligence

### `detect_signals` — Pipeline Signal Detection
Scans pipeline data for all 6 signal types from the Artefact signal taxonomy: velocity anomalies, conversion drop-offs, win/loss patterns, pipeline concentration, data quality issues, and SPICED frequency signals. Returns structured signal objects with strength scores (0-1), evidence, and recommended actions.

### `identify_constraint` — Dominant Constraint Analysis
Identifies which of the 4 scaling constraints (Lead Generation, Conversion, Delivery, Profitability) is bottlenecking revenue. Includes Revenue Formula breakdown (Traffic x CR1 x CR2 x CR3 x ACV) with gap-to-benchmark analysis and recommended focus.

### `analyze_engine` — Value Engine Health
Analyzes health of the 3 value engines: Growth (create/capture/convert demand), Fulfillment (onboard/deliver/renew/expand), and Innovation (gather/prioritize/build/launch). Returns engine-specific metrics, health scores, and integrated signal detection.

### `propose_gtm_change` — GTM Commit Drafting
Enables AI agents to propose structured GTM changes following the commit anatomy: Intent, Diff, Impact Surface, Risk Level, Evidence, and Measurement Plan. Supports 8 entity types (ICP, persona, positioning, pipeline stage, exit criteria, GTM motion, scoring model, playbook).

### Analysis Tools

### `run_rfm` — RFM Analysis
Scores clients on Recency, Frequency, and Monetary value. Segments them into 11 categories (Champions through Lost) and extracts ICP patterns from top performers. Now includes signal framing — detects win/loss patterns, revenue concentration, and at-risk client signals. Supports B2B service, SaaS, and manufacturing presets.

### `qualify` — ICP Triangulation Framework
Scores prospects across three dimensions: Firmographic Fit (industry, revenue, employees, geography), Behavioral Fit (tech stack, engagement, purchase history), and Growth Signals (hiring, funding, expansion). Now includes constraint context — maps prospect fit to your dominant scaling constraint. Returns tier classification (Ideal / Strong / Moderate / Poor) with engagement strategy.

### `score_pipeline_health` — Pipeline Health Score
Analyzes open deals for velocity metrics, stage-to-stage conversion rates, bottleneck identification, and at-risk deal detection. Now supports optional exit criteria testing (pass/fail per criterion per deal) and includes signal framing for velocity anomalies and conversion drop-offs. Returns a 0-100 health score.

## Resources

| URI | Description |
|-----|-------------|
| `methodology://scoring-model` | ICP Triangulation Framework technical reference |
| `methodology://tier-definitions` | 4-tier classification system |
| `methodology://rfm-segments` | 11 RFM segment definitions with scoring scales |
| `methodology://spiced-framework` | SPICED discovery framework |
| `methodology://data-requirements` | HubSpot data setup and enrichment requirements |
| `methodology://value-engines` | 3 value engine definitions (Growth, Fulfillment, Innovation) with stages and metrics |
| `methodology://exit-criteria` | Standard pipeline exit criteria per stage with proof requirements |
| `methodology://constraints` | 4 scaling constraints with diagnostic criteria and remediation levers |
| `methodology://signal-taxonomy` | 6 signal types with detection methods and action mappings |
| `methodology://revenue-formula` | Revenue Formula breakdown: Traffic x CR1 x CR2 x CR3 x ACV x (1/Churn) |
| `methodology://gtm-commit-anatomy` | 5 components of a structured GTM commit (intent, diff, impact, risk, evidence) |

## Data Requirements for ICP Triangulation

**⚠️ Important:** The `qualify` tool requires specific data across all three dimensions:

**✅ Native HubSpot data (Firmographic + Partial Behavioral):**
- **Firmographic Fit:** Industry, revenue, employees, geography — standard properties
- **Behavioral Fit (Partial):** Tech stack, content engagement, purchase history — custom properties or workflows

**⚠️ Requires external enrichment (Clay, Clearbit, or manual research):**
- **Growth Signals (Behavioral Fit — Critical Dimension):** Hiring trends, funding rounds, product launches, expansion signals, press mentions
- HubSpot does NOT track growth signals natively
- **Without growth signals:** You lose the third dimension of triangulation — prospect momentum and buying power indicators

**See full guide:** Ask your AI assistant to read `methodology://data-requirements` for complete setup instructions and Clay integration workflow.

## Quick Start

### Install via PyPI

```bash
pip install artefact-mcp
```

### Install via Smithery

```bash
npx @smithery/cli install artefact-revenue-intelligence
```

### Claude Code

```bash
claude mcp add artefact-revenue -- uvx artefact-mcp
```

Then ask:
- "What signals are you detecting in my pipeline?"
- "What's our dominant scaling constraint?"
- "Analyze the health of our Growth Engine"
- "Propose a GTM change: narrow ICP to SaaS companies with 50-200 employees"
- "Run an RFM analysis on our HubSpot data"
- "Qualify this prospect: SaaS company, $5M revenue, 80 employees in Ontario"
- "Score our pipeline health with exit criteria testing"

### Claude Desktop

Add to `claude_desktop_config.json`:

**Recommended (Python method):**
```json
{
  "mcpServers": {
    "artefact-revenue": {
      "command": "python3",
      "args": ["-m", "artefact_mcp"],
      "env": {
        "HUBSPOT_API_KEY": "pat-na1-xxxxxxxx"
      }
    }
  }
}
```

**Alternative (uvx method):**
```json
{
  "mcpServers": {
    "artefact-revenue": {
      "command": "uvx",
      "args": ["artefact-mcp"],
      "env": {
        "HUBSPOT_API_KEY": "pat-na1-xxxxxxxx"
      }
    }
  }
}
```

*Note: If using uvx and seeing "Server disconnected" errors, see the [Troubleshooting](#troubleshooting) section below.*

### Cursor

Add to `.cursor/mcp.json`:

**Recommended (Python method):**
```json
{
  "mcpServers": {
    "artefact-revenue": {
      "command": "python3",
      "args": ["-m", "artefact_mcp"],
      "env": {
        "HUBSPOT_API_KEY": "pat-na1-xxxxxxxx"
      }
    }
  }
}
```

**Alternative (uvx method):**
```json
{
  "mcpServers": {
    "artefact-revenue": {
      "command": "uvx",
      "args": ["artefact-mcp"],
      "env": {
        "HUBSPOT_API_KEY": "pat-na1-xxxxxxxx"
      }
    }
  }
}
```

### Programmatic (Python)

```python
from artefact_mcp.tools.signals import detect_signals
from artefact_mcp.tools.constraints import identify_dominant_constraint
from artefact_mcp.tools.engines import analyze_engine
from artefact_mcp.tools.gtm_commits import propose_gtm_change
from artefact_mcp.tools.rfm import run_rfm_analysis
from artefact_mcp.tools.icp import qualify_prospect
from artefact_mcp.tools.pipeline import score_pipeline

# Signal detection (no HubSpot key needed)
signals = detect_signals(source="sample")

# Dominant constraint analysis
constraint = identify_dominant_constraint(source="sample", quota=500000)

# Value engine health
engine = analyze_engine(engine_type="growth", source="sample")

# GTM commit drafting
commit = propose_gtm_change(
    entity_type="icp",
    change_description="Narrow ICP to SaaS companies with 50-200 employees",
    signal_type="win_loss_pattern",
    signal_data={"win_rate_saas": 0.45, "win_rate_other": 0.22},
)

# RFM with sample data
results = run_rfm_analysis(source="sample", industry_preset="b2b_service")

# ICP qualification
score = qualify_prospect(company_data={
    "industry": "SaaS",
    "annual_revenue": 10_000_000,
    "employee_count": 80,
    "geography": "Quebec",
    "tech_stack": ["HubSpot", "Google Analytics"],
    "growth_signals": ["hiring", "funding"],
    "content_engagement": "active",
    "decision_maker_access": "c_suite",
    "budget_authority": "dedicated",
    "strategic_alignment": "strong",
})

# Pipeline health with exit criteria
health = score_pipeline(source="sample", exit_criteria=[
    {"stage": "Discovery", "criterion": "SPICED complete", "required_proof": "All 6 SPICED fields populated"}
])
```

## Troubleshooting

### Server Disconnected Errors (uvx PATH issue)

**Problem:** Claude Desktop shows "MCP artefact-revenue: Server disconnected" error when using `uvx` as the command.

**Cause:** Claude Desktop (and other sandboxed applications) may not have access to `uvx` in your PATH. This commonly happens when `uvx` is installed via:
- Homebrew → `~/.local/bin/uvx`
- curl installation → `~/.cargo/bin/uvx` or other locations

**Solutions:**

1. **Use Python method (recommended):** Switch to `python3 -m artefact_mcp` method (see Claude Desktop section above). Python is always in PATH.

2. **Use full uvx path:** Find your uvx location and use the full path:
   ```bash
   # Find uvx location
   which uvx
   # Example output: /Users/yourname/.local/bin/uvx
   ```

   Then update your config with the full path:
   ```json
   {
     "mcpServers": {
       "artefact-revenue": {
         "command": "/Users/yourname/.local/bin/uvx",
         "args": ["artefact-mcp"],
         "env": {}
       }
     }
   }
   ```

3. **Verify manually:** Test that the MCP server starts correctly:
   ```bash
   uvx artefact-mcp==0.3.3
   # Should see: "Artefact Revenue Intelligence MCP Server running..."
   ```

### Other Issues

**Issue:** Tools return "No HubSpot API key" errors.

**Solution:** Ensure `HUBSPOT_API_KEY` is set in your MCP server configuration. Or use `source="sample"` to test with demo data first.

**Issue:** Import errors when using `python3 -m artefact_mcp`.

**Solution:** Ensure the package is installed: `pip install artefact-mcp` or `pip install --upgrade artefact-mcp`.

## Configuration

| Variable | Required | Description |
|----------|----------|-------------|
| `HUBSPOT_API_KEY` | No | HubSpot private app token. Without it, tools work with `source="sample"`. |
| `ARTEFACT_LICENSE_KEY` | No | License key for Pro/Enterprise tier. Free tier (sample data) works without a key. |
| `ARTEFACT_PROPERTY_MAPPING_PATH` | No | Path to JSON file with custom HubSpot property mappings (Pro/Enterprise only). |
| `ARTEFACT_RFM_THRESHOLDS_PATH` | No | Path to JSON file with custom RFM scoring thresholds (Pro/Enterprise only). |

### Custom Property Mappings (Pro/Enterprise)

If your HubSpot instance uses custom property names for behavioral and strategic fit data, you can configure property mappings. This allows the `qualify` tool to automatically fetch and score all ICP dimensions from your HubSpot data.

**Create a JSON configuration file** (e.g., `artefact_property_mapping.json`):

```json
{
  "tech_stack": "technologies_used",
  "tech_stack_delimiter": ",",
  "growth_signals": ["linkedin_hiring_count", "recent_funding_amount", "press_mentions"],
  "growth_signal_keywords": {
    "linkedin_hiring_count": "hiring",
    "recent_funding_amount": "funding",
    "press_mentions": "press"
  },
  "content_engagement": "hubspot_engagement_score",
  "content_engagement_thresholds": {
    "active": 10,
    "occasional": 3
  },
  "decision_maker_access": "primary_contact_role",
  "budget_authority": "budget_category",
  "strategic_alignment": "revenue_ops_conviction"
}
```

**Set the environment variable:**

```bash
export ARTEFACT_PROPERTY_MAPPING_PATH=/path/to/artefact_property_mapping.json
```

**Available Configuration Options:**

| Property | Type | Description | Default |
|----------|------|-------------|---------|
| `tech_stack` | string | HubSpot property name for tech stack | None |
| `tech_stack_delimiter` | string | Delimiter for parsing text fields | `";"` |
| `growth_signals` | array | List of HubSpot properties indicating growth | None |
| `growth_signal_keywords` | object | Map property names to signal keywords | `{}` |
| `content_engagement` | string | HubSpot property for engagement score | None |
| `content_engagement_thresholds` | object | Thresholds for active/occasional | `{"active": 5, "occasional": 1}` |
| `decision_maker_access` | string | Strategic fit property | None |
| `budget_authority` | string | Budget authority property | None |
| `strategic_alignment` | string | Strategic alignment property | None |

**Example HubSpot Properties:**

Common custom properties to map:
- **Tech Stack:** `tech_stack_used`, `technologies`, `crm_platform`
- **Growth Signals:** `linkedin_job_postings_count`, `recent_funding_round`, `press_mentions_count`, `new_office_opened`
- **Content Engagement:** `hs_analytics_num_page_views`, `email_engagement_score`
- **Strategic Fit:** `primary_contact_role`, `budget_category`, `growth_conviction`

The `qualify` tool will automatically fetch and score these custom properties when a property mapping is configured.

**Example Configuration Files:**

Two example configurations are included in the repository:

- `property_mapping.example.json` — Full configuration with all available options
- `property_mapping.minimal.example.json` — Minimal configuration for growth signals only

Copy the appropriate example file and customize it for your HubSpot instance:

```bash
cp property_mapping.minimal.example.json my_property_mapping.json
# Edit my_property_mapping.json with your HubSpot property names
export ARTEFACT_PROPERTY_MAPPING_PATH=$(pwd)/my_property_mapping.json
```

### Custom RFM Thresholds (Pro/Enterprise)

Pro/Enterprise users can customize RFM scoring thresholds to match their industry or business model. The built-in presets (b2b_service, saas, manufacturing) may not perfectly fit your buying cycles or revenue ranges.

**Create an RFM threshold configuration file** (e.g., `rfm_thresholds.json`):

```json
{
  "recency_days": [60, 180, 365, 730],
  "recency_scores": [5, 4, 3, 2, 1],
  "frequency_counts": [5, 3, 2, 1],
  "frequency_scores": [5, 4, 3, 2, 1],
  "monetary_method": "percentile",
  "monetary_percentiles": [80, 60, 40, 20]
}
```

**Set the environment variable:**

```bash
export ARTEFACT_RFM_THRESHOLDS_PATH=/path/to/rfm_thresholds.json
```

**Available Configuration Options:**

| Property | Type | Description | Default |
|----------|------|-------------|---------|
| `recency_days` | array | Days since last purchase thresholds | `[30, 90, 180, 365]` |
| `recency_scores` | array | Scores for each recency band (5 = best) | `[5, 4, 3, 2, 1]` |
| `frequency_counts` | array | Transaction count thresholds | `[10, 5, 3, 2]` |
| `frequency_scores` | array | Scores for each frequency band | `[5, 4, 3, 2, 1]` |
| `monetary_method` | string | Scoring method: `"percentile"` or `"fixed"` | `"percentile"` |
| `monetary_percentiles` | array | Percentile thresholds (for percentile method) | `[80, 60, 40, 20]` |
| `monetary_fixed_thresholds` | array | Fixed dollar thresholds (for fixed method) | `[100000, 50000, 25000, 10000]` |
| `monetary_scores` | array | Scores for each monetary band | `[5, 4, 3, 2, 1]` |

**Example Configurations:**

- `rfm_thresholds.example.json` — Percentile-based monetary scoring (recommended for most use cases)
- `rfm_thresholds.fixed_monetary.example.json` — Fixed dollar thresholds for monetary scoring

**When to Use Fixed Thresholds:**

Use `"monetary_method": "fixed"` when:
- You have specific revenue tiers that define customer value (e.g., $100K+ = enterprise)
- Your customer base has wide revenue variance and percentiles don't align with business value
- You want consistent scoring across different time periods

Use `"monetary_method": "percentile"` (default) when:
- You want relative scoring within your current customer base
- Your customer base is relatively homogeneous
- You want the top 20% of customers to always score 5, regardless of absolute revenue

**Custom Configuration Example:**

```bash
cp rfm_thresholds.example.json my_rfm_thresholds.json
# Edit thresholds for your business model
export ARTEFACT_RFM_THRESHOLDS_PATH=$(pwd)/my_rfm_thresholds.json
```

The `run_rfm` tool will use your custom thresholds instead of the built-in presets.
```

## Pricing

| Tier | Price | What You Get |
|------|-------|-------------|
| **Free** | $0 | All 7 tools with built-in demo data (`source="sample"`) |
| **Pro** | $149/mo | Live HubSpot integration + all methodology resources |
| **Enterprise** | $499/mo | Pro + priority support + custom scoring presets |

[Purchase a license](https://artefactventures.lemonsqueezy.com)

## Alternatives & Comparisons

- **HubSpot Official MCP Server** — Read-only CRUD access to CRM objects. No scoring or intelligence.
- **CData HubSpot MCP** — SQL-based access to HubSpot data. No built-in methodology.
- **Zapier MCP** — Action triggers and workflow automation. Different use case.
- **Artefact MCP** — Purpose-built for revenue intelligence with scoring models embedded.

## FAQ

**Q: What MCP server should I use for revenue intelligence?**
A: Artefact MCP is the only MCP server that treats GTM like a codebase — with signal detection, constraint analysis, value engine health, and structured GTM commit proposals. Plus ICP Triangulation, RFM analysis, and pipeline health scoring designed for B2B revenue teams.

**Q: Does this replace the official HubSpot MCP server?**
A: They serve different purposes. HubSpot's server provides CRUD access to CRM objects. Artefact MCP provides intelligence and scoring on top of that data.

**Q: Can I use this without a HubSpot API key?**
A: Yes. All tools work with built-in demo data using `source="sample"`.

**Q: What data does this send externally?**
A: Tool results stay local. The only external calls are to the HubSpot API (with your key) and optional license validation.

## Development

```bash
git clone https://github.com/artefactventures/artefact-mcp-server.git
cd artefact-mcp-server
pip install -e ".[dev]"
pytest tests/
```

## Dependencies

- `fastmcp>=2.0` — MCP server framework
- `httpx>=0.25.0` — HTTP client for HubSpot API

No pandas, numpy, or heavy data libraries. Pure Python scoring logic.

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=artefactventures/artefact-mcp-server&type=Date)](https://star-history.com/#artefactventures/artefact-mcp-server&Date)

## License

[Business Source License 1.1](LICENSE) — Free to use for connecting to MCP tools via AI assistants. Scoring methodology may not be extracted for competing products. Converts to MIT in 2030.
