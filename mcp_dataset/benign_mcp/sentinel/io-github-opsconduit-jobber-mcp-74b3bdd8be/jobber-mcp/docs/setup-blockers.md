# Setup Blockers

## Already Set Up

- OpsConduit GitHub account exists.
- Public repository exists: `opsconduit/jobber-mcp`.
- OpsConduit Gmail exists.
- Jobber Developer Center signup is reportedly complete.

## Still Needed

- Valid mailing address for outbound email footer.
- Coinbase Commerce payment links:
  - $149 Async Install Help
  - $399 Pilot Setup
  - $79 Monthly Maintenance
- A safe way to send and receive OpsConduit Gmail without exposing credentials in docs or git.
- At least one real Jobber OAuth authorization against the test account to validate live GraphQL queries.

## Security Note

The public repository must never store:

- Gmail passwords
- GitHub tokens
- Jobber client secrets
- customer access tokens
- prospect lists
- customer emails
- payment records
