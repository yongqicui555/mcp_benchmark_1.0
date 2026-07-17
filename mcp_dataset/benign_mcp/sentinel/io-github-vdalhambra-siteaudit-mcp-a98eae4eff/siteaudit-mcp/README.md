[![PyPI version](https://img.shields.io/pypi/v/siteaudit-mcp)](https://pypi.org/project/siteaudit-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Glama MCP Server](https://glama.ai/mcp/servers/vdalhambra/siteaudit-mcp/badges/score.svg)](https://glama.ai/mcp/servers/vdalhambra/siteaudit-mcp)

<!-- mcp-name: io.github.vdalhambra/siteaudit-mcp -->

# SiteAudit MCP

**Instant SEO, Performance, and Security Audits for AI Agents** — analyze any URL with a single tool call via the Model Context Protocol (MCP).

SiteAudit is an MCP server that gives Claude Code, Cursor, Windsurf, and any AI agent the ability to audit any website instantly. No API keys, no configuration, no cost. The complete website audit toolkit for AI-powered development.

> **Try it now — no install needed:** [Open SiteAudit in the MCPize Playground](https://mcpize.com/mcp/siteaudit-mcp/playground) — runs in your browser, free tier (100 audits/month)

## Use Cases

Here are concrete examples of what you can ask your AI agent once SiteAudit is installed:

- **"Audit example.com and give me a prioritized list of SEO fixes"** — Full SEO audit with title tags, meta descriptions, headings, structured data, Open Graph, and actionable recommendations
- **"Check the security headers on my production site"** — HTTPS, HSTS, CSP, X-Frame-Options, cookie flags, SSL certificate validity, and server disclosure
- **"Compare my site vs 3 competitors side-by-side"** — Multi-site comparison with scores for SEO, performance, and security across all sites
- **"Run a Lighthouse audit on my homepage"** — Google PageSpeed Insights performance, accessibility, best practices, and SEO scores
- **"Find all broken links on my site"** — Crawl internal and external links, report 404s, redirects, and unreachable URLs
- **"Check if my robots.txt is blocking anything important"** — Parse robots.txt rules, find sitemap references, and identify potential crawl issues

## Why SiteAudit?

| Feature | SiteAudit MCP | Ahrefs | Screaming Frog | Google Lighthouse |
|---------|--------------|--------|----------------|-------------------|
| Works with Claude Code / Cursor | Yes | No | No | CLI only |
| No API key needed | Yes | No ($99/mo) | Free (limited) | Yes |
| SEO + Security + Performance | All three | SEO only | SEO only | Performance only |
| AI-native (MCP protocol) | Yes | REST API | Desktop app | CLI / API |
| Broken link checker | Yes | Yes | Yes | No |
| Lighthouse integration | Yes | No | No | It is Lighthouse |
| Multi-site comparison | Yes | Manual | Manual | Manual |
| Free | Yes | $99+/mo | Free (500 URLs) | Yes |

## Tools (8)

| Tool | Description |
|------|-------------|
| `full_audit` | Comprehensive SEO + performance + security audit with unified score (0-100) |
| `seo_audit` | SEO analysis: title, meta, headings, images, links, structured data, Open Graph |
| `security_audit` | Security headers, HTTPS, HSTS, CSP, SSL certificate check, cookie flags |
| `performance_audit` | Response time, page size, compression, caching, redirects |
| `compare_sites` | Side-by-side comparison of multiple websites |
| `lighthouse_audit` | Google PageSpeed Insights: performance, accessibility, best practices, SEO |
| `check_links` | Crawl and validate all links on a page — find broken links, redirects, timeouts |
| `check_robots_txt` | Parse and analyze robots.txt rules, directives, and sitemaps |

## Installation

### ⭐ Recommended: MCPize (hosted, no setup)

The fastest way to get started. No terminal, no config files, no Python setup — works in any MCP client:

👉 **[Install SiteAudit on MCPize](https://mcpize.com/mcp/siteaudit-mcp)** — Free tier available (100 audits/month)

Or add to your MCP config directly:

```json
{
  "mcpServers": {
    "siteaudit": {
      "url": "https://siteaudit-mcp.mcpize.run/mcp"
    }
  }
}
```

**Why MCPize?**
- ✅ Zero setup — works immediately in Claude Desktop, Cursor, Windsurf, Claude Code
- ✅ Always up-to-date — new SEO checks and features added continuously
- ✅ Scales with you — upgrade to Pro ($19/mo) for 10,000 audits + full Lighthouse + priority
- ✅ No rate limits on PageSpeed API — we handle the Google quota for you
- ✅ Reliable uptime — managed cloud infrastructure

See [pricing](#pricing) below for all tiers including Agency and Enterprise.

---

### 💻 Advanced: Self-hosted (developers)

For those who prefer to run the server locally:

<details>
<summary><b>Claude Code CLI</b></summary>

```bash
claude mcp add siteaudit -- uvx --from siteaudit-mcp siteaudit
```
</details>

<details>
<summary><b>Claude Desktop / Cursor / Windsurf (local)</b></summary>

```json
{
  "mcpServers": {
    "siteaudit": {
      "command": "uvx",
      "args": ["--from", "siteaudit-mcp", "siteaudit"]
    }
  }
}
```
</details>

<details>
<summary><b>From PyPI</b></summary>

```bash
pip install siteaudit-mcp
siteaudit
```
</details>

<details>
<summary><b>From source</b></summary>

```bash
git clone https://github.com/vdalhambra/siteaudit-mcp.git
cd siteaudit-mcp
uv sync
uv run siteaudit
```
</details>

<details>
<summary><b>Smithery</b></summary>

```bash
npx -y @smithery/cli install @vdalhambra/siteaudit --client claude
```
</details>

> **Note:** Self-hosted = full feature access but you manage updates, uptime, and Google PageSpeed quotas. For most users, MCPize is the better choice.

---

## Pricing

| Tier | Price | Audits/month | Includes |
|------|-------|--------------|----------|
| **Free** | $0 | 100 | Basic audit (no Lighthouse) |
| **Hobby** | $7/mo | 2,500 | Full audit without site comparison |
| **Pro** ⭐ | $19/mo | 10,000 | All 8 tools + full Lighthouse + priority |
| **Agency** | $49/mo | 50,000 | Pro + 10 saved sites + scheduled audits |
| **Agency Plus** | $119/mo | 200,000 | Agency + white-label PDF reports + 25 seats |
| **Enterprise** | $349/mo | Unlimited | Agency Plus + on-prem + custom integrations + SLA |

**Annual plans:** Get 2 months free (pay for 10, use 12).

**Bundle:** Combine with [FinanceKit MCP](https://github.com/vdalhambra/financekit-mcp) for **$39/mo** (Pro Combo — save 19%).

👉 **[View all pricing on MCPize](https://mcpize.com/mcp/siteaudit-mcp)**

## What it checks

### SEO Audit (20+ checks)
- Title tag (presence, length optimization)
- Meta description (presence, length)
- H1 tag (count, content)
- Heading hierarchy (H1-H6)
- Image alt text coverage
- Internal/external link count
- Canonical URL
- Open Graph tags
- Twitter Card tags
- Mobile viewport
- Structured data (JSON-LD)
- Favicon
- Language attribute
- robots meta directives
- Content length (word count)

### Security Audit (10+ checks)
- HTTPS enforcement
- HSTS header (with subdomains and preload)
- Content-Security-Policy
- X-Content-Type-Options
- X-Frame-Options
- Referrer-Policy
- Permissions-Policy
- Server/X-Powered-By disclosure
- Cookie security flags (Secure, HttpOnly, SameSite)
- SSL certificate validity and expiration

### Performance Audit
- Server response time (ms)
- Page size (KB)
- Compression (gzip/brotli)
- Cache-Control headers
- Redirect chain analysis
- HTTP status code

### Lighthouse Audit (via Google PageSpeed Insights)
- Performance score
- Accessibility score
- Best practices score
- SEO score
- Core Web Vitals (FCP, LCP, TBT, CLS)

## Example Output

```
URL: https://github.com
Overall Score: 90/100 (Grade: A)

Scores:
  SEO: 85/100
  Performance: 95/100
  Security: 90/100

Issues: 0
Warnings: 3
  [SEO] No JSON-LD structured data
  [Security] Missing Content-Security-Policy header
  [Security] Server header discloses: 'GitHub.com'
```

## No API Keys Required

SiteAudit works entirely by analyzing the HTML and HTTP headers of the target URL. No third-party API keys needed. It uses:
- `requests` for HTTP fetching
- `BeautifulSoup` for HTML parsing
- Python `ssl` for certificate checking
- Google PageSpeed Insights API (free, no key required for basic usage)

## Compatible AI Agents

SiteAudit works with any AI agent or IDE that supports the Model Context Protocol:

- **Claude Code** (CLI) — `claude mcp add`
- **Claude Desktop** — `claude_desktop_config.json`
- **Cursor** — `.cursor/mcp.json`
- **Windsurf** — MCP settings
- **Copilot** — MCP configuration
- **Any MCP client** — stdio or HTTP transport

## Support this project

If SiteAudit is useful to you, please consider supporting ongoing development:

- 💎 **[Upgrade to Pro on MCPize](https://mcpize.com/mcp/siteaudit-mcp)** — Best way to support + get priority access
- ⭐ **Star this repo** — Helps other developers find it
- 💖 **[Sponsor on GitHub](https://github.com/sponsors/vdalhambra)** — One-time or recurring support
- 🐦 **Share on Twitter/X** — Tag [@ElAgenteRayo](https://twitter.com/ElAgenteRayo)

## License

MIT
