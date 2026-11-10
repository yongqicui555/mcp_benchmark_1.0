# Install Guide

This guide is for a customer-hosted OpsConduit Jobber MCP install. The connector is read-only by default and stores Jobber tokens on the machine running the MCP server.

## Requirements

- Node.js 20 or newer
- A Jobber account with permission to authorize apps
- A local MCP client that can run a stdio server
- Jobber app client ID and client secret

## npm Setup

Create a small working folder for your local config:

```bash
mkdir opsconduit-jobber
cd opsconduit-jobber
npm install @opsconduit/jobber-mcp
cp node_modules/@opsconduit/jobber-mcp/.env.example .env
```

Edit `.env`:

```bash
JOBBER_CLIENT_ID=your_client_id
JOBBER_CLIENT_SECRET=your_client_secret
JOBBER_REDIRECT_URI=http://localhost:3333/oauth/callback
JOBBER_REQUEST_TIMEOUT_MS=30000
JOBBER_TOKEN_STORE=.opsconduit/jobber-tokens.json
```

Run the local OAuth helper:

```bash
npx opsconduit-jobber-auth
```

Open the URL printed by the helper, authorize the app in Jobber, and let the browser return to `http://localhost:3333/oauth/callback`.

Start the MCP server:

```bash
npx opsconduit-jobber-mcp
```

## Source Checkout Setup

```bash
git clone https://github.com/opsconduit/jobber-mcp.git
cd jobber-mcp
npm install
cp .env.example .env
```

Edit `.env`:

```bash
JOBBER_CLIENT_ID=your_client_id
JOBBER_CLIENT_SECRET=your_client_secret
JOBBER_REDIRECT_URI=http://localhost:3333/oauth/callback
JOBBER_REQUEST_TIMEOUT_MS=30000
JOBBER_TOKEN_STORE=.opsconduit/jobber-tokens.json
```

Run the local OAuth helper:

```bash
npm run auth
```

Open the URL printed by the helper, authorize the app in Jobber, and let the browser return to `http://localhost:3333/oauth/callback`.

Start the MCP server:

```bash
npm start
```

## MCP Client Config

Use this shape for MCP clients that accept a stdio server config:

```json
{
  "mcpServers": {
    "opsconduit-jobber": {
      "command": "npx",
      "args": ["-y", "-p", "@opsconduit/jobber-mcp", "opsconduit-jobber-mcp"],
      "env": {
        "JOBBER_CLIENT_ID": "your_client_id",
        "JOBBER_CLIENT_SECRET": "your_client_secret",
        "JOBBER_REDIRECT_URI": "http://localhost:3333/oauth/callback",
        "JOBBER_REQUEST_TIMEOUT_MS": "30000",
        "JOBBER_TOKEN_STORE": "C:/path/to/opsconduit-jobber/.opsconduit/jobber-tokens.json"
      }
    }
  }
}
```

## Validation

After setup, run these MCP tools:

1. `jobber_account`
2. `jobber_clients_sample`

If both return data, the install can read from Jobber.

## Safety

- Mutations are blocked by default.
- Jobber token and GraphQL requests use a bounded timeout.
- Tokens are stored locally in `.opsconduit/jobber-tokens.json`.
- The local OAuth helper validates the returned state value before exchanging a code.
- Do not paste Jobber tokens into email, GitHub issues, or chat tools.
- Do not enable write access unless there is a separate written scope.
