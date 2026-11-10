import { chmod, mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname } from "node:path";
import { randomBytes } from "node:crypto";
import { config, requireAppCredentials } from "./config.js";

const AUTH_URL = "https://api.getjobber.com/api/oauth/authorize";
const TOKEN_URL = "https://api.getjobber.com/api/oauth/token";
const GRAPHQL_URL = "https://api.getjobber.com/api/graphql";

export function buildAuthorizationUrl({ redirectUri = config.redirectUri, state = randomBytes(18).toString("hex") } = {}) {
  requireAppCredentials();
  const url = new URL(AUTH_URL);
  url.searchParams.set("response_type", "code");
  url.searchParams.set("client_id", config.clientId);
  url.searchParams.set("redirect_uri", redirectUri);
  url.searchParams.set("state", state);
  return { url: url.toString(), state, redirectUri };
}

export async function exchangeAuthorizationCode({ code, redirectUri = config.redirectUri }) {
  requireAppCredentials();
  if (!code) throw new Error("code is required");

  const body = new URLSearchParams({
    client_id: config.clientId,
    client_secret: config.clientSecret,
    grant_type: "authorization_code",
    code,
    redirect_uri: redirectUri
  });

  const tokens = await tokenRequest(body);
  await saveTokens(tokens);
  return redactTokens(tokens);
}

export async function refreshAccessToken() {
  return redactTokens(await refreshStoredAccessToken());
}

async function refreshStoredAccessToken() {
  requireAppCredentials();
  const current = await readTokens();
  if (!current.refresh_token) {
    throw new Error("No refresh_token found. Run the OAuth helper first.");
  }

  const body = new URLSearchParams({
    client_id: config.clientId,
    client_secret: config.clientSecret,
    grant_type: "refresh_token",
    refresh_token: current.refresh_token
  });

  const refreshed = await tokenRequest(body);
  const merged = { ...current, ...refreshed, captured_at: new Date().toISOString() };
  await saveTokens(merged);
  return merged;
}

export async function jobberGraphql({ query, variables = {}, accessTokenOverride = "", retriedAfterRefresh = false }) {
  if (!query || typeof query !== "string") throw new Error("query is required");
  assertReadOnlyQuery(query);

  const accessToken = accessTokenOverride || await getUsableAccessToken();
  const res = await fetchWithTimeout(GRAPHQL_URL, {
    method: "POST",
    headers: {
      "authorization": `Bearer ${accessToken}`,
      "content-type": "application/json",
      "x-jobber-graphql-version": config.apiVersion
    },
    body: JSON.stringify({ query, variables })
  });

  const text = await res.text();
  let data;
  try {
    data = text ? JSON.parse(text) : {};
  } catch {
    throw new Error(`Jobber returned non-JSON response (${res.status}): ${text.slice(0, 500)}`);
  }

  if (res.status === 401) {
    if (retriedAfterRefresh) {
      throw new Error("Jobber GraphQL request failed (401) after refreshing access token.");
    }
    const refreshed = await refreshStoredAccessToken();
    return jobberGraphql({ query, variables, accessTokenOverride: refreshed.access_token, retriedAfterRefresh: true });
  }

  if (!res.ok) {
    throw new Error(`Jobber GraphQL request failed (${res.status}): ${JSON.stringify(data).slice(0, 1000)}`);
  }

  return data;
}

export async function getAccount() {
  return jobberGraphql({
    query: `query OpsConduitAccount {
  account {
    id
    name
  }
}`
  });
}

export async function getClientSample({ first = 10 } = {}) {
  return jobberGraphql({
    query: `query OpsConduitClientSample($first: Int!) {
  clients(first: $first) {
    totalCount
    nodes {
      id
      firstName
      lastName
      companyName
      billingAddress {
        city
      }
    }
  }
}`,
    variables: { first }
  });
}

function assertReadOnlyQuery(query) {
  if (config.allowMutations) return;
  const compact = query.replace(/#[^\n\r]*/g, " ").trim().toLowerCase();
  if (compact.startsWith("mutation") || /\bmutation\b/.test(compact)) {
    throw new Error("Mutation blocked. This connector is read-only by default.");
  }
}

async function getUsableAccessToken() {
  const tokens = await readTokens();
  if (!tokens.access_token) throw new Error("No access_token found. Run the OAuth helper first.");
  if (isJwtExpiring(tokens.access_token)) {
    const refreshed = await refreshStoredAccessToken();
    return refreshed.access_token;
  }
  return tokens.access_token;
}

async function tokenRequest(body) {
  const res = await fetchWithTimeout(TOKEN_URL, {
    method: "POST",
    headers: { "content-type": "application/x-www-form-urlencoded" },
    body
  }, "Jobber token request");
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(`Jobber token request failed (${res.status}): ${JSON.stringify(data).slice(0, 1000)}`);
  }
  return { ...data, captured_at: new Date().toISOString() };
}

async function readTokens() {
  if (process.env.JOBBER_ACCESS_TOKEN) {
    return {
      access_token: process.env.JOBBER_ACCESS_TOKEN,
      refresh_token: process.env.JOBBER_REFRESH_TOKEN || ""
    };
  }

  try {
    return JSON.parse(await readFile(config.tokenStorePath, "utf8"));
  } catch (error) {
    if (error.code === "ENOENT") return {};
    throw error;
  }
}

async function saveTokens(tokens) {
  await mkdir(dirname(config.tokenStorePath), { recursive: true });
  await writeFile(config.tokenStorePath, `${JSON.stringify(tokens, null, 2)}\n`, { mode: 0o600 });
  await chmod(config.tokenStorePath, 0o600).catch(() => {});
}

function redactTokens(tokens) {
  return {
    accessToken: tokens.access_token ? `${tokens.access_token.slice(0, 12)}...` : "",
    refreshToken: tokens.refresh_token ? `${tokens.refresh_token.slice(0, 8)}...` : "",
    capturedAt: tokens.captured_at || ""
  };
}

function isJwtExpiring(token) {
  const payload = token.split(".")[1];
  if (!payload) return false;
  try {
    const decoded = JSON.parse(Buffer.from(payload, "base64url").toString("utf8"));
    if (!decoded.exp) return false;
    return decoded.exp * 1000 < Date.now() + 120000;
  } catch {
    return false;
  }
}

async function fetchWithTimeout(url, options, label = "Jobber request") {
  const timeoutMs = Number.isFinite(config.requestTimeoutMs) && config.requestTimeoutMs > 0
    ? config.requestTimeoutMs
    : 30000;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(url, { ...options, signal: controller.signal });
  } catch (error) {
    if (error.name === "AbortError") {
      throw new Error(`${label} timed out after ${timeoutMs}ms.`);
    }
    throw error;
  } finally {
    clearTimeout(timer);
  }
}
