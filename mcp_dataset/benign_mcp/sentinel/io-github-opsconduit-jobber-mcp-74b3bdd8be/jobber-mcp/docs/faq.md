# FAQ

## Is this an official Jobber product?

No. OpsConduit is an independent customer-hosted connector for customers who want to connect their own Jobber account to an MCP-compatible AI client.

## Does it change my Jobber data?

Not by default. The public connector is read-only by default and blocks GraphQL mutations unless local config explicitly allows them.

## Where do tokens and credentials go?

OAuth tokens are stored in the customer's local install path, not in this public repo. Do not send Jobber passwords, API secrets, tokens, exports, or private customer data by email or GitHub issue.

## What is the first useful output?

The first useful output is a short owner action list, such as stale sent estimates, overdue invoices, unscheduled jobs, and active work with no upcoming visit.

## What does the paid pilot include?

The pilot setup is for installing the connector, authorizing Jobber, validating read-only access, running one customer-approved read-only data check, and handing off a short usage guide.

## Can OpsConduit build write automation?

Not in the standard Jobber pilot. Write actions require a separate explicit scope, separate risk review, and clear customer approval.

## How do I start?

Email `opsconduit@gmail.com` with the subject `Jobber pilot`.

Do not include private Jobber credentials or customer data in the first email.
