import "dotenv/config";
import { resolve } from "node:path";

export const config = {
  clientId: process.env.JOBBER_CLIENT_ID || "",
  clientSecret: process.env.JOBBER_CLIENT_SECRET || "",
  redirectUri: process.env.JOBBER_REDIRECT_URI || "http://localhost:3333/oauth/callback",
  apiVersion: process.env.JOBBER_API_VERSION || "2025-04-16",
  requestTimeoutMs: Number(process.env.JOBBER_REQUEST_TIMEOUT_MS || 30000),
  tokenStorePath: resolve(process.env.JOBBER_TOKEN_STORE || ".opsconduit/jobber-tokens.json"),
  allowMutations: process.env.OPSCONDUIT_ALLOW_MUTATIONS === "true",
  supportEmail: process.env.OPSCONDUIT_SUPPORT_EMAIL || "opsconduit@gmail.com"
};

export function requireAppCredentials() {
  const missing = [];
  if (!config.clientId) missing.push("JOBBER_CLIENT_ID");
  if (!config.clientSecret) missing.push("JOBBER_CLIENT_SECRET");

  if (missing.length) {
    throw new Error(`Missing required environment variable(s): ${missing.join(", ")}`);
  }
}
