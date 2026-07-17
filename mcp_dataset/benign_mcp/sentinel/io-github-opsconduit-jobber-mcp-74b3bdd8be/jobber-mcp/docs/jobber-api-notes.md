# Jobber API Notes

These notes explain the implementation posture for the read-only Jobber connector.

## Sources

- Jobber Developer Center: https://developer.getjobber.com/docs/
- Getting started and app scopes: https://developer.getjobber.com/docs/getting_started/
- API queries and mutations: https://developer.getjobber.com/docs/using_jobbers_api/api_queries_and_mutations/
- API versioning: https://developer.getjobber.com/docs/using_jobbers_api/api_versioning/

## Practical Notes

- Jobber's API is GraphQL-based.
- App scopes control what data an app can read or write.
- Jobber recommends using GraphiQL against a tester Jobber account to inspect the current schema.
- API requests should include the active `X-JOBBER-GRAPHQL-VERSION` header.
- Schema fields can change over time, so pilot queries should be validated against the customer's authorized account before treating them as a stable report.

## OpsConduit Defaults

- OAuth tokens stay in the customer-controlled local install.
- `jobber_graphql_read` blocks mutations unless local config explicitly allows them.
- The pilot starts with low-risk validation queries, then customer-approved read-only reporting queries.
- Customer data, tokens, and exports should not be posted to GitHub issues or sent by email.

## First Pilot Query Categories

The first paid pilot should validate which Jobber objects and fields are available for the account, then build one short action list from customer-approved read-only queries:

- stale sent estimates or quotes
- overdue invoices
- active jobs with no upcoming visit
- draft estimates or requests that have not moved forward
- recently updated clients or work objects for sanity checks
