# 12 — MCPMarket (mcpmarket.com)

**URL:** https://mcpmarket.com/
**Submit:** Discover/claim flow at https://mcpmarket.com/submit (also auto-indexes from npm and the official registry)
**Free:** Yes
**Review:** auto-indexed; manual claim adds editorial fields

## Strategy

MCPMarket aggregates from multiple upstream sources, so once steps 01 (Official Registry) and 02 (npm) are done, your listing should appear automatically within ~48h. Then claim it for editorial control.

## Claim flow

1. Wait ~48h after Official Registry publish
2. Find your listing — search "halal" at https://mcpmarket.com/
3. Click **"Claim"** (GitHub OAuth — must own the linked repo)
4. Set the editorial fields below

## Editorial fields

| Field | Value |
|---|---|
| **Featured image** | A 1200×630 OG-style banner if you have one; else `https://halalterminal.com/android-chrome-192x192.png` |
| **Categories** | `Finance`, `Compliance`, `Research` |
| **Tags** | (paste keyword set from `copy-bank.md`) |
| **Why it's notable** | (paste **Elevator ≤280 chars**) |
| **Quick install snippet** | `npx -y @halalterminal/mcp` |
| **Setup time** | `≤1 min` |
| **Has free tier** | `Yes` |

## Notes

- MCPMarket sometimes runs "category spotlights" — Finance is one of their tracked verticals. If they do a halal/ethical-investing roundup, this listing is your shot at being the canonical entry.
