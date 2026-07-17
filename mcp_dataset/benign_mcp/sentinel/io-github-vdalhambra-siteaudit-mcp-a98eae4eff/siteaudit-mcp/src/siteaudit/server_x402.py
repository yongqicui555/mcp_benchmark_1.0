"""SiteAudit HTTP server with x402 pay-per-call micropayments.

OPTIONAL entrypoint — adds pay-per-call USDC payments via x402 protocol.
For MCPize-hosted and self-hosted stdio users, use the regular `siteaudit`
command (via `siteaudit.server:main`) — no payment flow.

### Usage

Set environment variables:
    EVM_ADDRESS          # Your receiving wallet (required)
    FACILITATOR_URL      # Default: https://x402.org/facilitator
    X402_NETWORK         # Default: eip155:8453 (Base mainnet)
    PORT                 # Default: 4023

Run:
    python -m siteaudit.server_x402

### Pricing applied

Free tools: check_robots_txt
Paid tools:
    - seo_audit, security_audit, performance_audit:    $0.02
    - full_audit, lighthouse_audit:                    $0.10
    - compare_sites, check_links, competitor_gap_analysis:  $0.15

### Dependencies

    x402[mcp,evm]>=2.7.0
    fastmcp>=3.2.3
    uvicorn[standard]>=0.20

See docs/X402_DEPLOYMENT.md for full deployment guide.
"""

import json
import os
import sys

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from x402.http import FacilitatorConfig, HTTPFacilitatorClientSync
    from x402.mcp import (
        MCPToolResult,
        SyncPaymentWrapperConfig,
        create_payment_wrapper_sync,
        wrap_fastmcp_tool_sync,
    )
    from x402.schemas import ResourceConfig
    from x402.server import x402ResourceServerSync
    from x402.mechanisms.evm.exact import ExactEvmServerScheme
except ImportError:
    sys.stderr.write(
        "x402 not installed. Run: uv add 'x402[mcp,evm]>=2.7.0' uvicorn\n"
    )
    sys.exit(1)

from fastmcp import FastMCP, Context

from siteaudit.utils.fetcher import fetch_page
from siteaudit.analyzers.seo import analyze_seo
from siteaudit.analyzers.security import analyze_security
from siteaudit.analyzers.performance import analyze_performance

# Config
EVM_ADDRESS = os.environ.get("EVM_ADDRESS")
if not EVM_ADDRESS:
    sys.stderr.write("EVM_ADDRESS env var is required.\n")
    sys.exit(1)

FACILITATOR_URL = os.getenv("FACILITATOR_URL", "https://x402.org/facilitator")
NETWORK = os.getenv("X402_NETWORK", "eip155:8453")
PORT = int(os.getenv("PORT", "4023"))

PRICE_BASIC = "$0.02"    # Single-category audits
PRICE_FULL = "$0.10"     # Full audit, lighthouse
PRICE_PREMIUM = "$0.15"  # Multi-site, crawls, gap analysis


mcp = FastMCP(
    name="SiteAudit (x402)",
    instructions=(
        "SiteAudit with pay-per-call x402 micropayments. "
        "Single-category audits $0.02, full audits $0.10, multi-site/crawl $0.15. "
        "Receives USDC on Base mainnet."
    ),
    version="1.2.0",
)

facilitator = HTTPFacilitatorClientSync(FacilitatorConfig(url=FACILITATOR_URL))
resource_server = x402ResourceServerSync(facilitator)
resource_server.register(NETWORK, ExactEvmServerScheme())
resource_server.initialize()


def accepts_for(price_usd: str):
    return resource_server.build_payment_requirements(
        ResourceConfig(
            scheme="exact",
            network=NETWORK,
            pay_to=EVM_ADDRESS,
            price=price_usd,
            extra={"name": "USDC", "version": "2"},
        )
    )


basic_accepts = accepts_for(PRICE_BASIC)
full_accepts = accepts_for(PRICE_FULL)
premium_accepts = accepts_for(PRICE_PREMIUM)

