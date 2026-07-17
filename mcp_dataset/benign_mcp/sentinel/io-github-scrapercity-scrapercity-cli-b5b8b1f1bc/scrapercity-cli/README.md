# ScraperCity - B2B Lead Generation for AI Agents

Pull leads, validate emails, find mobile numbers, and scrape business data - all from your AI agent, CLI, or code.

ScraperCity gives AI agents access to 15+ B2B data tools: Apollo scraping, Google Maps extraction, email finding/validation, mobile number lookup, skip tracing, ecommerce store data, criminal records, and more.

## Quick Start

### Option 1: CLI

```bash
npx scrapercity login            # enter your API key
npx scrapercity wallet           # check balance
npx scrapercity maps -q "plumbers" -l "Denver, CO"
npx scrapercity poll <runId>     # wait for results
npx scrapercity download <runId> # save CSV
```

### Option 2: MCP Server (Claude Code, Cursor, Windsurf, etc.)

Add to your MCP config (e.g. `~/.claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "scrapercity": {
      "command": "npx",
      "args": ["-y", "--package", "scrapercity", "scrapercity-mcp"],
      "env": {
        "SCRAPERCITY_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

Then tell your AI: *"Find 1000 plumbers in Denver with emails using ScraperCity"*

### Option 3: Skill File (Claude Code)

Copy the skill file into your project:

```bash
npx scrapercity-mcp --print-skill > SCRAPERCITY_SKILL.md
```

Or download from: `https://scrapercity.com/agents/SKILL.md`

Then in Claude Code: *"Read SCRAPERCITY_SKILL.md and find me 2000 marketing directors at SaaS companies in California, validate their emails, and save to leads.csv"*

### Option 4: Direct API

```bash
# Start a Maps scrape
curl -X POST https://app.scrapercity.com/api/v1/scrape/maps \
  -H "Authorization: Bearer $SCRAPERCITY_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"searchStringsArray":["plumbers"],"locationQuery":"Denver, CO","maxCrawledPlacesPerSearch":500}'

# Check status
curl https://app.scrapercity.com/api/v1/scrape/status/RUN_ID \
  -H "Authorization: Bearer $SCRAPERCITY_API_KEY"

# Download CSV when SUCCEEDED
curl -O https://app.scrapercity.com/api/downloads/RUN_ID \
  -H "Authorization: Bearer $SCRAPERCITY_API_KEY"
```

## Available Tools

| Tool | What it does | Cost |
|------|-------------|------|
| **Apollo** | B2B contacts by job title, industry, location | $0.0039/lead |
| **Google Maps** | Local businesses with phones, emails, reviews | $0.01/place |
| **Email Validator** | Verify deliverability, catch-all, MX records | $0.0036/email |
| **Email Finder** | Find business email from name + company | $0.05/contact |
| **Mobile Finder** | Phone numbers from LinkedIn or email | $0.25/input |
| **People Finder** | Skip trace by name, email, phone, address | $0.02/result |
| **Store Leads** | Shopify/WooCommerce stores with contacts | $0.0039/lead |
| **BuiltWith** | All sites using a technology | $4.99/search |
| **Criminal Records** | Background check by name | $1.00 if found |
| **Lead Database** | 3M+ B2B contacts, instant query ($649 plan) | Included |

## How It Works

1. **Start a scrape** → get a `runId`
2. **Poll status** (or use webhooks) → wait for `SUCCEEDED`
3. **Download CSV** → leads with full contact info

Apollo scrapes take 11-48+ hours. All other scrapers: 1-30 minutes. Store leads are instant.

## Authentication

Get your API key at [app.scrapercity.com/dashboard/api-docs](https://app.scrapercity.com/dashboard/api-docs)

```bash
# Environment variable (recommended)
export SCRAPERCITY_API_KEY="your_key"

# Or save to config file
npx scrapercity login
```

## Webhooks

For Apollo and long-running scrapes, configure a webhook at [app.scrapercity.com/dashboard/webhooks](https://app.scrapercity.com/dashboard/webhooks) to get notified when results are ready.

## Plans

| Plan | Price | Credits |
|------|-------|---------|
| Trial | Free | $5 |
| Starter | $49/mo | $49 |
| Growth | $149/mo | $149 + 10% bonus |
| Professional | $649/mo | $649 + 30% bonus + Database API |

Buy additional credits anytime. [scrapercity.com/pricing](https://scrapercity.com/pricing)

## Links

- [Agent Docs](https://scrapercity.com/agents) - setup guide
- [API Reference](https://scrapercity.com/api-docs) - full documentation
- [Skill File](https://scrapercity.com/agents/SKILL.md) - for Claude Code
- [MCP Server Listing](https://scrapercity.com/agents) - configuration

## License

MIT
