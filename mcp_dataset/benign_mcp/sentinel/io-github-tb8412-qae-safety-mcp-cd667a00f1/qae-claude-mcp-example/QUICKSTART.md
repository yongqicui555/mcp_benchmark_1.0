# Quick Start Guide — 5 Minutes to Safety Certification

## Objective
Get the QAE Safety Certification MCP server running in Claude in under 5 minutes.

## Prerequisites
- Python 3.9+
- Claude Desktop installed
- Internet connection (to install packages)

## Step-by-Step

### 1. Download the Example (1 min)

Clone or download this repository to a local directory:
```bash
git clone https://github.com/tb8412/qae-claude-mcp-example.git
cd qae-claude-mcp-example
```

Or download as ZIP and extract.

### 2. Install the Package (1 min)

```bash
pip install -e .
```

This installs the MCP server and its dependencies:
- `qae-safety` — The QAE safety kernel (PyPI package)
- `mcp` — Model Context Protocol SDK

### 3. Configure Claude Desktop (2 min)

1. **Find your config file:**
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
   - **Linux**: `~/.config/Claude/claude_desktop_config.json`

2. **Open it in a text editor and add the server:**

   ```json
   {
     "mcpServers": {
       "qae-safety": {
         "command": "python",
         "args": ["-m", "qae_mcp_server"],
         "env": {}
       }
     }
   }
   ```

   If you already have other servers configured, just add the `"qae-safety"` block to the `mcpServers` object.

3. **Replace path if needed:**
   If the directory is not in your Python path, use the full path:
   ```json
   "args": ["-m", "qae_mcp_server", "--path", "/full/path/to/repo"]
   ```

### 4. Restart Claude Desktop

Close and reopen Claude Desktop. The MCP server will start automatically.

### 5. Test It! (1 min)

In Claude, try this:

**User message:**
```
I'm thinking about deploying a new feature to 20% of users. The feature has a UI change (easy to reverse) but will affect a moderate number of users.

Can you evaluate the safety of this action?
- Scope: 0.2 (20% of users)
- Reversibility: 0.8 (feature flag toggle)
- Sensitivity: 0.3 (UI cosmetic change)
```

**Claude will respond with something like:**
```
Let me evaluate the safety of this deployment using QAE certification.

[Claude invokes certify_action tool]

Result: CERTIFIED (Safe zone)

All margins are strong:
- Scope margin: 0.80 (20% is manageable)
- Reversibility margin: 0.80 (feature flag is quick to toggle)
- Sensitivity margin: 0.70 (cosmetic change is low-risk)

Recommendation: PROCEED with the rollout. Monitor metrics for 24 hours, then
consider expanding to more users if telemetry looks good.
```

## Done!

You now have QAE safety certification integrated into Claude. Use the tools to evaluate the safety of any autonomous action.

## Common First Actions

### Check Available Tools

In Claude, ask:
```
What tools do I have available?
```

Claude will list:
- `certify_action` — Evaluate action safety
- `check_budget` — View safety budget status
- `get_certification_history` — See past certifications

### Try a Different Action

Propose any action with the three dimensions:

**Example: Risky schema change**
```
I need to add a column to the production database. This affects all users and
is difficult to reverse. Is this safe?
- Scope: 1.0 (all users)
- Reversibility: 0.2 (difficult, requires migration rollback)
- Sensitivity: 0.7 (could block user access if wrong)
```

Claude will evaluate and show the result.

## Troubleshooting

### "Tool not found" error
1. Did you restart Claude Desktop? (Required after config change)
2. Check `claude_desktop_config.json` syntax (use JSON validator)
3. Verify path is correct (try absolute path)

### "qae-safety not installed" error
```bash
pip install qae-safety --upgrade
```

### Server won't start
Check logs by running manually:
```bash
python -m qae_mcp_server
```

Look for error messages. Common issues:
- Missing Python dependencies (run `pip install -e .`)
- Python version < 3.8 (check with `python --version`)

### Slow certification
First call takes ~100ms (initialization). Subsequent calls are faster (~5-20ms).

## Next Steps

### Read the Documentation
- **README.md** — Full overview and API reference
- **INTEGRATION.md** — How to interpret certificates and integrate into decisions
- **EXAMPLES.md** — Real-world scenarios with detailed walkthroughs
- **DEVELOPMENT.md** — Extend the server or customize the adapter

### Try More Complex Scenarios
See `EXAMPLES.md` for:
- Feature rollouts
- Database migrations
- Pricing changes
- Data export decisions
- Batch jobs

### Integrate with Your Workflow
Use QAE certification whenever Claude suggests an action:
- Code changes
- Configuration updates
- User-facing deployments
- Data operations
- Revenue/pricing decisions

### Configure for Your Needs
Edit `src/qae_mcp_server/server.py` to customize:
- Budget limits (currently 100/day)
- Rate limits (currently 50/hour)
- Decision thresholds (Safe > 0.6, Caution 0.3-0.6, etc.)

## Support

For issues or questions:
1. Check the documentation files (README, INTEGRATION, EXAMPLES)
2. Review the unit tests in `tests/test_server.py` for usage patterns
3. Consult the QAE research paper: https://doi.org/10.6084/m9.figshare.31742857
4. Visit https://qaesubstrate.com for more information

## Key Concepts

| Term | Meaning |
|------|---------|
| **Certified** | Safe to proceed immediately |
| **CertifiedWithWarning** | Proceed with caution and monitoring |
| **EscalateToHuman** | Human review needed before proceeding |
| **Blocked** | Do not proceed; too risky |
| **Scope** | How many users/systems affected [0=narrow, 1=global] |
| **Reversibility** | How easily can you undo this [0=permanent, 1=trivial] |
| **Sensitivity** | How much user/revenue impact [0=none, 1=critical] |
| **Margin** | Safety headroom in [0, 1] where 0=at risk boundary |
| **Binding Constraint** | Which dimension is most restrictive |

## Certificate Zones

| Zone | Color | Decision | Margin | Action |
|------|-------|----------|--------|--------|
| Safe | 🟢 | Certified | > 0.6 | Proceed immediately |
| Caution | 🟡 | CertifiedWithWarning | 0.3-0.6 | Proceed with safeguards |
| Danger | 🔴 | EscalateToHuman | 0.1-0.3 | Get human approval |
| Danger | 🔴 | Blocked | ≤ 0.1 | Reject, no proceed |

---

**Congratulations!** You're now ready to use QAE safety certification with Claude. Start with simple actions and work up to complex scenarios.
