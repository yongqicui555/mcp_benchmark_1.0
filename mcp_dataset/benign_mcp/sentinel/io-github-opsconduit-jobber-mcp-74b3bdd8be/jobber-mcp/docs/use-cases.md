# Jobber MCP Use Cases

OpsConduit is meant for owner/operator follow-up work, not generic chat.

## Daily Owner Summary

Ask:

```text
What needs attention in Jobber today?
```

Useful output:

- unscheduled jobs
- estimates that need follow-up
- overdue invoices
- stale requests
- customers with no recent activity

## Estimate Follow-Up

Ask:

```text
Which quotes or estimates should I follow up on this week?
```

Useful output:

- open quotes
- age of each quote
- customer name
- suggested next action

## Invoice Review

Ask:

```text
Which invoices appear overdue or need attention?
```

Useful output:

- overdue invoice list
- customer name
- balance
- age
- whether a manual review is needed

## Schedule Gaps

Ask:

```text
Which jobs are not scheduled yet?
```

Useful output:

- job/request name
- customer
- current status
- created date
- recommended follow-up

## Why Read-Only Matters

The connector is read-only by default because operational reporting should not require giving an AI tool permission to change Jobber data.

Write actions are outside the standard scope and should require a separate agreement.
