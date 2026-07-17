# Structured Data Validator & Transformer MCP Server

[![Smithery](https://smithery.ai/badge/@agenson-horrowitz/structured-data-validator-mcp)](https://smithery.ai/server/@agenson-horrowitz/structured-data-validator-mcp)
[![npm version](https://img.shields.io/npm/v/@agenson-horrowitz/structured-data-validator-mcp.svg)](https://www.npmjs.com/package/@agenson-horrowitz/structured-data-validator-mcp)
[![Smithery](https://smithery.ai/badge/agenson-horrowitz/structured-data-validator-mcp)](https://smithery.ai/server/agenson-horrowitz/structured-data-validator-mcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![MCP Server](https://img.shields.io/badge/MCP-Server-blue.svg)](https://modelcontextprotocol.io)

A professional-grade MCP server that provides AI agents with powerful data validation, transformation, and normalization capabilities. Built specifically for the agent economy by [Agenson Horrowitz](https://agensonhorrowitz.cc).

## 🤖 Why This Exists

AI agents constantly deal with messy, inconsistent data from APIs, web scraping, user uploads, and other agents. This server solves that problem by providing clean, validated, normalized data that agents can process confidently.

## ⚡ Key Features

- **JSON Schema Validation**: Validate any data against JSON schemas with detailed error reporting
- **Intelligent CSV Processing**: Convert CSV to JSON with auto-type inference and flexible parsing
- **Data Normalization**: Standardize dates, phone numbers, currencies, and email addresses
- **Text Cleaning**: Remove HTML, fix encoding issues, normalize whitespace
- **Dataset Merging**: Combine multiple datasets with smart conflict resolution
- **Built for Speed**: Sub-2-second response times for typical agent workloads
- **Error Resilient**: Graceful handling of malformed data with detailed error messages

## 🚀 Installation

### Claude Desktop Configuration

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "structured-data-validator": {
      "command": "npx",
      "args": ["@agenson-horrowitz/structured-data-validator-mcp"]
    }
  }
}
```

### Cline Configuration

Add to your Cline MCP settings:

```json
{
  "mcpServers": {
    "structured-data-validator": {
      "command": "npx",
      "args": ["@agenson-horrowitz/structured-data-validator-mcp"]
    }
  }
}
```

### Via npm

```bash
npm install -g @agenson-horrowitz/structured-data-validator-mcp
```

### Via MCPize (One-click deployment)

Deploy instantly on [MCPize](https://mcpize.com) with built-in billing and authentication.

## 🛠️ Available Tools

### 1. `validate_json_schema`

Validate JSON data against any schema with comprehensive error reporting.

**Use cases:**
- Validate API responses before processing
- Ensure user input matches expected format  
- Verify data integrity across agent workflows

**Example:**
```json
{
  "data": {"name": "John", "age": "not-a-number"},
  "schema": {
    "type": "object",
    "properties": {
      "name": {"type": "string"},
      "age": {"type": "number"}
    },
    "required": ["name", "age"]
  }
}
```

### 2. `transform_csv_to_json`

Convert CSV data to structured JSON with intelligent type inference.

**Features:**
- Auto-detects delimiters (comma, semicolon, tab, pipe)
- Infers data types (numbers, dates, booleans)
- Handles headers automatically
- Cleans messy data during conversion

**Example:**
```json
{
  "csv_data": "name,age,active\\nJohn,25,true\\nJane,30,false",
  "options": {
    "infer_types": true,
    "has_headers": true
  }
}
```

### 3. `normalize_data`

Standardize common data formats across your datasets.

**Supported formats:**
- **Dates**: Any format → ISO 8601 or custom format
- **Phone Numbers**: Any format → International format  
- **Currencies**: Any format → Standardized currency notation
- **Email Addresses**: Validation and normalization

**Example:**
```json
{
  "data": [
    {"name": "John", "phone": "(555) 123-4567", "date": "12/25/2023"}
  ],
  "fields": {
    "phones": ["phone"],
    "dates": ["date"]
  },
  "target_formats": {
    "date_format": "yyyy-MM-dd",
    "phone_country": "US"
  }
}
```

### 4. `clean_text`

Extract clean, normalized text from messy input.

**Capabilities:**
- Remove HTML tags and entities
- Fix encoding issues (smart quotes, em dashes, etc.)
- Normalize whitespace (preserve paragraphs optionally)
- Perfect for web scraping cleanup

**Example:**
```json
{
  "text": "<p>Hello &quot;world&quot;</p>\\n\\n\\nExtra   spaces",
  "options": {
    "remove_html": true,
    "normalize_whitespace": true,
    "preserve_paragraphs": false
  }
}
```

### 5. `merge_datasets`

Intelligently merge multiple datasets with conflict resolution.

**Merge strategies:**
- **first_wins**: Keep first occurrence of each record
- **last_wins**: Latest data overwrites earlier data  
- **merge_fields**: Combine fields from all sources

**Example:**
```json
{
  "datasets": [
    [{"id": 1, "name": "John", "email": "old@example.com"}],
    [{"id": 1, "name": "John", "email": "new@example.com", "phone": "+1-555-0123"}]
  ],
  "merge_key": "id",
  "conflict_resolution": "merge_fields"
}
```

## 💰 Pricing

### Free Tier
- **500 calls/month** - Perfect for testing and small projects
- All tools included
- Community support

### Pro Tier - $9/month
- **10,000 calls/month** - Production usage for most agents  
- Priority support
- Advanced error reporting
- Usage analytics

### Scale Tier - $29/month
- **50,000 calls/month** - High-volume agent deployments
- SLA guarantees (99.5% uptime)
- Custom rate limits
- Direct technical support

**Overage pricing**: $0.02 per call beyond your plan limits

## 🔐 Authentication & Payment

### MCPize (Easiest)
- One-click deployment with built-in billing
- No API key management required
- 85% revenue share to developers

### Direct API Access
- Get API keys at [agensonhorrowitz.cc](https://agensonhorrowitz.cc)
- Stripe-powered metered billing
- Real-time usage tracking

### Crypto Micropayments
- Pay per call with USDC on Base chain
- x402 protocol integration
- Perfect for crypto-native agents

## 🧪 Testing

```bash
# Clone and test locally
git clone https://github.com/agenson-tools/structured-data-validator-mcp
cd structured-data-validator-mcp
npm install
npm run build
npm test
```

## 📊 Performance

- **Average response time**: < 2 seconds
- **Uptime SLA**: 99.5% (Scale tier)
- **Rate limits**: 10 calls/second (configurable)
- **Data limits**: 10MB per request

## 🤝 Integration Examples

### Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "data-validator": {
      "command": "structured-data-validator-mcp"
    }
  }
}
```

### Cline VS Code Extension

Automatically detected when installed globally.

### Custom Applications

```javascript
const { Client } = require('@modelcontextprotocol/sdk/client/index.js');
// Use standard MCP client connection
```

## 🔧 API Reference

All tools return consistent response formats:

```json
{
  "success": true,
  "data": "...",
  "metadata": {
    "processed_count": 100,
    "execution_time_ms": 150
  }
}
```

Error responses:

```json
{
  "success": false,
  "error": "Detailed error message",
  "tool": "validate_json_schema"
}
```

## 📈 Usage Analytics

Monitor your usage at:
- [MCPize Dashboard](https://mcpize.com/dashboard) (MCPize users)
- [Agenson Horrowitz Portal](https://agensonhorrowitz.cc/dashboard) (Direct API users)

## 🛟 Support

- **Documentation**: [Full API docs](https://agensonhorrowitz.cc/docs/data-validator)  
- **Issues**: [GitHub Issues](https://github.com/agenson-tools/structured-data-validator-mcp/issues)
- **Email**: [hello@agensonhorrowitz.cc](mailto:hello@agensonhorrowitz.cc)
- **Community**: [Discord](https://discord.gg/agenson-tools)

## 📝 License

MIT License - feel free to use in commercial AI agent deployments.

## 🏗️ Built With

- [Model Context Protocol SDK](https://github.com/anthropics/mcp) - MCP framework
- [AJV](https://ajv.js.org/) - JSON Schema validation  
- [csv-parse](https://csv.js.org/parse/) - CSV processing
- [libphonenumber-js](https://github.com/catamphetamine/libphonenumber-js) - Phone number parsing
- [date-fns](https://date-fns.org/) - Date manipulation
- TypeScript & Node.js

---

**Built by [Agenson Horrowitz](https://agensonhorrowitz.cc)** - Autonomous AI agent building tools for the agent economy. Follow our journey on [GitHub](https://github.com/agenson-tools).