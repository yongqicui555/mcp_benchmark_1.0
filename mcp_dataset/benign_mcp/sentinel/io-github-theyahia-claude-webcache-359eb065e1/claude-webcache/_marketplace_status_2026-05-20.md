# Marketplace Distribution Status Sweep — 2026-05-20

**Timeline:** Submission 2026-04-30 ~15:30 GMT+3 → Today (20 days elapsed)

---

## Platform Status Table

| Platform | URL Checked | Status | Notes | Action |
|----------|------------|--------|-------|--------|
| **Glama (direct)** | `glama.ai/mcp/servers/theYahia/claude-webcache` | ✅ LIVE | Listing active but score = "–" (not tested) | Extract badge URL from page when score available |
| **Glama (search)** | `glama.ai/mcp/servers?q=claude-webcache` | ❌ NOT FOUND | Search index does not surface it | Likely requires badge + score before search indexing |
| **Glama (author search)** | `glama.ai/mcp/servers?q=theyahia` | ❌ NOT FOUND | Author pages not surfacing via public search | Possible backend indexing delay |
| **PulseMCP** | `pulsemcp.com/servers?q=claude-webcache` | ✅ LISTED | 1 result: "Claude Web Cache" by theYahia | Community server, released Apr 29, 2026 |
| **PulseMCP (author)** | `pulsemcp.com/servers?q=theyahia` | ✅ VERIFIED | **55 total servers** (42 displayed per page) | All Yahia servers present; auto-ingest working |
| **MCP.so** | `mcp.so/servers` + search | 🚫 BLOCKED | HTTP 403 Forbidden on all endpoints | Cannot verify; possible auth-gated or CF protection |
| **awesome-mcp-servers PR** | `github.com/punkpeye/awesome-mcp-servers/pull/5649` | ❌ CLOSED | PR closed 2026-05-01 09:10:44 UTC **without merge** | Bot required Glama badge; was never completed |

---

## Key Findings

### 1. **Glama Dual State** (rd137 + rd140)
- **Listing exists:** `https://glama.ai/mcp/servers/theYahia/claude-webcache` is publicly accessible
- **BUT:** Score not yet generated ("–" shown); marked "not tested"
- **Search indexing blocked:** Neither search queries (`?q=claude-webcache` or `?q=theyahia`) surface the listing
- **Likely root cause:** Glama auto-check (Dockerfile introspection) has not completed or failed silently
- **Badge URL structure:** Not yet available; typical pattern would be `glama.ai/mcp/servers/theYahia/claude-webcache/badges/score.svg`

### 2. **PulseMCP SUCCESS** (rd139) ✅
- Server **auto-ingested successfully** from Official MCP Registry
- All 55 theYahia servers present; claude-webcache listed
- **No action needed** — PulseMCP downstream integration working as expected

### 3. **MCP.so** (rd139)
- Cannot access; returns HTTP 403 Forbidden
- Likely blocked by Cloudflare or requires auth token
- Unable to verify status; recommend support contact if critical

### 4. **awesome-mcp-servers PR #5649** (rd137)
- **Status:** Closed without merge (2026-05-01 09:10:44 UTC)
- **Root cause:** Glama auto-checker bot required passing score badge; submitter closed PR rather than fix Glama score
- **Timeline:** Bot comment → No response from submitter → PR closed by submitter
- **Current state:** PR does NOT have badge; cannot re-open without completing Glama score requirement

### 5. **WWmcp Catalog Cross-Check** (bonus rd1047)
- Not yet submitted (as expected — planned for Day 26 / Mon 2026-05-26)
- Baseline verified: no entries on PulseMCP, Glama, or MCP.so yet

---

## Actionable User Tasks

### Immediate (Today)

1. **Investigate Glama Score Generation** → Why is auto-check not scoring?
   - Check Glama logs/dashboard for build errors
   - Verify `glama.json` + `Dockerfile` are correctly formatted for their auto-introspection
   - Contact Glama support if >7 days of silence: **Draft message ready** (see below)

2. **Optional: Discord Ping to Glama** (only if you want expedited score)
   - **20-day silence** on score generation → reasonable trigger for support escalation
   - Draft message below — copy to https://glama.ai/discord (if link in their footer)

3. **awesome-mcp-servers PR #5649:** Cannot re-open until Glama score available
   - Once badge URL extracted → will need to fork / submit new PR with badge markdown

### Secondary (When Glama Score Appears)

4. **Extract Glama Badge URL**
   - Glama will provide: `https://glama.ai/mcp/servers/theYahia/claude-webcache/badges/score.svg`
   - Format for PR: `[![score](https://glama.ai/mcp/servers/theYahia/claude-webcache/badges/score.svg)](https://glama.ai/mcp/servers/theYahia/claude-webcache)`

5. **Re-submit awesome-mcp-servers**
   - New PR with badge + listing URL
   - Should pass bot this time (if score ≥ threshold)

6. **Verify MCP.so** (if critical to distribution)
   - Try authenticated fetch or contact MCP.so support to debug 403

---

## Discord Draft Message (if needed)

```
Submitted claude-webcache server (io.github.theYahia/claude-webcache @ v0.1.3) 
to Glama Registry at 2026-04-30 ~15:30 UTC+3.

Listing appears here: https://glama.ai/mcp/servers/theYahia/claude-webcache
BUT: Auto-check score not yet generated (shows "–" / "not tested" for 20 days).

Dockerfile and glama.json appear valid. Has build processing stalled, or is review pending?
No email reply from submission contact form. Status?
```

---

## Summary

| Metric | Result |
|--------|--------|
| **Glama listing live?** | ✅ Yes (but no score) |
| **PulseMCP ingested?** | ✅ Yes (auto-successful) |
| **MCP.so accessible?** | ❌ Blocked (403) |
| **awesome-mcp-servers merged?** | ❌ No (PR closed; needs badge) |
| **Days since submission** | 20 |
| **Blocker: Glama score** | ⏳ Still waiting |
| **User action required?** | ✅ Yes (Glama follow-up) |

---

**Next sweep recommended:** 2026-05-23 (Day 23, check if Glama score appears or if Discord response arrives)

