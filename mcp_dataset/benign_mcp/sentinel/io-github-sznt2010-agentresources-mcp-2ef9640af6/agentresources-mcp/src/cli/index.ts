import { runDoctor } from "./doctor.js";
import { runSkills } from "./skills.js";
import { runMcp } from "./mcp.js";

const HELP = `ar — Agent Resources CLI

Usage:
  ar doctor [--fix] [--offline] [--quick] [--json]
  ar skills get <slug> [--dir <path>]
  ar skill add <slug>  [--dir <path>]   (alias of \`ar skills get\`)
  ar mcp                                (start the operational MCP server on stdio)
  ar version
  ar help

Environment:
  AR_API_URL          Gateway base URL (default: https://api.agentresources.xyz)
  AR_SESSION_TOKEN    Bearer token for authed routes (use \`walletLogin\` from @agentresources/sdk)

Documentation: https://agentresources.xyz/docs
`;

const VERSION = "0.1.0";

export async function runCli(argv: ReadonlyArray<string>): Promise<void> {
  const [cmd, sub, ...rest] = argv;

  if (!cmd || cmd === "help" || cmd === "--help" || cmd === "-h") {
    process.stdout.write(HELP);
    return;
  }

  if (cmd === "version" || cmd === "--version" || cmd === "-v") {
    process.stdout.write(`ar v${VERSION}\n`);
    return;
  }

  if (cmd === "doctor") {
    const flags = parseFlags([sub, ...rest]);
    const exitCode = await runDoctor({
      apiUrl: process.env["AR_API_URL"] ?? "https://api.agentresources.xyz",
      ...(process.env["AR_SESSION_TOKEN"] ? { token: process.env["AR_SESSION_TOKEN"] } : {}),
      fix: flags.has("--fix"),
      offline: flags.has("--offline"),
      quick: flags.has("--quick"),
      json: flags.has("--json"),
    });
    process.exit(exitCode);
  }

  if (cmd === "skills" || cmd === "skill") {
    const action = sub;
    const slug = rest[0];
    if ((action === "get" || action === "add") && slug && !slug.startsWith("--")) {
      const dirIdx = rest.indexOf("--dir");
      const dir = dirIdx >= 0 ? rest[dirIdx + 1] : undefined;
      const exit = await runSkills({
        action: "get",
        slug,
        ...(dir ? { dir } : {}),
        registryUrl: process.env["AR_SKILLS_URL"] ?? "https://agentresources.xyz/skills",
      });
      process.exit(exit);
    }
    process.stderr.write(`Unknown skills subcommand. Try: ar skills get <slug>\n`);
    process.exit(2);
  }

  if (cmd === "mcp") {
    await runMcp();
    return;
  }

  process.stderr.write(`Unknown command: ${cmd}\n\n${HELP}`);
  process.exit(2);
}

function parseFlags(parts: ReadonlyArray<string | undefined>): Set<string> {
  const flags = new Set<string>();
  for (const p of parts) {
    if (p && p.startsWith("--")) flags.add(p);
  }
  return flags;
}
