# 11 — Docker MCP Registry

**URL:** https://github.com/docker/mcp-registry
**Submit:** PR adding `servers/halalterminal/server.yaml`
**Free:** Yes
**Review time:** Docker team review; days–weeks
**Path used:** **Remote server** (we don't ship a Docker image — we proxy to `mcp.halalterminal.com/sse`)

## Why a "remote" registration

Docker's registry has two tiers — **Local (containerized, requires Dockerfile)** and **Remote (hosted, accessed via HTTP/SSE)**. We use Remote because the actual MCP server runs on Halal Terminal infrastructure; the npm bridge is a client-side relay, not something to ship as a container.

## Workflow

```bash
cd /tmp
gh repo fork docker/mcp-registry --clone --remote
cd mcp-registry
git checkout -b add-halalterminal
mkdir -p servers/halalterminal
# create servers/halalterminal/server.yaml with the contents below
git add servers/halalterminal/server.yaml
git -c user.email=yassir@halalterminal.com -c user.name="Yassir" -c commit.gpgsign=false \
  commit -m "Add Halal Terminal remote MCP server"
git push -u origin add-halalterminal
gh pr create --title "Add Halal Terminal remote MCP server" \
  --body-file /root/halalterminal-mcp/submissions/docker-pr-body.md
```

## servers/halalterminal/server.yaml

```yaml
name: halalterminal
displayName: Halal Terminal
description: |
  Shariah-compliant stock & ETF screening across AAOIFI, DJIM, FTSE, MSCI and S&P
  methodologies, plus portfolio audit, zakat, dividend purification, market data,
  news, and SEC filings — for any MCP-compatible AI agent.
type: server
remote:
  transport: sse
  url: https://mcp.halalterminal.com/sse
  headers:
    - name: X-API-Key
      description: Halal Terminal API key (prefix ht_). Free tier at https://api.halalterminal.com — no credit card.
      required: true
      secret: true
metadata:
  license: Apache-2.0
  category: finance
  tags:
    - halal
    - shariah
    - islamic-finance
    - stock-screening
    - etf-screening
    - zakat
    - aaoifi
    - djim
    - ftse-shariah
    - msci-islamic
    - sp-shariah
  homepage: https://halalterminal.com
  source:
    type: github
    url: https://github.com/goww7/halalterminal-mcp
  maintainer:
    name: Yassir
    email: yassir@halalterminal.com
  logo: https://halalterminal.com/android-chrome-192x192.png
```

## docker-pr-body.md

(See companion file `docker-pr-body.md`.)

## Notes

- Docker requires **MIT or Apache-2.0** explicitly — we comply.
- They also require a **Test Credentials** form (https://forms.gle/6Lw3nsvu2d6nFg8e6 per CONTRIBUTING). Fill it with a fresh Free-plan API key dedicated to Docker review (revoke after merge to keep usage clean).
- "Every pull request requires a review from the Docker team before merging." — be patient, don't push for quicker review unless 3+ weeks.
