"""
Rug Munch Intelligence — MCP Server
Model Context Protocol server for Claude Desktop, Cursor, Windsurf, etc.

19 tools covering token risk, deployer tracking, holder analysis,
KOL detection, market intelligence, AI forensics, and token monitoring.

Usage:
  python3 mcp_server.py

Config for Claude Desktop:
{
  "mcpServers": {
    "rug-munch": {
      "command": "python3",
      "args": ["/path/to/mcp_server.py"],
      "env": {"RUG_MUNCH_API_BASE": "https://cryptorugmunch.app/api/agent/v1"}
    }
  }
}
"""

import os
import json
import httpx
import asyncio
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server

API_BASE = os.environ.get("RUG_MUNCH_API_BASE", "https://cryptorugmunch.app/api/agent/v1")
API_KEY = os.environ.get("RUG_MUNCH_API_KEY", "")

server = Server("rug-munch-intelligence")


def _headers():
    h = {"Content-Type": "application/json"}
    if API_KEY:
        h["X-API-Key"] = API_KEY
    return h


async def _post(path: str, data: dict, timeout: float = 30) -> dict:
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(f"{API_BASE}{path}", json=data, headers=_headers())
        resp.raise_for_status()
        return resp.json()


async def _get(path: str, timeout: float = 30) -> dict:
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.get(f"{API_BASE}{path}", headers=_headers())
        resp.raise_for_status()
        return resp.json()


# ─── Tool Definitions ────────────────────────────────────────

TOKEN_ADDRESS_SCHEMA = {
    "token_address": {
        "type": "string",
        "description": "Token mint address (Solana) or contract address (EVM)",
    },
    "chain": {
        "type": "string",
        "default": "solana",
        "description": "Blockchain: solana, ethereum, base, arbitrum, polygon, optimism, avalanche",
    },
}


