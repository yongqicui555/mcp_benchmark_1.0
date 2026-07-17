# `distribution/` — M3 Signal D launch materials

> Single source of truth for claude-webcache distribution drafts.
> Created 2026-05-20 as part of M3 Signal D push (target: ≥1 week ≥100 npm DLs by 31.07).

---

## Files

| File | Channel | Status | Owner |
|---|---|---|---|
| `HN_Show_submission.md` | Hacker News Show | Ready | User submits |
| `Reddit_r_ClaudeAI_submission.md` | Reddit r/ClaudeAI + r/LocalLLaMA + r/node | Ready | User submits |
| `Discord_posts.md` | Anthropic / MCP / Node Discord servers | Ready | User submits |
| `Anthropic_Plugin_Directory_followup.md` | Email to plugin directory team | Ready | User sends |

## Existing assets (elsewhere in project)

| File | Channel | Status |
|---|---|---|
| `../TWEET.md` | Twitter/X (3 variants) | Ready — but check 7-day TTL claim in variants A/B (v0.1.4+ is **unlimited TTL** by default) |
| `D:/Yahia/experiments/builder-story-content/habr_article_01_FINAL.md` | Habr | Ready — corrected 2026-05-20 to reflect post-launch decay reality |
| `D:/Yahia/experiments/builder-story-content/linkedin_post.md` | LinkedIn EN | Ready — 1380 chars |
| `D:/Yahia/experiments/builder-story-content/habr_article_01_publish_checklist.md` | Habr | Ready (pre-publish QA checklist) |

## Sequencing (W1: 20-26.05)

**Day 0 (today, 20.05 evening, depends on user actions):**
1. Restart Claude Code → rd975 Phase 4 smoke checks
2. `npm publish --otp=NNN` → v0.4.0 live
3. `mcp-publisher.exe publish` → MCP Registry updated
4. Verify `npm view @theyahia/claude-webcache version` = `0.4.0`

**Day +1-2 (21-22.05):**
5. Habr publish (`habr_article_01_FINAL.md`) — pre-publish checklist required
6. LinkedIn post (`linkedin_post.md`) — same day or +1
7. Twitter thread (`../TWEET.md` Variant A or B)

**Day +3-5 (23-25.05):**
8. HN Show (Tuesday 5-7am PT optimal) — see `HN_Show_submission.md`
9. Reddit r/ClaudeAI — same day as HN
10. Discord posts (3 servers, staggered 1 hour apart)
11. Anthropic Plugin Directory follow-up email (independently from HN — these are separate audiences)

**Day +6-7 (26-27.05):**
12. Monitor metrics (npm DLs, GitHub stars, HN/Reddit positions)
13. Reply to comments on all channels (response window first 6h critical)
14. Reddit r/LocalLLaMA (delayed cross-post)

## What to do if launch hits

If npm DLs spike >200/day OR HN reaches front page:

- DO update README with current metrics (but only after the spike, not during)
- DO ship v0.4.1 if real bugs get filed (signals "alive maintainer")
- DON'T tweet "we hit front page!" — let others surface it
- DON'T offer paid tier / consulting / Patreon — wrong context, breaks trust
- DO answer every issue / PR within 24h for the next 2 weeks

## What to do if launch flops (HN <50 points, Reddit <20 upvotes)

- Don't take it personally. MCP is still niche.
- Wait 2-3 weeks. Ship v0.4.1 / v0.5.0 with one substantive improvement.
- Try a different angle (technical deep-dive instead of project story).
- Consider second-tier channels: dev.to, Habr again (different angle), GitHub Trending niche tags.

## Tracking

Log each submission to `D:/Yahia/obsidian/Base/Inbox/launch-claude-webcache-<date>.md`:
- Channel
- Submit timestamp UTC
- URL / item ID
- 1h / 6h / 24h checkpoints (rank, score, comments)
- npm DL delta on the day
- Key comments (incl. negative — for v0.4.1 backlog)
