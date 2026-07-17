# First Report Delivery

This is the buyer-facing shape of the first paid async install. It is designed to be useful even when the customer only wants a quick validation before deciding on a larger pilot.

## What The Buyer Gets In 24 Hours

- A customer-hosted Jobber MCP install with read-only access only.
- OAuth setup notes showing which Jobber account was connected.
- A short validation record: account check, client sample check, and one read-only GraphQL check.
- A first owner action list focused on missed follow-up and cash timing.
- A handoff note explaining what was checked, what was not changed, and what the owner can ask next.

## First Owner Action List

The first report is intentionally short. A useful report should answer:

- Which sent estimates are old enough to deserve follow-up?
- Which invoices are overdue or close to overdue?
- Which active jobs do not have a next visit scheduled?
- Which requests, quotes, or draft estimates appear stalled?
- Which five actions would be worth doing this week?

## Example Output

```text
OpsConduit Jobber First Report

Connected account:
- Verified Jobber account name and id
- Confirmed read-only GraphQL access
- No writes or mutations were run

Top action list:
1. Follow up on 4 sent estimates older than 7 days.
2. Review 3 overdue invoices before Friday.
3. Check 2 active jobs with no upcoming visit.
4. Clean up 5 stale requests or draft estimates.
5. Re-run this report next Monday before dispatch planning.

Notes:
- This is an operational triage report, not accounting, legal, or financial advice.
- The connector stays customer-hosted and does not require sharing Jobber passwords by email.
```

## Boundaries

OpsConduit does not ask for Jobber passwords, exported customer data, or write access. The async install is complete when the customer can run the read-only checks and has the first short report in hand.
