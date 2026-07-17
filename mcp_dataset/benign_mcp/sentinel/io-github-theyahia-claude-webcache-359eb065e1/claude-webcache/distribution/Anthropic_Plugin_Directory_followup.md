# Anthropic Plugin Directory — follow-up email/message

> **Context:** Submitted claude-webcache to Anthropic's official Plugin Directory on **2026-04-30**.
> Today is **2026-05-20** — **20 days elapsed**, SLA was 5-7 business days, **soft-overdue 13+ days**.
> Goal: polite nudge that opens dialog without sounding pushy. Make it easy to say "yes" or "still reviewing".

---

## Channel selection (pick one)

1. **Reply to original submission email** if the submission was email-based — preserves thread context for the reviewer.
2. **Anthropic Discord / Plugin Directory channel** if there's a public channel for submissions.
3. **support@anthropic.com / partnership-related contact form** as fallback if no thread exists.

**Default pick:** option 1 (reply-to-original). If you don't remember the thread, search Gmail for "plugin directory" / "claude code plugin" from 2026-04-30 ±2 days.

---

## Email draft (under 200 words, polite, action-oriented)

**Subject (if new thread):**
```
Re: claude-webcache plugin submission (theYahia, 2026-04-30) — v0.4.0 update
```

**Subject (if reply):**
```
Re: <original subject> — quick update + question
```

**Body:**

```
Hi <team>,

Quick follow-up on the claude-webcache plugin submission from April 30th.
I know reviews take time and don't want to rush the process — just wanted
to share a couple of updates and check whether anything's pending on my side.

Updates since submission:

- Just shipped v0.4.0 (npm: @theyahia/claude-webcache@0.4.0,
  GitHub tag v0.4.0). Highlights:
  - URL canonicalization fixing a silent cache-miss bug
  - Credential redaction for tokens in cached URLs
  - Namespace isolation per project
  - Concurrent schema-migration safety (busy_timeout + WAL init retry)
  - 53-test suite (unit + MCP stdio integration + concurrent stress)
- PulseMCP auto-ingested the listing.
- Glama listing exists but the auto-score hasn't generated in 20 days
  — separately reaching out to them; flagging in case it's relevant
  to the directory check.

Question: is there anything I can help with on the review side? Common
gaps I've seen on similar submissions are around CHANGELOG completeness,
test coverage, or marketplace.json format quirks (I've documented the
2.1.x parser behavior in CLAUDE.md if that's useful as reference).

Happy to provide additional materials or jump on a quick call if it
unblocks anything. No rush either way — appreciate the work that goes
into directory curation.

Thanks,
Tim
github.com/theYahia
```

---

## Tone analysis (why this works)

- **Opening line:** acknowledges review time → not adversarial.
- **Updates list:** signals project is alive and improving, not stagnant.
- **Question framing:** "anything I can help with" is the lowest-friction reply prompt — reviewer can answer yes/no in 10 seconds.
- **Offer to call:** opens a high-bandwidth channel without demanding it.
- **Closing line:** "no rush either way" softens the implicit pressure of a follow-up at all.

---

## What NOT to write

- ❌ "It's been 20 days, what's the holdup?" — adversarial, kills relationship.
- ❌ "When can I expect a decision?" — too demanding.
- ❌ "Other plugins got approved faster" — comparison = bad signal.
- ❌ "I have HN coverage scheduled" — implies pressure / threat.
- ❌ Long detailed feature list — reviewer doesn't have time to read 500 words.

---

## Followup-of-followup playbook

If no response in **7 more days** (i.e. by 2026-05-27):

- Send **one more** ping, even shorter (~80 words). Acknowledge the
  previous email, ask if there's an alternate contact, mention that
  v0.4.0 has been stable in npm for a week with no breaking issues.

If no response in **another 14 days** (i.e. by 2026-06-10):

- Stop pinging. Assume soft-rejection.
- Pivot strategy: focus on community-curated lists (awesome-mcp-servers,
  PulseMCP highlights, Glama featured) and direct distribution
  (Habr/HN/Reddit). Anthropic listing was nice-to-have, not blocking.

---

## Track in Board

After sending the email:

- Add line to `Bren.md` line 626 changelog: `2026-05-20 Anthropic Directory follow-up sent`
- Set reminder in `Board.md` to check status 2026-05-27
- Log thread URL/screenshot in `Cards/rd141 ...md` if that card exists, or
  create a new one with anchor rd-NEW

---

## Plan-B: if follow-up bounces or finds wrong contact

- Try: feedback@claude.ai
- Try: plugin-directory@anthropic.com (educated guess)
- Try: thread in Anthropic Developer Discord general channel — once,
  not in multiple channels
- Try: DM-ing a known Anthropic engineer on X who has tweeted about
  plugins (no spray — pick one based on relevant context)

**Hard rule:** if you've tried 4+ contact methods with zero response, the
signal is "not interested right now." Stop trying for ≥30 days; focus
on traction in the meantime. Inbound from end-users beats inbound from
Anthropic in 2026.
