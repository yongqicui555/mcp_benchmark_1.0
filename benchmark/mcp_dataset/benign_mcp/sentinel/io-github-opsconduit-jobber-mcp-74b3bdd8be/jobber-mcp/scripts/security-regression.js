import { spawn } from "node:child_process";
import { once } from "node:events";
import { mkdtemp, rm } from "node:fs/promises";
import { join } from "node:path";
import { tmpdir } from "node:os";
import assert from "node:assert/strict";

const tempRoot = await mkdtemp(join(tmpdir(), "opsconduit-security-"));
const realFetch = globalThis.fetch;

try {
  process.env.JOBBER_CLIENT_ID = "test-client";
  process.env.JOBBER_CLIENT_SECRET = "test-secret";
  process.env.JOBBER_ACCESS_TOKEN = "expired-access";
  process.env.JOBBER_REFRESH_TOKEN = "refresh-token";
  process.env.JOBBER_TOKEN_STORE = join(tempRoot, "tokens.json");
  process.env.JOBBER_REQUEST_TIMEOUT_MS = "50";

  const { jobberGraphql } = await import("../src/jobber.js");

  await assert.rejects(
    () => jobberGraphql({ query: "mutation Bad { doThing }" }),
    /Mutation blocked/
  );

  globalThis.fetch = (url, options = {}) => new Promise((resolve, reject) => {
    options.signal?.addEventListener("abort", () => {
      const error = new Error(`aborted ${url}`);
      error.name = "AbortError";
      reject(error);
    });
  });
  await assert.rejects(
    () => jobberGraphql({ query: "query TimeoutCheck { account { id } }" }),
    /timed out after 50ms/
  );

  const calls = [];
  globalThis.fetch = async url => {
    calls.push(String(url));
    if (String(url).includes("/oauth/token")) {
      return Response.json({
        access_token: "refreshed-access",
        refresh_token: "new-refresh-token"
      });
    }
    return Response.json({ errors: [{ message: "unauthorized" }] }, { status: 401 });
  };

  await assert.rejects(
    () => jobberGraphql({ query: "query RetryCheck { account { id } }" }),
    /after refreshing access token/
  );

  assert.equal(calls.filter(url => url.includes("/api/graphql")).length, 2);
  assert.equal(calls.filter(url => url.includes("/oauth/token")).length, 1);

  await assertOAuthStateMismatch();
  console.log("Security regression checks ok");
} finally {
  await rm(tempRoot, { recursive: true, force: true });
}

async function assertOAuthStateMismatch() {
  const port = 3900 + Math.floor(Math.random() * 500);
  const child = spawn(process.execPath, ["src/oauth-local.js"], {
    env: {
      ...process.env,
      JOBBER_CLIENT_ID: "test-client",
      JOBBER_CLIENT_SECRET: "test-secret",
      JOBBER_REDIRECT_URI: `http://localhost:${port}/oauth/callback`,
      JOBBER_TOKEN_STORE: join(tempRoot, "oauth-tokens.json")
    },
    stdio: ["ignore", "pipe", "pipe"]
  });

  try {
    await waitForOutput(child, "OAuth helper listening", 5000);
    const res = await realFetch(`http://127.0.0.1:${port}/oauth/callback?code=test-code&state=wrong-state`);
    const text = await res.text();
    assert.equal(res.status, 400);
    assert.match(text, /OAuth state mismatch/);
  } finally {
    child.kill();
    await once(child, "exit").catch(() => {});
  }
}

function waitForOutput(child, expected, timeoutMs) {
  return new Promise((resolve, reject) => {
    let output = "";
    const timeout = setTimeout(() => {
      cleanup();
      reject(new Error(`Timed out waiting for child output: ${expected}\n${output}`));
    }, timeoutMs);

    const onData = chunk => {
      output += chunk.toString();
      if (output.includes(expected)) {
        cleanup();
        resolve();
      }
    };

    const onExit = code => {
      cleanup();
      reject(new Error(`Child exited before expected output (${code}): ${output}`));
    };

    const cleanup = () => {
      clearTimeout(timeout);
      child.stdout.off("data", onData);
      child.stderr.off("data", onData);
      child.off("exit", onExit);
    };

    child.stdout.on("data", onData);
    child.stderr.on("data", onData);
    child.on("exit", onExit);
  });
}
