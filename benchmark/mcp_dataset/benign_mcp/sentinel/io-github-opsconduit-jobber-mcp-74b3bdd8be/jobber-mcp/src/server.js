#!/usr/bin/env node
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import {
  buildAuthorizationUrl,
  exchangeAuthorizationCode,
  getAccount,
  getClientSample,
  jobberGraphql,
  refreshAccessToken
} from "./jobber.js";

const server = new McpServer({
  name: "opsconduit-jobber-mcp",
  version: "0.1.3"
});

server.registerTool(
  "jobber_auth_url",
  {
    title: "Build Jobber OAuth URL",
    description: "Create the one-time Jobber OAuth authorization link for a customer-hosted install. Use this during setup when the Jobber admin is ready to approve read-only access; the tool returns the URL plus the state value that should be checked after redirect.",
    inputSchema: {
      redirectUri: z.string().url().describe("OAuth callback URL configured in the Jobber developer app, for example http://localhost:3333/oauth/callback.").optional(),
      state: z.string().min(8).describe("Opaque CSRF/state token to verify when Jobber redirects back. If omitted, OpsConduit generates one.").optional()
    }
  },
  async ({ redirectUri, state }) => textResult(buildAuthorizationUrl({ redirectUri, state }))
);

server.registerTool(
  "jobber_exchange_code",
  {
    title: "Exchange Jobber OAuth Code",
    description: "Complete the Jobber OAuth setup by exchanging the redirected authorization code for local tokens. Use only with a code copied from the customer's own redirect URL; tokens are stored on the local machine and are not returned in chat.",
    inputSchema: {
      code: z.string().min(8).describe("Temporary authorization code from Jobber's OAuth redirect after the admin approves access."),
      redirectUri: z.string().url().describe("Same callback URL used in jobber_auth_url and registered with the Jobber app.").optional()
    }
  },
  async ({ code, redirectUri }) => textResult(await exchangeAuthorizationCode({ code, redirectUri }))
);

server.registerTool(
  "jobber_refresh_token",
  {
    title: "Refresh Jobber Token",
    description: "Refresh the locally stored Jobber access token when a read-only query needs a current token. This uses the customer's local refresh token and does not expose token values in the MCP response.",
    inputSchema: {}
  },
  async () => textResult(await refreshAccessToken())
);

server.registerTool(
  "jobber_account",
  {
    title: "Get Jobber Account",
    description: "Validate the Jobber connection by returning the connected account id and display name. Use after OAuth setup to confirm the install points at the expected customer account before running operational read queries.",
    inputSchema: {}
  },
  async () => textResult(await getAccount())
);

server.registerTool(
  "jobber_clients_sample",
  {
    title: "Sample Jobber Clients",
    description: "Read a small sample of Jobber clients to confirm GraphQL read access and pagination behavior. This is an install-validation check, not an export workflow.",
    inputSchema: {
      first: z.number().int().min(1).max(25).default(10).describe("Number of client records to sample for validation, capped at 25.")
    }
  },
  async ({ first }) => textResult(await getClientSample({ first }))
);

server.registerTool(
  "jobber_graphql_read",
  {
    title: "Run Read-Only Jobber GraphQL",
    description: "Run a read-only Jobber GraphQL query for operations reporting, such as overdue invoices, stale requests, unscheduled jobs, or estimate follow-up. Mutation operations are blocked before the request is sent.",
    inputSchema: {
      query: z.string().min(10).describe("Read-only GraphQL query text. Queries containing mutation operations are rejected."),
      variables: z.record(z.string(), z.unknown()).describe("Optional GraphQL variables object for the read-only query.").optional()
    }
  },
  async ({ query, variables }) => textResult(await jobberGraphql({ query, variables: variables || {} }))
);

await server.connect(new StdioServerTransport());

function textResult(value) {
  return {
    content: [
      {
        type: "text",
        text: typeof value === "string" ? value : JSON.stringify(value, null, 2)
      }
    ]
  };
}