paid_basic = create_payment_wrapper_sync(
    resource_server, SyncPaymentWrapperConfig(accepts=basic_accepts)
)
paid_full = create_payment_wrapper_sync(
    resource_server, SyncPaymentWrapperConfig(accepts=full_accepts)
)
paid_premium = create_payment_wrapper_sync(
    resource_server, SyncPaymentWrapperConfig(accepts=premium_accepts)
)


def _run_seo(url: str) -> dict:
    resp, soup = fetch_page(url)
    return analyze_seo(resp.url, resp, soup)


def _run_security(url: str) -> dict:
    resp, _ = fetch_page(url)
    return analyze_security(resp.url, resp)


def _run_performance(url: str) -> dict:
    resp, _ = fetch_page(url)
    return analyze_performance(resp.url, resp)


def _run_full_audit(url: str) -> dict:
    resp, soup = fetch_page(url)
    seo = analyze_seo(resp.url, resp, soup)
    sec = analyze_security(resp.url, resp)
    perf = analyze_performance(resp.url, resp)
    overall = round(seo["score"] * 0.4 + perf["score"] * 0.3 + sec["score"] * 0.3)
    return {
        "url": resp.url,
        "overall_score": overall,
        "seo": seo,
        "security": sec,
        "performance": perf,
    }


def make_paid_handler(wrapper, logic_fn, tool_name: str):
    def bridge(args: dict, _ctx):
        result = logic_fn(**args)
        return MCPToolResult(
            content=[{"type": "text", "text": json.dumps(result, default=str)}]
        )
    return wrap_fastmcp_tool_sync(wrapper, bridge, tool_name=tool_name)


paid_seo_audit = make_paid_handler(paid_basic, _run_seo, "seo_audit")
paid_security_audit = make_paid_handler(paid_basic, _run_security, "security_audit")
paid_performance_audit = make_paid_handler(paid_basic, _run_performance, "performance_audit")
paid_full_audit = make_paid_handler(paid_full, _run_full_audit, "full_audit")


@mcp.tool()
def seo_audit(url: str, ctx: Context):
    """SEO analysis: 20+ checks. $0.02/call via x402."""
    return paid_seo_audit({"url": url}, ctx)


@mcp.tool()
def security_audit(url: str, ctx: Context):
    """Security headers + SSL check. $0.02/call via x402."""
    return paid_security_audit({"url": url}, ctx)


@mcp.tool()
def performance_audit(url: str, ctx: Context):
    """Response time, size, compression, caching. $0.02/call via x402."""
    return paid_performance_audit({"url": url}, ctx)


@mcp.tool()
def full_audit(url: str, ctx: Context):
    """SEO + security + performance in one call. $0.10/call via x402."""
    return paid_full_audit({"url": url}, ctx)


@mcp.tool()
def ping() -> str:
    """Health check. Free."""
    return "pong"


@mcp.tool()
def pricing_info() -> dict:
    """Current x402 pricing tiers. Free."""
    return {
        "basic_usd": PRICE_BASIC,
        "basic_tools": ["seo_audit", "security_audit", "performance_audit"],
        "full_usd": PRICE_FULL,
        "full_tools": ["full_audit", "lighthouse_audit"],
        "premium_usd": PRICE_PREMIUM,
        "premium_tools": ["compare_sites", "check_links", "competitor_gap_analysis"],
        "network": NETWORK,
        "pay_to": EVM_ADDRESS,
        "token": "USDC",
        "facilitator": FACILITATOR_URL,
    }


# Note: Only basic + full_audit tiers are wired here for clarity.
# Premium tier tools (compare_sites, check_links, competitor_gap_analysis)
# follow the same pattern — see server_x402.py in FinanceKit or the
# Coinbase x402 advanced examples for the complete wrapper code.


def main():
    """Run the x402 HTTP MCP server."""
    print(f"SiteAudit x402 MCP on http://localhost:{PORT}/sse")
    print(f"  pay-to: {EVM_ADDRESS}")
    print(f"  network: {NETWORK}")
    print(f"  facilitator: {FACILITATOR_URL}")
    mcp.run(transport="sse", host="0.0.0.0", port=PORT)


if __name__ == "__main__":
    main()