@server.list_tools()
async def list_tools():
    return [
        # ─── Core Risk Assessment ───
        Tool(
            name="check_token_risk",
            description=(
                "CRITICAL: Check a token's rug pull risk score BEFORE any transaction. "
                "Returns 0-100 risk score, honeypot detection, deployer history, freeze authority check, "
                "holder concentration, and SAFE/CAUTION/AVOID recommendation. "
                "Cost: $2.50 via x402."
            ),
            inputSchema={
                "type": "object",
                "properties": TOKEN_ADDRESS_SCHEMA,
                "required": ["token_address"],
            },
        ),
        Tool(
            name="check_token_risk_premium",
            description=(
                "Premium deep risk analysis with full category breakdown, deployer cross-reference, "
                "social OSINT, holder intelligence, and historical pattern matching. "
                "Use for high-value positions. Cost: $10.00 via x402."
            ),
            inputSchema={
                "type": "object",
                "properties": TOKEN_ADDRESS_SCHEMA,
                "required": ["token_address"],
            },
        ),
        Tool(
            name="check_batch_risk",
            description=(
                "Batch risk check for up to 20 tokens at once. "
                "Returns risk scores and recommendations for all tokens. "
                "Ideal for portfolio screening. Cost: $7.50 via x402 (up to 20 tokens)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "tokens": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of token addresses (max 20)",
                    },
                    "chain": {"type": "string", "default": "solana"},
                },
                "required": ["tokens"],
            },
        ),

        # ─── Intelligence Endpoints ───
        Tool(
            name="check_deployer_history",
            description=(
                "Check a token deployer's full history: tokens deployed, rug count, "
                "classification (legitimate_builder / suspicious / serial_rugger). "
                "Essential for evaluating new token trustworthiness. Cost: $7.50 via x402."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "deployer_address": {"type": "string", "description": "Deployer wallet address"},
                },
                "required": ["deployer_address"],
            },
        ),
        Tool(
            name="get_token_intelligence",
            description=(
                "Comprehensive token data: price, volume, market cap, holder stats, "
                "LP lock status, authority flags, buy/sell ratios, and top holders. Cost: $7.50 via x402."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "token_address": {"type": "string", "description": "Token address"},
                },
                "required": ["token_address"],
            },
        ),
        Tool(
            name="get_holder_deepdive",
            description=(
                "Deep holder analysis: sniper detection, Jito bundle analysis, "
                "fresh wallet clustering, whale concentration, connected wallet patterns. "
                "Detects coordinated manipulation. Cost: $12.50 via x402."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "token_address": {"type": "string", "description": "Token address"},
                },
                "required": ["token_address"],
            },
        ),
        Tool(
            name="get_social_osint",
            description=(
                "Social infrastructure analysis: Twitter account recycling, domain age, "
                "Telegram group legitimacy, cross-references with known scam infrastructure. Cost: $2.50 via x402."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "token_address": {"type": "string", "description": "Token address"},
                },
                "required": ["token_address"],
            },
        ),
        Tool(
            name="get_kol_shills",
            description=(
                "KOL shill pattern detection: which influencers promote this token, "
                "their buy timing vs shill timing, coordinated pump patterns. Cost: $2.50 via x402."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "token_address": {"type": "string", "description": "Token address"},
                },
                "required": ["token_address"],
            },
        ),
        Tool(
            name="get_coordinated_buys",
            description=(
                "Detect coordinated buying across tracked KOLs. Identifies tokens where "
                "multiple influencers bought within a short window. Cost: $2.50 via x402."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "hours": {"type": "integer", "default": 72, "description": "Lookback window in hours"},
                },
            },
        ),
        Tool(
            name="check_blacklist",
            description=(
                "Check if a token is community-flagged. Community-sourced intelligence "
                "with reputation-weighted flags. Cost: $2.50 via x402."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "token_address": {"type": "string"},
                    "chain": {"type": "string", "default": "solana"},
                },
                "required": ["token_address"],
            },
        ),
        Tool(
            name="check_scammer_wallet",
            description=(
                "Check if a wallet belongs to a known scammer, serial rugger, "
                "or flagged entity. Cost: $2.50 via x402."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "wallet_address": {"type": "string", "description": "Wallet address to check"},
                },
                "required": ["wallet_address"],
            },
        ),
        Tool(
            name="get_market_risk_index",
            description=(
                "Daily market-wide rug risk index (0-100). Components: high_risk_ratio, "
                "rug_velocity, liquidity_drains, deployer_activity. "
                "High = more rugs happening = exercise caution. Cost: $2.50 via x402."
            ),
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="get_serial_ruggers",
            description="Known serial rug deployer watchlist. Cross-reference before trusting new tokens. Cost: $2.50 via x402.",
            inputSchema={
                "type": "object",
                "properties": {
                    "min_tokens": {"type": "integer", "default": 2, "description": "Min tokens deployed to qualify"},
                },
            },
        ),

        # ─── Marcus AI Forensics ───
        Tool(
            name="marcus_quick",
            description=(
                "AI forensic verdict by Marcus Aurelius (Claude Sonnet 4). "
                "One-paragraph analysis with risk score, key flags, and Stoic wisdom. "
                "~5-30s latency. Cost: $7.50 via x402."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    **TOKEN_ADDRESS_SCHEMA,
                    "question": {
                        "type": "string",
                        "description": "Optional specific question about the token",
                    },
                },
                "required": ["token_address"],
            },
        ),
        Tool(
            name="marcus_forensics",
            description=(
                "Full AI forensic investigation by Marcus Aurelius (Claude Sonnet 4). "
                "Covers deployer history, holder patterns, social OSINT, KOL cross-reference, "
                "contract security, liquidity, and trading patterns. ~15-60s. Cost: $35.00 via x402."
            ),
            inputSchema={
                "type": "object",
                "properties": TOKEN_ADDRESS_SCHEMA,
                "required": ["token_address"],
            },
        ),
        Tool(
            name="marcus_ultra",
            description=(
                "The deepest AI forensic analysis available. Powered by Claude Opus 4 "
                "with extended reasoning. Catches subtle patterns: connected wallet clusters, "
                "timing correlations, historical rug playbook matching. ~30-120s. Cost: $25.00 via x402."
            ),
            inputSchema={
                "type": "object",
                "properties": TOKEN_ADDRESS_SCHEMA,
                "required": ["token_address"],
            },
        ),
        Tool(
            name="marcus_thread",
            description=(
                "X/Twitter-thread-ready forensic analysis. 5-8 posts, each ≤280 chars. "
                "Perfect for research posting. Cost: $10.00 via x402."
            ),
            inputSchema={
                "type": "object",
                "properties": TOKEN_ADDRESS_SCHEMA,
                "required": ["token_address"],
            },
        ),

        # ─── Monitoring ───
        Tool(
            name="watch_token",
            description=(
                "Set up real-time token monitoring with webhook alerts. "
                "When risk changes, rug detected, or price drops, we POST to your webhook. "
                "Covers 7 days. No other service offers proactive rug detection. Cost: $7.50 via x402."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "token_address": {"type": "string"},
                    "webhook_url": {"type": "string", "description": "HTTPS URL to POST alerts to"},
                    "watch_type": {
                        "type": "string",
                        "default": "rug_detected",
                        "enum": ["risk_change", "rug_detected", "price_drop", "all"],
                    },
                },
                "required": ["token_address", "webhook_url"],
            },
        ),

        # ─── Free Tools ───
        Tool(
            name="get_api_status",
            description=(
                "Get service status, performance metrics, trust score, and pricing. "
                "FREE — no payment required. Use this to verify the service is up before making paid calls."
            ),
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


# ─── Tool Handlers ────────────────────────────────────────────

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    try:
        handlers = {
            # Core risk
            "check_token_risk": lambda a: _post("/check-risk", {
                "token_address": a["token_address"], "chain": a.get("chain", "solana")}),
            "check_token_risk_premium": lambda a: _post("/check-risk-premium", {
                "token_address": a["token_address"], "chain": a.get("chain", "solana")}),
            "check_batch_risk": lambda a: _post("/check-batch", {
                "tokens": a["tokens"], "chain": a.get("chain", "solana")}),

            # Intelligence
            "check_deployer_history": lambda a: _get(f"/deployer/{a['deployer_address']}"),
            "get_token_intelligence": lambda a: _get(f"/token-intel/{a['token_address']}"),
            "get_holder_deepdive": lambda a: _get(f"/holder-deepdive/{a['token_address']}"),
            "get_social_osint": lambda a: _get(f"/social-osint/{a['token_address']}"),
            "get_kol_shills": lambda a: _get(f"/kol-shills/{a['token_address']}"),
            "get_coordinated_buys": lambda a: _get(f"/coordinated-buys?hours={a.get('hours', 72)}"),
            "check_blacklist": lambda a: _get(f"/blacklist/{a['token_address']}"),
            "check_scammer_wallet": lambda a: _get(f"/scammer-check/{a['wallet_address']}"),
            "get_market_risk_index": lambda a: _get("/market-risk"),
            "get_serial_ruggers": lambda a: _get(f"/serial-ruggers?min_tokens={a.get('min_tokens', 2)}"),

            # Marcus AI (longer timeouts)
            "marcus_quick": lambda a: _post("/marcus-quick", {
                "token_address": a["token_address"], "chain": a.get("chain", "solana"),
                **({"question": a["question"]} if a.get("question") else {})}, timeout=60),
            "marcus_forensics": lambda a: _post("/marcus-forensics", {
                "token_address": a["token_address"], "chain": a.get("chain", "solana")}, timeout=120),
            "marcus_ultra": lambda a: _post("/marcus-ultra", {
                "token_address": a["token_address"], "chain": a.get("chain", "solana")}, timeout=180),
            "marcus_thread": lambda a: _post("/marcus-thread", {
                "token_address": a["token_address"], "chain": a.get("chain", "solana")}, timeout=120),

            # Monitoring
            "watch_token": lambda a: _post("/watch", {
                "token_address": a["token_address"],
                "webhook_url": a["webhook_url"],
                "watch_type": a.get("watch_type", "rug_detected")}),

            # Free
            "get_api_status": lambda a: _get("/status"),
        }

        if name not in handlers:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

        result = await handlers[name](arguments)
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 402:
            return [TextContent(type="text", text=(
                "Payment required (HTTP 402). This endpoint requires x402 payment or an API key. "
                "See https://cryptorugmunch.app/api/agent/v1/status for pricing."
            ))]
        return [TextContent(type="text", text=f"API error {e.response.status_code}: {e.response.text[:200]}")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())


def main_sync():
    """Sync entry point for console_scripts."""
    asyncio.run(main())
