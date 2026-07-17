# QuantRisk MCP — X Thread Draft

*5-7 tweets. Punchy and data-driven. Target: quant traders, developers building with AI, MCP ecosystem watchers.*

---

**Tweet 1 (hook)**

I researched 10,000+ MCP servers trying to find one that computes portfolio risk.

There isn't one.

So I built it.

Introducing @QuantRiskMCP — VaR, Monte Carlo, optimization, stress testing, and Greeks inside your AI assistant.

Thread 🧵

---

**Tweet 2 (the gap)**

The gap is wild when you see it.

You can ask Claude to:
- Check your GitHub PRs ✅
- Query your database ✅
- Send a Slack message ✅

Ask it "what's my portfolio's VaR at 95% confidence?"

You get an explanation of what VaR is.

Not an answer.

---

**Tweet 3 (what it does)**

QuantRisk gives your AI 10 tools:

→ analyze_risk — VaR, CVaR, volatility, beta, drawdown
→ monte_carlo_simulation — 100K paths, percentile outcomes
→ stress_test — GFC 2008, COVID, dot-com, Black Monday
→ optimize_portfolio — max Sharpe, min variance (Markowitz)
→ calculate_greeks — delta/gamma/theta/vega/rho
→ + 5 more

All in natural language. No Python. No Bloomberg.

---

**Tweet 4 (example)**

Real example:

You: "Stress test my AAPL/MSFT/NVDA portfolio against 2008 and COVID."

Claude runs the tool, comes back with:

"2008: -$41,200 (-19.7%). NVDA was worst (-28.4%). COVID: -$33,800 (-16.2%). Both events hit tech hard. Consider tail-risk hedges."

That's not a hallucination. That's structured computation.

---

**Tweet 5 (technical decisions)**

Technical choices that matter:

• Cloudflare Workers — edge latency, not Lambda cold starts
• Stateless — positions inline per call, no session state
• TypeScript — native MCP SDK, type-safe math
• KV price cache — daily prices cached 24hrs, protects upstream limits

10K Monte Carlo paths return in under 2 seconds.

---

**Tweet 6 (pricing + free tier)**

Pricing is simple:

Free: 7/10 tools, 20 positions, 1K Monte Carlo paths, 100 calls/day. Actually useful.

Pro ($29/mo): All 10 tools, 500 positions, 100K paths, custom stress scenarios.

For comparison: Bloomberg terminal = $24,000/year.

$29/month is the easiest upsell in quant finance.

---

**Tweet 7 (CTA)**

Try it now:

npm install -g @quantrisk/mcp-server

Free API key at quantrisk.dev
One JSON block in Claude Desktop config
Ask your first risk question in 2 minutes

Code is MIT on GitHub: github.com/quantrisk/mcp-server

If you're a quant or PM using AI — I want to know what tools you're missing.

---

*Notes for posting:*
- *Post tweets 1-7 as a single thread from the @QuantRiskMCP account or personal account*
- *Pin tweet 1 and add the quantrisk.dev link to bio before posting*
- *Ideal timing: Tuesday or Wednesday, 9-11am ET for maximum dev/finance audience*
- *Target accounts to tag/reply: @mcp_so, @PulseMCP, quant finance communities on X*
- *Consider quote-tweeting any MCP round-up posts the same week*
