# @apitier/mcp-server

MCP (Model Context Protocol) server exposing all APITier utility APIs as tools for AI agents.

Two integration modes:

| Mode | Best for |
| --- | --- |
| **Hosted HTTP** — `https://mcp.apitier.com` | Anthropic connector directory, remote agents, server-to-server |
| **stdio (npx)** — runs locally | Claude Desktop, Cursor, Windsurf, local agents |

Both modes use the same **MCP Key** — one key unlocks all your subscribed services.

**Postman collection:** import the ready-made collection to test all endpoints instantly:
[`https://raw.githubusercontent.com/apitier/apitier-mcp-server/main/postman/APITier%20MCP%20Server.postman_collection.json`](https://raw.githubusercontent.com/apitier/apitier-mcp-server/main/postman/APITier%20MCP%20Server.postman_collection.json)

In Postman: **Import → Link → paste URL → set `mcp_api_key` collection variable**.

---

## Tools Available

### 🇬🇧 UK KYC Onboarding

| Tool | Description |
| --- | --- |
| `kyc_onboard_uk` | **Full UK business onboarding check in one call.** Validates VAT, verifies Companies House, retrieves PSC (beneficial owners), and confirms the registered address. Returns `PASS / REVIEW / FAIL`, a risk score, and the full data bundle. Requires `postcode` + `vat` + `leadAgent` subscriptions. |

**Example output:**

```json
{
  "decision": "PASS",
  "risk_score": 95,
  "flags": [],
  "checks": {
    "company": { "status": "active", "data": { ... } },
    "psc":     { "status": "found",  "data": { ... } },
    "vat":     { "status": "valid",  "data": { ... } },
    "address": { "status": "verified", "data": { ... } }
  }
}
```

---

### 🇬🇧 UK Address & Property

| Tool | Description |
| --- | --- |
| `verify_uk_address` | Verify a UK address against Royal Mail PAF — returns canonical address, UPRN, UDPRN, and per-delivery-point geocode |
| `lookup_uprn` | Look up a full AddressBase record by UDPRN — returns UPRN, PAF canonical address, coordinates. Use UDPRN from `verify_uk_address` |
| `lookup_uk_postcode` | UK postcode → full PAF address list + district, ward, county, country, and geocode |

### 🇬🇧 UK Business & Compliance

| Tool | Description |
| --- | --- |
| `verify_uk_company` | Look up a UK company on Companies House by name or number — status, address, SIC codes, filing health |
| `get_company_psc` | Persons with Significant Control register for a UK company — required for AML beneficial ownership checks |
| `validate_sort_code` | Validate a UK sort code and optionally a bank account number (Vocalink modulus check). No API key required. |

### 🇬🇧🇪🇺 UK + EU VAT Compliance

| Tool | Description |
| --- | --- |
| `validate_vat` | Validate UK and EU VAT numbers — checks HMRC for GB numbers, EU VIES for all other country prefixes. Returns registered business name and address. Accepts any country prefix (e.g. `GB123456789`, `DE123456789`, `FR12345678901`). |

### 🌍 Global Identity

| Tool | Description |
| --- | --- |
| `validate_email` | Validate email — syntax, MX, SMTP reachability, disposable domain check. Works for any email address globally. |
| `validate_phone` | Validate and parse phone numbers — accepts any international format, returns country, carrier, and line type. |

### 🇮🇳 India

| Tool | Description |
| --- | --- |
| `lookup_india_pincode` | Indian PIN code → state / district / town |

### 🌍 Utilities

| Tool | Description |
| --- | --- |
| `generate_barcode` | Generate barcode image (Code128, EAN-13, UPC, and more) |
| `generate_qrcode` | Generate QR code image with optional logo and colour |
| `convert_data` | Convert between CSV, JSON, XML, YAML |

---

## Quick Start

### 1. Get your MCP Key

Sign up at [apitier.com](https://apitier.com) → **Account → AI & MCP → Generate MCP Key**.

Your MCP Key (`mcp_...`) automatically unlocks the tools for every APITier service you have subscribed to. No per-service configuration needed.

---

## Hosted HTTP Endpoint

`POST https://mcp.apitier.com/mcp?x-api-key=YOUR_MCP_KEY`

Pass your MCP Key as the `x-api-key` query parameter. The endpoint resolves your subscribed services and returns only the tools available to you.

**Required headers:**

```http
Content-Type: application/json
Accept: application/json, text/event-stream
```

**Test with curl:**

```bash
curl -s -X POST 'https://mcp.apitier.com/mcp?x-api-key=YOUR_MCP_KEY' \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | jq .
```

**Call a tool:**
```bash
curl -s -X POST 'https://mcp.apitier.com/mcp?x-api-key=YOUR_MCP_KEY' \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "verify_uk_company",
      "arguments": { "q": "03977902" }
    }
  }' | jq .
```

**Health check:**

```bash
curl https://mcp.apitier.com/health
```

### Use with any HTTP MCP client

```json
{
  "mcpServers": {
    "apitier": {
      "url": "https://mcp.apitier.com/mcp?x-api-key=YOUR_MCP_KEY"
    }
  }
}
```

---

## Claude Desktop (stdio)

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

**With MCP Key (recommended — single key, all subscribed tools):**

```json
{
  "mcpServers": {
    "apitier": {
      "command": "npx",
      "args": ["-y", "@apitier/mcp-server"],
      "env": {
        "APITIER_MCP_KEY": "mcp_your-key-here"
      }
    }
  }
}
```

**With individual service keys (if you prefer explicit control):**

```json
{
  "mcpServers": {
    "apitier": {
      "command": "npx",
      "args": ["-y", "@apitier/mcp-server"],
      "env": {
        "APITIER_POSTCODE_KEY":     "key-from-postcode-subscription",
        "APITIER_LEAD_AGENT_KEY":   "key-from-lead-agent-subscription",
        "APITIER_EMAIL_KEY":        "key-from-email-subscription",
        "APITIER_PHONE_KEY":        "key-from-phone-subscription",
        "APITIER_VAT_KEY":          "key-from-vat-subscription",
        "APITIER_BARCODE_KEY":      "key-from-barcode-subscription",
        "APITIER_CONVERT_DATA_KEY": "key-from-data-conversion-subscription"
      }
    }
  }
}
```

Restart Claude Desktop after saving. Only tools for your active subscriptions will appear.

---

## Cursor / Windsurf / VS Code

```json
{
  "mcp": {
    "servers": {
      "apitier": {
        "command": "npx",
        "args": ["-y", "@apitier/mcp-server"],
        "env": {
          "APITIER_MCP_KEY": "mcp_your-key-here"
        }
      }
    }
  }
}
```

---

## LangChain (Python)

**stdio:**

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from langchain_anthropic import ChatAnthropic

async def main():
    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "@apitier/mcp-server"],
        env={"APITIER_MCP_KEY": "mcp_your-key-here"},
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await load_mcp_tools(session)

            model = ChatAnthropic(model="claude-sonnet-4-6")
            agent = create_react_agent(model, tools)

            result = await agent.ainvoke({
                "messages": "Validate this email: test@example.com and look up postcode SW1A 1AA"
            })
            print(result["messages"][-1].content)
```

**HTTP endpoint:**

```python
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

async def main():
    async with streamablehttp_client(
        "https://mcp.apitier.com/mcp?x-api-key=mcp_your-key-here"
    ) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await load_mcp_tools(session)
            # use tools with your agent...
```

---

## Vercel AI SDK (TypeScript)

**stdio:**

```typescript
import { experimental_createMCPClient as createMCPClient } from "ai";
import { Experimental_StdioMCPTransport as StdioMCPTransport } from "ai/mcp-stdio";
import { anthropic } from "@ai-sdk/anthropic";
import { generateText } from "ai";

const mcp = await createMCPClient({
  transport: new StdioMCPTransport({
    command: "npx",
    args: ["-y", "@apitier/mcp-server"],
    env: { APITIER_MCP_KEY: process.env.APITIER_MCP_KEY! },
  }),
});

const tools = await mcp.tools();

const { text } = await generateText({
  model: anthropic("claude-sonnet-4-6"),
  tools,
  prompt: "Verify this UK company: Google UK Limited",
});

await mcp.close();
```

**HTTP endpoint:**

```typescript
import { experimental_createMCPClient as createMCPClient } from "ai";

const mcp = await createMCPClient({
  transport: {
    type: "sse",
    url: `https://mcp.apitier.com/mcp?x-api-key=${process.env.APITIER_MCP_KEY}`,
  },
});

const tools = await mcp.tools();
```

---

## Environment Variables

| Variable | Description |
| --- | --- |
| `APITIER_MCP_KEY` | **Recommended.** Single MCP Key from account page — resolves all subscribed service keys automatically |
| `APITIER_POSTCODE_KEY` | UK Postcode subscription — enables `verify_uk_address`, `lookup_uprn`, `lookup_uk_postcode` |
| `APITIER_LEAD_AGENT_KEY` | Lead Agent subscription — enables `verify_uk_company`, `get_company_psc` |
| `APITIER_EMAIL_KEY` | Email Validation subscription — enables `validate_email` |
| `APITIER_PHONE_KEY` | Phone Validation subscription — enables `validate_phone` |
| `APITIER_VAT_KEY` | VAT Validation subscription — enables `validate_vat` |
| `APITIER_PINCODE_KEY` | India Pincode subscription — enables `lookup_india_pincode` |
| `APITIER_BARCODE_KEY` | Barcode/QR Code subscription — enables `generate_barcode`, `generate_qrcode` |
| `APITIER_CONVERT_DATA_KEY` | Data Conversion subscription — enables `convert_data` |

`validate_sort_code` requires no API key — it is always available.

`kyc_onboard_uk` requires `APITIER_POSTCODE_KEY` + `APITIER_LEAD_AGENT_KEY` + `APITIER_VAT_KEY` (or a unified `APITIER_MCP_KEY` with all three subscriptions). The tool only appears when all three services are active.

Individual service keys take precedence over `APITIER_MCP_KEY` if both are set.

---

## Development

```bash
git clone https://github.com/apitier/apitier-mcp-server.git
cd apitier-mcp-server
npm install
npm run build
APITIER_MCP_KEY=mcp_your-key node dist/index.js
```

Test with the MCP Inspector:

```bash
npx @modelcontextprotocol/inspector npx @apitier/mcp-server
```

Set `APITIER_MCP_KEY` in the inspector's environment variables panel.

---

## Example Agent Prompts

Once connected to Claude Desktop or any MCP-compatible agent:

### UK KYC onboarding

- *"Run a KYC check on Vodafone Group Plc, VAT GB778476239, postcode EC1A 1BB"*
- *"Onboard this supplier: company name Tesco PLC, VAT GB220437023"*
- *"Verify this business before we sign the contract: company number 00445790"*

### UK address & property

- *"Verify this address and give me its UPRN: 10 Downing Street, SW1A 2AA"*
- *"Look up UK postcode EC1A 1BB and fill in the address form"*

### UK business & compliance

- *"Verify this UK company on Companies House: Barclays Bank UK PLC"*
- *"Who are the persons with significant control for company number 00026167?"*
- *"Validate this UK sort code and account number: 60-16-13 / 31926819"*
- *"Validate this UK VAT number: GB927065390"*
- *"Validate this EU VAT number before I send the invoice: DE123456789"*

### Global identity

- *"Validate this list of emails and tell me which ones are invalid"*
- *"Validate these phone numbers and tell me which country each is from"*

### Utilities

- *"Generate a QR code for [apitier.com](https://apitier.com)"*
- *"Convert this CSV to JSON"*
