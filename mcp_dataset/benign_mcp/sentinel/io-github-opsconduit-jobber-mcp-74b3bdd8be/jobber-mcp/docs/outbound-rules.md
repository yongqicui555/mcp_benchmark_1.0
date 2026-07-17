# Outbound Rules

OpsConduit can use targeted B2B email, but it must stay low-volume, accurate, and easy to opt out of.

## Allowed

- Public business contact addresses such as `info@`, `hello@`, `office@`, or contact forms.
- Businesses with public evidence that they use Jobber or run field-service workflows where Jobber is plausible.
- Short emails that clearly identify OpsConduit and the reason for contact.
- One initial email and at most one follow-up unless the recipient replies.

## Not Allowed

- Fake identities.
- Fake customer claims.
- Fake urgency.
- Mass blasting.
- Purchased personal email lists.
- Scraping personal emails from social profiles.
- Contacting anyone who opted out.
- Security, bug bounty, vulnerability, exploit, or scanning language.

## Required Footer

Use a footer like this once a valid mailing address is available:

```text
--
OpsConduit
[VALID MAILING ADDRESS]
You received this because we found a public business contact for a field-service company that may use Jobber or similar operations software.
Reply "unsubscribe" and we will not contact you again.
```

The valid mailing address must be supplied before commercial outreach begins.

## First Email Draft

Subject: Read-only Jobber ops assistant

Hi,

I am building OpsConduit, a small read-only MCP connector for Jobber.

The goal is simple: let an owner or manager ask questions like "which estimates need follow-up?", "which invoices are overdue?", or "which jobs are unscheduled?" from an AI assistant without changing Jobber data.

It is customer-hosted and read-only by default. I am looking for a few early users to test the install path and operational reports.

Would you like the install notes or a short demo?

[FOOTER]

