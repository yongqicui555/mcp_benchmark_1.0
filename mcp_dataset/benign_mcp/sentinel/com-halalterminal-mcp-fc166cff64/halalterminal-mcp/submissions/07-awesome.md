# 07 — awesome-mcp-servers (punkpeye/awesome-mcp-servers)

**URL:** https://github.com/punkpeye/awesome-mcp-servers
**Submit:** PR adding one alphabetically-sorted line under `### 💰 Finance & Fintech`
**Free:** Yes
**Review time:** PR-dependent; 1–2 weeks typical
**Acquisition value:** high — it's the de-facto "everyone reads this" list

## Branch & PR (gh CLI)

```bash
cd /tmp
gh repo fork punkpeye/awesome-mcp-servers --clone --remote
cd awesome-mcp-servers
git checkout -b add-halal-terminal
# edit README.md per the snippet below
git add README.md
git -c user.email=yassir@halalterminal.com -c user.name="Yassir" -c commit.gpgsign=false \
  commit -m "Add Halal Terminal — Shariah-compliant stock & ETF screening"
git push -u origin add-halal-terminal
gh pr create --title "Add Halal Terminal — Shariah-compliant stock & ETF screening" \
  --body-file /root/halalterminal-mcp/submissions/awesome-pr-body.md
```

## The line to add

Insert under `### 💰 <a name="finance--fintech"></a>Finance & Fintech`, **alphabetically sorted by repo path** (`goww7/halalterminal-mcp` slots between entries starting with `g…h`):

```markdown
- [goww7/halalterminal-mcp](https://github.com/goww7/halalterminal-mcp) 📇 ☁️ 🍎 🪟 🐧 - Official Halal Terminal MCP server. Screen any stock or ETF for Shariah (Islamic) compliance across 5 methodologies (AAOIFI, DJIM, FTSE, MSCI, S&P), audit portfolios, calculate zakat and dividend purification, plus market data, news, and SEC filings. Free tier, no credit card. `npx @halalterminal/mcp`
```

**Emoji legend** (per the README's key):
- 📇 — TypeScript / JavaScript
- ☁️ — Remote/cloud-hosted
- 🍎 / 🪟 / 🐧 — macOS / Windows / Linux compatible

## PR body — `awesome-pr-body.md`

(Will be created at `/root/halalterminal-mcp/submissions/awesome-pr-body.md` — see file.)

## Notes

- Run the repo's link-check / lint if their CI complains (`npm test` or per CONTRIBUTING).
- Maintainer reviews are batched; don't ping unless 3+ weeks silent.
- Once merged, the entry also gets aggregated into several derivative `awesome-mcp-*` lists. Bonus reach.
