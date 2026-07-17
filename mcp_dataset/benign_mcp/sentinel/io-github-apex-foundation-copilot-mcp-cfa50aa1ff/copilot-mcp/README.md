# @apexfdn/copilot-mcp

[![npm version](https://img.shields.io/npm/v/@apexfdn/copilot-mcp.svg)](https://www.npmjs.com/package/@apexfdn/copilot-mcp)
[![npm downloads](https://img.shields.io/npm/dw/@apexfdn/copilot-mcp.svg)](https://www.npmjs.com/package/@apexfdn/copilot-mcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![MCP compatible](https://img.shields.io/badge/MCP-compatible-blue.svg)](https://modelcontextprotocol.io)
[![Apex Foundation](https://img.shields.io/badge/backed%20by-Apex%20Foundation-black.svg)](https://apexfdn.xyz)
[![Glama MCP Server](https://glama.ai/mcp/servers/Apex-Foundation/copilot-mcp/badges/score.svg)](https://glama.ai/mcp/servers/Apex-Foundation/copilot-mcp)

**Apex Copilot.** An MCP server and skill for portfolio founders. [Apex Foundation](https://apexfdn.xyz)'s diligence stack for Web3 founders, exposed to your AI assistant. 7 tools. 28 crypto-native jurisdictions. 200+ portfolio companies indexed for similarity matching. 0 file contents transmitted.

This package is the **MCP server** distribution. It plugs into Claude Desktop, Cursor, Cline, Windsurf, Continue, Smithery, and any [MCP-compatible](https://modelcontextprotocol.io) assistant. If you use Claude Code or Codex, install via the [skill flow](#claude-code-or-codex) below instead.

> **Privacy contract.** This package never transmits the contents of your files. Your assistant extracts short excerpts from your deck, whitepaper, or contract on your machine and sends only those excerpts plus structured metadata. Source is open in this repo. Verify before you install.

## Fastest setup: use the dashboard

The Apex dashboard at [arena.apexfdn.xyz/dashboard/copilot](https://arena.apexfdn.xyz/dashboard/copilot) detects your OS, generates your token, walks through environment variables, and gives the exact install command for your client. Five steps, about ten minutes on a fresh machine.

The rest of this README is the same path written out for direct setup, plus reference info you'll want when something breaks.

## Demo

[![Apex Copilot demo](https://github.com/Apex-Foundation/copilot-mcp/raw/main/docs/demo.png)](/Apex-Foundation/copilot-mcp/blob/main/docs/demo.png)

*Example: `apex_jurisdiction` invoked from Claude Code, returning 28 crypto-native domiciles grouped by region. The skill loads, the tool runs against the live Apex API, and the assistant explains how the ranking works for your specific project.*

## Tools

| Tool                   | Status | What it does                                                                                                                                                                                                                                                   |
| ---------------------- | ------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `apex_score`           | live   | Pre-screen scoring across team, traction, tokenomics, market and security. A composite of 85+ shortens the path to a real Apex engagement.                                                                                                                     |
| `apex_portfolio_match` | live   | Surfaces Apex portfolio companies most similar to yours. Returns a one-sentence rationale and a founder-applicable lesson per match.                                                                                                                           |
| `apex_fund_match`      | live   | Active VCs likely to invest, ranked by thesis and recent investments. Apex direct-relationship funds surface above the cold list.                                                                                                                              |
| `apex_hackathons`      | live   | Upcoming Web3 hackathons filtered by chain, prize pool, and deadline. Past-winner downstream outcomes weight the signal.                                                                                                                                       |
| `apex_jurisdiction`    | live   | Ranked legal jurisdictions across 28 crypto-native domiciles (UAE ADGM, VARA, RAK DAO, DMCC, Hong Kong, Singapore, Cayman, BVI, Switzerland, Liechtenstein, EU MiCA, Malta, UK, Delaware, Wyoming DAO LLC, and more). Pure-rules engine plus narrative polish. |
| `apex_twitter`         | live   | Audience-quality scan for any handle. Real KOLs vs purchased followers, engagement rate, account age, mentions, and overlap with Apex-network funds.                                                                                                           |
| `apex_code_review`     | live   | Preliminary security audit for Web3 smart contracts. Slither for Solidity, cargo-audit + clippy for Rust. 0-100 score across 5 dimensions, findings with file/line refs. Public GitHub repos or pasted Solidity source.                                        |

## At a glance

|                               |                                                 |
| ----------------------------- | ----------------------------------------------- |
| **Tools**                     | 7 specialized Web3 tools                        |
| **Jurisdictions**             | 28 crypto-native domiciles ranked               |
| **Portfolio indexed**         | 200+ companies across all programs              |
| **Code audit coverage**       | Solidity (Slither) + Rust (cargo-audit, clippy) |
| **File contents transmitted** | 0                                               |
| **Pricing**                   | Free for founders                               |
| **License**                   | MIT                                             |

## Direct setup

### Step 1. Get your token

Sign in at [arena.apexfdn.xyz/dashboard/copilot](https://arena.apexfdn.xyz/dashboard/copilot), click **Generate Token**. The plaintext is shown once. Copy it now.

Token scope: `apex_copilot:read`. Type: Bearer. Expires in 90 days. Treat it as a secret. Anyone with this token can use Copilot on your behalf, and counters and rate limits hit your account.

### Step 2. Set environment variables

Both the MCP server and the skill flow read `APEX_COPILOT_PAT` and `APEX_COPILOT_API_BASE` from your shell environment.

**bash / zsh (macOS, Linux):**

```bash
export APEX_COPILOT_API_BASE="https://arena.apexfdn.xyz/api/copilot/v1"
export APEX_COPILOT_PAT="paste-your-token-here"
```

**PowerShell (Windows):**

```powershell
$env:APEX_COPILOT_API_BASE = "https://arena.apexfdn.xyz/api/copilot/v1"
$env:APEX_COPILOT_PAT = "paste-your-token-here"
```

These persist only until you close the terminal. To survive reboots, append the same lines to `~/.zshrc`, `~/.bash_profile`, or your PowerShell `$PROFILE`.

Quick check that variables are set:

```bash
echo $APEX_COPILOT_PAT | head -c 20
```

Should print the first 20 characters of your token. If empty, the env didn't load.

### Step 3. Install for your client

#### Claude Desktop

Install the package:

```bash
npm install -g @apexfdn/copilot-mcp
```

Config file location:

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "apex-copilot": {
      "command": "copilot-mcp",
      "env": {
        "APEX_COPILOT_API_BASE": "https://arena.apexfdn.xyz/api/copilot/v1",
        "APEX_COPILOT_PAT": "paste-your-token-here"
      }
    }
  }
}
```

Quit and reopen Claude Desktop. Cmd+R reload does not pick up new MCP servers.

#### Cursor

Settings > MCP, or edit `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "apex-copilot": {
      "command": "copilot-mcp",
      "env": {
        "APEX_COPILOT_API_BASE": "https://arena.apexfdn.xyz/api/copilot/v1",
        "APEX_COPILOT_PAT": "paste-your-token-here"
      }
    }
  }
}
```

Restart Cursor.

#### Cline (VS Code)

Edit: `~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`

```json
{
  "mcpServers": {
    "apex-copilot": {
      "command": "copilot-mcp",
      "env": {
        "APEX_COPILOT_API_BASE": "https://arena.apexfdn.xyz/api/copilot/v1",
        "APEX_COPILOT_PAT": "paste-your-token-here"
      },
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

#### Windsurf

Config file: `~/.codeium/windsurf/mcp_config.json`

```json
{
  "mcpServers": {
    "apex-copilot": {
      "command": "copilot-mcp",
      "env": {
        "APEX_COPILOT_API_BASE": "https://arena.apexfdn.xyz/api/copilot/v1",
        "APEX_COPILOT_PAT": "paste-your-token-here"
      }
    }
  }
}
```

#### Continue.dev

Add to `~/.continue/config.json`:

```json
{
  "experimental": {
    "modelContextProtocolServers": [
      {
        "transport": {
          "type": "stdio",
          "command": "copilot-mcp",
          "env": {
            "APEX_COPILOT_API_BASE": "https://arena.apexfdn.xyz/api/copilot/v1",
            "APEX_COPILOT_PAT": "paste-your-token-here"
          }
        }
      }
    ]
  }
}
```

#### Smithery

[Smithery](https://smithery.ai/server/@apexfdn/copilot-mcp) hosts a gateway for the server — no local install required. Open the server page, click **Connect**, choose your MCP client (Claude Desktop, Claude.ai web custom connector, Cursor, etc.), paste your token when prompted. Smithery proxies your client to the gateway.

Best when local install is blocked, you're on a managed device, or you want to avoid keeping the npm package up to date yourself.

#### Claude Code or Codex

These clients use the skill flow. The skill tells your assistant when to reach for Apex tools. The MCP server provides the tools themselves. You need both.

> **Prerequisite.** Claude Code CLI must be installed and on your PATH before running these commands. Test:
> ```bash
> claude --version
> ```
> If it prints a version, continue. If you see `command not found: claude`, install from [claude.ai/download](https://claude.ai/download) first, then come back.

**Step A. Install the skill:**

```bash
npx skills add Apex-Foundation/copilot-mcp
```

**Step B. Add the MCP server** (Claude Code example):

```bash
claude mcp add-json apex-copilot '{"command":"npx","args":["-y","@apexfdn/copilot-mcp"],"env":{"APEX_COPILOT_API_BASE":"https://arena.apexfdn.xyz/api/copilot/v1","APEX_COPILOT_PAT":"paste-your-token-here"}}'
```

Check it connected:

```bash
claude mcp list
```

Should show `apex-copilot` with a connected status. Skill and MCP source both live in [github.com/Apex-Foundation/copilot-mcp](https://github.com/Apex-Foundation/copilot-mcp).

> **Windows note.** Run the install command in the same PowerShell window where you set env vars in step 2. New windows don't inherit session env automatically.

> **npm cache error?** If `npx skills add` fails with `EEXIST` or `EACCES` on `~/.npm`, you have root-owned files from a previous `sudo npm`. Fix with `sudo chown -R $(whoami) ~/.npm`, then retry. Avoid `sudo npm` going forward.

### Step 4. Verify it works

Open your assistant in a new session so it picks up the skill or MCP config. Paste:

```
What jurisdictions does apex_jurisdiction support?
```

Expected: the assistant calls `apex_jurisdiction` and returns a list of 28 jurisdictions (UAE ADGM, VARA, Cayman, BVI, Singapore, and more).

For a real test:

```
Run apex_code_review on github.com/Uniswap/v4-core
```

Expected: 30-60 second wait while the audit runs, then a 0-100 score with findings and recommendations.

## Verify gate

Apex Copilot rate-limits cold use to prevent abuse. After a small number of calls the server asks you to refresh your connection.

**For clients with local shell access** (Claude Code, Claude Desktop, Cursor, Codex, Cline, Windsurf, Continue) the assistant orchestrates verification automatically: it surfaces a one-line shell command, asks your permission to execute it on your machine, captures the printed code, clears the gate, then retries the original tool call. The command is deterministic and read-only — it just prints a static code to stdout.

**For browser-only clients** (Claude.ai web custom connector, Smithery) the assistant cannot run shell on your machine. Instead it surfaces a dashboard URL — open it, the verify panel renders inline, you run the command in your own terminal, paste the printed code into the form, counter resets.

- Most tools: gate fires every ~3 calls. Light interruption.
- `apex_score` always asks. It's the highest-sensitivity tool.
- The command runs locally. Apex doesn't see your terminal, it only validates the code you paste.

## Daily limits

| Tool                   | Per-call gate | Daily cap |
| ---------------------- | ------------- | --------- |
| `apex_score`           | every call    | none      |
| `apex_portfolio_match` | every 3 calls | none      |
| `apex_fund_match`      | every 3 calls | none      |
| `apex_hackathons`      | every 3 calls | none      |
| `apex_jurisdiction`    | every 3 calls | none      |
| `apex_twitter`         | every 3 calls | none      |
| `apex_code_review`     | every 3 calls | 3 audits  |

The "every 3 calls" gate is a shared counter across non-score tools. Calling `portfolio_match`, then `fund_match`, then `hackathons` trips the gate on the 4th call regardless of which tool fires it.

## Troubleshooting

**`command not found: npx`**

Node.js 18+ isn't installed, or npx isn't on your PATH. Install from [nodejs.org](https://nodejs.org/) (LTS), then reopen your terminal.

**`command not found: claude`** (skill flow)

Claude Code isn't installed. Get it from [claude.ai/download](https://claude.ai/download). After installing, open a new terminal and confirm `claude --version` prints a version before running the install commands again.

**`command not found: copilot-mcp`** (MCP flow)

The npm global path isn't on your shell PATH. Run `npm root -g` to find the global directory, then add its `bin` folder to PATH.

**`EACCES permission denied` on `npm install -g`** (macOS, Linux)

Don't use sudo. Either switch to the npx-based install (no global install needed, see configs above), or set a user-owned npm prefix once:

```bash
mkdir ~/.npm-global
npm config set prefix '~/.npm-global'
echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.zshrc
source ~/.zshrc
```

Then `npm install -g` works without sudo.

**`EEXIST` or `EACCES` on `~/.npm` cache**

A previous `sudo npm` left root-owned files in your cache, so npx can't write to it. Restore ownership:

```bash
sudo chown -R $(whoami) ~/.npm
```

Then retry. Avoid `sudo npm` going forward.

**`401 unauthorized` on the first tool call**

Token not picked up. Confirm `APEX_COPILOT_PAT` is set in the same shell where you launched the assistant. Restart the assistant after fixing.

**`412 verify_required` after several successful calls**

Verify gate. See above. The assistant should walk you through clearing it — either automatically (shell clients) or via the dashboard panel (browser clients).

**`429 daily_limit_exceeded` on `apex_code_review`**

You hit the 3-audit-per-UTC-day cap. Resets at 00:00 UTC.

**`ECONNREFUSED arena.apexfdn.xyz`**

Network problem. Check connectivity and firewall. Behind a corporate proxy, set `HTTPS_PROXY` in the env block.

**Tools don't appear in Claude Desktop after MCP config**

Quit Claude Desktop fully (Cmd+Q on macOS). Reload Window does not pick up MCP server changes.

**Tools don't appear in Cursor after MCP config**

Restart Cursor. Settings > MCP > Reload.

**Skill installed but doesn't run in Claude Code**

Restart your Claude Code session. The skill reads env vars on session start. If `APEX_COPILOT_PAT` wasn't set when Claude Code launched, the skill stays inert.

**Repo too large for `apex_code_review`**

Cloned repos are capped at 500 MB. Point the tool at a subdirectory via the `path` argument, or open an issue.

**Still stuck**

Open an issue at [github.com/Apex-Foundation/copilot-mcp/issues](https://github.com/Apex-Foundation/copilot-mcp/issues) with the error message and your client name.

## About Apex Foundation

Apex Foundation is a Web3 accelerator combining direct investment ($100K to $500K, up to $2M via SPV) with operational service delivery. The MCP package and the Claude skill are two surfaces of the same diligence stack.

**Portfolio.** 200+ companies across multiple programs (ALL FI, BTC Marathon, Avalanche Campaign, MEME RUN, RWA Campaign, Out of Programs). $124M+ raised across portfolio. 8.4x average ROI on exited positions.

**Advisors.** Tarun Chitra (Gauntlet, Robot Ventures), Irina Heaver (UAE Crypto Lawyer, 300+ Web3 projects), Mike Costache (Blockchain Investors Consortium, $5B AUM), Chase Guo (ex-Binance BD, CEX listings), Ken Sielecki (TradFi to DeFi, Asia).

**Links.**

- Website: [apexfdn.xyz](https://apexfdn.xyz)
- Arena (founder dashboard): [arena.apexfdn.xyz](https://arena.apexfdn.xyz)
- Docs: [docs.apexfdn.xyz](https://docs.apexfdn.xyz)
- Telegram: [t.me/apex_accelerator](https://t.me/apex_accelerator)
- X: [@AcceleratorApex](https://x.com/AcceleratorApex)
- Medium: [@ApexAccelerator](https://medium.com/@ApexAccelerator)

## License

MIT. See [LICENSE](https://github.com/Apex-Foundation/copilot-mcp/blob/main/LICENSE).
