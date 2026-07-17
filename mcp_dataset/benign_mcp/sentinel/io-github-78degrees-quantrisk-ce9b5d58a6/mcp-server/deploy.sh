#!/bin/bash
# QuantRisk MCP — One-shot deployment script
# Run this AFTER: wrangler login (or CLOUDFLARE_API_TOKEN is set)
#
# Usage:
#   chmod +x deploy.sh
#   ./deploy.sh <ALPHA_VANTAGE_KEY> <STRIPE_SECRET_KEY> <STRIPE_WEBHOOK_SECRET>

set -euo pipefail

ALPHA_VANTAGE_KEY="${1:?Usage: ./deploy.sh <ALPHA_VANTAGE_KEY> <STRIPE_SECRET_KEY> <STRIPE_WEBHOOK_SECRET>}"
STRIPE_SECRET_KEY="${2:?Missing STRIPE_SECRET_KEY}"
STRIPE_WEBHOOK_SECRET="${3:?Missing STRIPE_WEBHOOK_SECRET}"

echo "==> Installing dependencies..."
npm install

echo "==> Creating KV namespace: PRICE_CACHE..."
KV_OUTPUT=$(npx wrangler kv namespace create PRICE_CACHE 2>&1)
KV_ID=$(echo "$KV_OUTPUT" | grep -oP 'id = "\K[^"]+' || echo "$KV_OUTPUT" | grep -oP '"[a-f0-9]{32}"' | tr -d '"')

if [ -z "$KV_ID" ]; then
  echo "ERROR: Could not extract KV namespace ID. Output was:"
  echo "$KV_OUTPUT"
  echo ""
  echo "If the namespace already exists, find it with: npx wrangler kv namespace list"
  echo "Then manually update wrangler.toml with the correct id."
  exit 1
fi

echo "    KV namespace ID: $KV_ID"

# Update wrangler.toml with real KV namespace ID
if [[ "$OSTYPE" == "darwin"* ]]; then
  sed -i '' "s/REPLACE_WITH_KV_NAMESPACE_ID/$KV_ID/" wrangler.toml
else
  sed -i "s/REPLACE_WITH_KV_NAMESPACE_ID/$KV_ID/" wrangler.toml
fi
echo "    Updated wrangler.toml"

echo "==> Setting Worker secrets..."
echo "$ALPHA_VANTAGE_KEY" | npx wrangler secret put ALPHA_VANTAGE_KEY
echo "$STRIPE_SECRET_KEY" | npx wrangler secret put STRIPE_SECRET_KEY
echo "$STRIPE_WEBHOOK_SECRET" | npx wrangler secret put STRIPE_WEBHOOK_SECRET

echo "==> Deploying to Cloudflare Workers..."
npx wrangler deploy

echo ""
echo "==> Deployment complete!"
echo ""
echo "Your QuantRisk MCP server is live."
echo "Health check: curl https://quantrisk-mcp.<your-subdomain>.workers.dev/health"
echo ""
echo "Next steps:"
echo "  1. Set up Stripe webhook pointing to: https://quantrisk-mcp.<your-subdomain>.workers.dev/stripe-webhook"
echo "  2. Add the MCP server to Claude Desktop (see claude-desktop-config.json)"
echo "  3. Test: 'What is the VaR of 100 shares of AAPL at 95% confidence?'"
