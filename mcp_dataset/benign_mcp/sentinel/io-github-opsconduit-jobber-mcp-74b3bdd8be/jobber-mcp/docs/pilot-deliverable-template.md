# Pilot Deliverable Template

This is the short deliverable OpsConduit sends after a paid Jobber MCP pilot setup. It is intentionally plain: the goal is to leave the owner or operator with a working connector, a validation record, and a first action list.

## 1. Install Summary

| Item | Value |
| --- | --- |
| Install date | YYYY-MM-DD |
| Installed by | OpsConduit / customer |
| Install location | Customer machine or server path |
| MCP client | Claude Desktop, Cursor, Codex, or other |
| Token storage | Local `.opsconduit/jobber-tokens.json` path |
| Write access | Disabled by default |

## 2. Validation Results

| Check | Result | Notes |
| --- | --- | --- |
| Jobber OAuth completed | Pass / Fail | Confirmed by customer-authorized OAuth callback |
| `jobber_account` | Pass / Fail | Account id and name returned |
| `jobber_clients_sample` | Pass / Fail | Small read-only client sample returned |
| Read-only GraphQL query | Pass / Fail | Customer-approved query returned data |
| Mutation guard | Pass / Fail | Mutation blocked unless local config explicitly allows it |

## 3. First Owner Action List

Use customer-approved read-only queries to produce a short list like:

1. Estimates older than 7 days that still need follow-up.
2. Overdue invoices with balance and age.
3. Active jobs with no upcoming visit.
4. Draft estimates or requests that have not moved forward.
5. Suggested owner questions for the next week.

## 4. Recommended Prompts

- Which sent estimates are older than 7 days and still open?
- Which overdue invoices should I collect this week?
- Which active jobs have no upcoming visit?
- Which draft estimates have been sitting for more than 2 days?
- Give me a short follow-up list ordered by likely revenue impact.

## 5. Handoff Notes

- OpsConduit does not need ongoing access to the customer's Jobber credentials.
- Tokens stay in the customer-controlled install unless a separate support path is agreed.
- The public repo is read-only by default and blocks GraphQL mutations unless local config explicitly changes that behavior.
- Maintenance can cover dependency updates, compatibility checks, and setup troubleshooting for the standard connector.
