# Pilot Checklist

Use this checklist for a paid pilot setup.

## Before Setup

- Confirm the customer wants a customer-hosted install.
- Confirm they have access to authorize Jobber apps.
- Confirm the first use case is read-only reporting or follow-up visibility.
- Confirm they understand OpsConduit does not write to Jobber by default.

## Setup Tasks

- Clone the repo.
- Install dependencies with `npm install`.
- Create `.env`.
- Run `npm run auth`.
- Authorize Jobber.
- Start the MCP server with `npm start`.
- Add the MCP server to the customer's chosen MCP client.

## Validation Tasks

- Run `jobber_account`.
- Run `jobber_clients_sample`.
- Run one customer-approved read-only GraphQL query.
- Confirm no mutation/write tools are enabled.

## Suggested First Questions

- Which estimates need follow-up?
- Which invoices appear overdue?
- Which jobs are unscheduled or stale?
- Which requests have not moved forward?
- What needs owner attention this week?

## Pilot Deliverable

At the end of the pilot, send the customer:

- install location
- token storage location
- MCP client config used
- validation results
- recommended next three owner/operator questions
- maintenance option if they want compatibility checks

Use [pilot-deliverable-template.md](pilot-deliverable-template.md) as the handoff format.
