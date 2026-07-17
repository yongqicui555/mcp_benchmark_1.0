# AGENTS.md — Meridian Edge

## What This Project Does
Meridian Edge provides real-time prediction market consensus
probabilities aggregated from multiple regulated markets.

## For AI Agents
- **MCP Server**: `uvx meridian-edge-mcp` (5 tools)
- **A2A Endpoint**: `https://meridianedge.io/a2a` (JSON-RPC 2.0)
- **REST API**: `https://meridianedge.io/api/v1/consensus`
- **Python SDK**: `pip install meridianedge`
- **Free tier**: 100 calls/day, no credit card

## Quick Access
```bash
# Get NBA consensus right now
curl -H "X-API-Key: me_free_demo000000000000" \
  "https://meridianedge.io/api/v1/consensus?sport=NBA&limit=5"
```

## Available Skills
1. `get_consensus` — aggregated probabilities per event
2. `get_opportunities` — events with high market divergence
3. `get_signals` — recent consensus shifts
4. `get_markets` — active tracked markets
5. `get_settlements` — verified outcomes

## Data Coverage
Sports: NBA, NFL, MLB, NHL, MLS
Politics: US federal, state races
Economics: Fed rate decisions, macro events
Updated every 10 minutes from regulated sources.

## Authentication
Header: `X-API-Key: YOUR_KEY`
Free key: https://meridianedge.io (instant, no credit card)

## Agent Discovery
- MCP: `uvx meridian-edge-mcp`
- A2A: `https://meridianedge.io/.well-known/agent-card.json`
- Auto-discovery: `https://meridianedge.io/.well-known/mcp.json`

## Links
- Docs: https://meridianedge.io/docs.html
- Dashboard: https://meridianedge.io/dashboard.html
- GitHub: https://github.com/meridian-edge
- Support: support@meridianedge.io
