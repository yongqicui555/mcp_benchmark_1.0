# 08 — Cursor Directory

**URL:** https://cursor.directory/mcp
**Submit:** "Submit" in top-right (typically https://cursor.directory/submit or https://cursor.directory/mcp/submit)
**Free:** Yes
**Review time:** ~1–3 days

## Field mapping

| Field | Value |
|---|---|
| **Name** | `Halal Terminal` |
| **Slug** | `halal-terminal` |
| **Description** | (paste **Elevator ≤280 chars**) |
| **Long description** | (paste **Full description ≤800 chars**) |
| **GitHub** | `https://github.com/goww7/halalterminal-mcp` |
| **Categories / Tags** | `finance`, `productivity`, `mcp` |
| **NPM package** | `@halalterminal/mcp` |
| **Install command** | `npx -y @halalterminal/mcp` |
| **Required env** | `HALALTERMINAL_API_KEY` |
| **Logo URL** | `https://halalterminal.com/android-chrome-192x192.png` |
| **Author** | `Yassir` |

## Cursor-specific install snippet (paste in description)

````
{
  "mcpServers": {
    "halalterminal": {
      "url": "https://mcp.halalterminal.com/sse?api_key=ht_yourkey"
    }
  }
}
````

## Notes

- Cursor Directory ranks listings partly by GitHub stars and recency of last release — push your first npm release **before** submitting so the listing shows a fresh `published 0d ago`.
- They highlight new entries on the homepage for ~48h after approval — coordinate any social posts to that window.
