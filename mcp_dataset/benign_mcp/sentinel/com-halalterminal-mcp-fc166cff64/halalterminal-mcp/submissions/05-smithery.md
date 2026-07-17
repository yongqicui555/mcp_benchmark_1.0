# 05 — Smithery (smithery.ai)

**URL:** https://smithery.ai/
**Free:** Yes
**Review:** automated (CLI-driven), typically live within minutes once `smithery publish` succeeds

## Two paths

### Path A — CLI from the repo (recommended)

```bash
# from /root/halalterminal-mcp
npm install -g @smithery/cli
smithery login
smithery init             # generates smithery.yaml — accept defaults
smithery publish
```

The CLI introspects `package.json`, `server.json`, and `README.md`. The `smithery init` step creates a `smithery.yaml` you should commit to the repo — see template below.

### Path B — manual via web

1. Sign in at https://smithery.ai with GitHub
2. Click **"Add server"** → **"From npm package"**
3. Enter `@halalterminal/mcp` — it pulls metadata
4. Edit fields per the mapping below
5. Click **"Publish"**

## smithery.yaml template (commit to repo root)

```yaml
startCommand:
  type: stdio
  configSchema:
    type: object
    required: ["halalterminal_api_key"]
    properties:
      halalterminal_api_key:
        type: string
        description: "Halal Terminal API key (prefix ht_). Get a free key at https://api.halalterminal.com — email-only signup, no credit card."
        secret: true
  commandFunction: |-
    (config) => ({
      command: "npx",
      args: ["-y", "@halalterminal/mcp"],
      env: { HALALTERMINAL_API_KEY: config.halalterminal_api_key }
    })
```

## Field mapping (manual path)

| Field | Value |
|---|---|
| **Display name** | `Halal Terminal` |
| **Description** | (paste **Full description ≤800 chars**) |
| **Categories** | `finance`, `productivity` |
| **Use cases** | "Shariah-compliant stock & ETF screening", "Portfolio audit & zakat", "Halal investing research" |
| **Source** | `npm:@halalterminal/mcp` |
| **License** | `Apache-2.0` |
