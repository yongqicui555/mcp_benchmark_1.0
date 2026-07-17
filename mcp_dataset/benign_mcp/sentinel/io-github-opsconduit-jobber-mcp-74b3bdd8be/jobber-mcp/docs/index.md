# OpsConduit Jobber MCP

Read-only Jobber reporting for owners who want a short action list without giving an AI tool write access.

## What It Produces

OpsConduit helps surface follow-up work that can be easy to miss:

- sent estimates older than 7 days
- overdue invoices
- active jobs with no upcoming visit
- draft estimates or requests that have stalled
- a short weekly owner action list

See the fictional sample output: [demo-output.md](demo-output.md)

See the first paid-install deliverable shape: [first-report.md](first-report.md)

## Why It Is Narrow

This project is deliberately not a broad automation tool. The default posture is:

- customer-hosted
- read-only
- no credential custody
- no autonomous writes to Jobber
- no customer data in public issues, docs, or email

## Pilot Setup

The paid pilot setup is for customers who want help installing the connector, authorizing Jobber, validating read-only access, and getting a first owner action list.

- Offer details: [offer.md](offer.md)
- First report delivery: [first-report.md](first-report.md)
- Pilot checklist: [pilot-checklist.md](pilot-checklist.md)
- Handoff template: [pilot-deliverable-template.md](pilot-deliverable-template.md)
- Jobber API notes: [jobber-api-notes.md](jobber-api-notes.md)
- Operator prompt library: [operator-prompts.md](operator-prompts.md)
- FAQ: [faq.md](faq.md)

Email `opsconduit@gmail.com` with the subject `Jobber pilot`.

Do not send Jobber passwords, tokens, API secrets, customer exports, or private customer data by email.

## Technical Repo

Install instructions and source are in the public GitHub repo:

https://github.com/opsconduit/jobber-mcp
