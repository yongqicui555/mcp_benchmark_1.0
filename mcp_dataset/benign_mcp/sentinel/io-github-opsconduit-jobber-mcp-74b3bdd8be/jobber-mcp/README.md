# OpsConduit Jobber MCP

Read-only MCP connector for Jobber field-service operations.

OpsConduit helps owners and operators ask practical questions about the tools that run their business. This first connector is for Jobber and is designed to stay read-only by default.

Plain buyer-facing overview: [docs/index.md](docs/index.md).
Common buyer questions are answered in [docs/faq.md](docs/faq.md).
Example owner/operator prompts are in [docs/operator-prompts.md](docs/operator-prompts.md).
First paid-install deliverable shape: [docs/first-report.md](docs/first-report.md).

## What It Should Answer

- Which estimates need follow-up?
- Which invoices are overdue?
- Which jobs are unscheduled, stale, or blocked?
- Which customers have not had activity recently?
- What work needs attention this week?
- Where is operational follow-up leaking revenue?

More buyer-facing examples are in [docs/use-cases.md](docs/use-cases.md).

A fictional sample output is available in [docs/demo-output.md](docs/demo-output.md), or run:

```bash
npm run demo
```

The paid pilot handoff format is documented in [docs/pilot-deliverable-template.md](docs/pilot-deliverable-template.md).

## Product Posture

- Customer-hosted first.
- Read-only first.
- No credential custody required for the public repo.
- No autonomous writes in customer systems.
- No scraping private data.
- No fake claims, fake testimonials, or deceptive outreach.

## Launch Offer

Early-access pricing is documented in [docs/offer.md](docs/offer.md).

For pilot setup, email `opsconduit@gmail.com` with the subject `Jobber pilot`. Do not send Jobber passwords, tokens, API secrets, or private customer data by email.

## Install

Requires Node.js 20+.

```bash
mkdir opsconduit-jobber
cd opsconduit-jobber
npm install @opsconduit/jobber-mcp
cp node_modules/@opsconduit/jobber-mcp/.env.example .env
npx opsconduit-jobber-auth
npx opsconduit-jobber-mcp
```

Fill `JOBBER_CLIENT_ID` and `JOBBER_CLIENT_SECRET` in `.env` before running the auth helper. The helper prints a Jobber OAuth URL, receives the local callback at `http://localhost:3333/oauth/callback`, and stores tokens in `.opsconduit/jobber-tokens.json`.

Detailed setup notes are in [docs/install.md](docs/install.md). Paid pilot validation steps are in [docs/pilot-checklist.md](docs/pilot-checklist.md).
Implementation notes for Jobber's GraphQL API are in [docs/jobber-api-notes.md](docs/jobber-api-notes.md).

## MCP Tools

- `jobber_auth_url` - create the one-time Jobber OAuth authorization link for a customer-hosted install.
- `jobber_exchange_code` - exchange the redirected OAuth code and store tokens locally without exposing them in chat.
- `jobber_refresh_token` - refresh the stored access token for continued read-only reporting.
- `jobber_account` - validate the connected account before running operational queries.
- `jobber_clients_sample` - validate read access with a capped client sample.
- `jobber_graphql_read` - run read-only Jobber GraphQL for owner reports; mutations are blocked before sending.

## Policies

- [Terms of Service](docs/terms.md)
- [Privacy Policy](docs/privacy.md)

## Status

This repository is in early implementation. The first usable target is a customer-hosted MCP server with local OAuth setup and read-only Jobber GraphQL access.
