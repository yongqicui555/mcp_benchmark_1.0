# Project Overview

## What Is This?

`qae-claude-mcp-example` is a **production-quality, fully working example** of an MCP (Model Context Protocol) server that exposes the **QAE safety certification kernel** as tools Claude can invoke.

**In plain English**: This lets Claude evaluate whether autonomous actions are safe before executing them.

## Core Problem Solved

Modern AI agents (like Claude) can take autonomous actions: code changes, deployments, configuration updates, data operations. But without safety guardrails, autonomous actions can be risky.

This example shows how to:
1. **Certify** actions using deterministic safety mathematics (the QAE kernel)
2. **Integrate** certificates into Claude's decision-making
3. **Enforce** safety budgets and rate limits
4. **Audit** all certifications for compliance

## Architecture

```
Claude Desktop
    ↓ (user message)
MCP Client
    ↓ (tool invocation)
MCP Protocol
    ↓ (JSON-RPC)
qae-claude-mcp-server (this repo)
    ↓ (API calls)
qae_safety Python Package (PyO3)
    ↓
Rust QAE Safety Kernel
    ↓
SafetyCertificate(decision, margins, hash)
```

## What You Get

### Server Implementation
- **`src/qae_mcp_server/server.py`** — Full MCP server with 3 tools
- **Lazy initialization** — Certifier created on first use
- **Stateful history** — Tracks last 50 certifications
- **Error handling** — Validates inputs, catches exceptions
- **Logging** — All operations logged for debugging

### Tools Exposed to Claude
1. **`certify_action`** — Main certification endpoint
   - Takes: action_id, agent_id, scope [0,1], reversibility [0,1], sensitivity [0,1]
   - Returns: decision (Certified/Warning/Escalate/Blocked), margins, certificate_id

2. **`check_budget`** — Budget status
   - Returns: budget_limit, budget_used, budget_remaining, utilization %

3. **`get_certification_history`** — Audit trail
   - Returns: recent certifications (limit 50, retrievable in batches)

### Documentation
- **README.md** — Full API reference and architecture
- **QUICKSTART.md** — 5-minute setup guide
- **INTEGRATION.md** — How to use certificates in decision-making
- **EXAMPLES.md** — 6 realistic scenarios with walkthroughs
- **DEVELOPMENT.md** — Extend and customize the server

### Tests
- **tests/test_server.py** — 15+ unit tests covering:
  - Input validation
  - Certificate structure
  - Budget tracking
  - History management
  - Determinism
  - Edge cases

### Project Files
- **pyproject.toml** — Python project metadata and entry points
- **requirements.txt** — Dependencies
- **setup.cfg** — Tool configuration
- **.gitignore** — Standard Python ignore rules
- **LICENSE** — Apache 2.0
- **MANIFEST.in** — Packaging manifest

## Key Features

### Determinism
- Same inputs → Same output, always
- No randomness, no stochastic behavior
- Safe for audit trails, compliance, regression testing
- Includes deterministic hash for verification

### Safety Budgets
- Rate limit enforcement (default: 50 certifications/hour)
- Budget tracking (default: 100 certifications/day)
- Prevents budget exhaustion attacks
- Resets on daily schedule

### Decision Framework
Four outcomes:
- **Certified** (Safe): All margins > 0.6 → Proceed
- **CertifiedWithWarning** (Caution): Margins 0.3-0.6 → Proceed with safeguards
- **EscalateToHuman** (Danger): Margins 0.1-0.3 → Get human approval
- **Blocked** (Danger): Margins ≤ 0.1 → Do not proceed

### Production Ready
- Clean code with docstrings
- Type hints (partially)
- Comprehensive error handling
- Logging for debugging
- Unit tests with pytest
- Linting ready (black, isort, flake8)

## How It Works

### Example Usage in Claude

**User**: "Is it safe to deploy the new recommendation algorithm to 10% of users?"

**Claude**:
1. Interprets the action
2. Scores dimensions:
   - Scope: 0.1 (10% of users)
   - Reversibility: 0.4 (requires hotfix)
   - Sensitivity: 0.7 (impacts user experience)
3. Invokes `certify_action` tool
4. Receives certificate
5. Explains decision to user

**Certificate** (example):
```json
{
  "decision": "CertifiedWithWarning",
  "zone": "Caution",
  "margins": {
    "scope": 0.9,
    "reversibility": 0.4,
    "sensitivity": 0.3
  },
  "binding_constraint": "reversibility"
}
```

**Claude**: "Proceed with caution. The binding constraint is reversibility (margin: 0.4). Have a rollback plan ready. Monitor closely for 24 hours."

## Real-World Scenarios

### Safe (Certified)
- Cosmetic UI changes
- Internal logging fixes
- Feature flags (easily reversible)
- Low-scope internal operations

### Caution (CertifiedWithWarning)
- Feature rollouts (25-50% traffic)
- Pricing changes (with monitoring)
- Moderate database changes
- Configuration updates with impact

### Danger (EscalateToHuman)
- Global database schema changes
- Revenue-critical operations
- Changes with difficult reversals
- High-impact deployments

### Danger (Blocked)
- PII data exports
- Permanent data deletions
- Global high-impact changes
- Operations violating policy

See **EXAMPLES.md** for detailed walkthroughs.

## Technology Stack

| Component | Purpose |
|-----------|---------|
| Python 3.9+ | Language |
| mcp 1.0+ | MCP SDK |
| qae-safety 0.1+ | Safety kernel (PyPI) |
| FastMCP | Server framework |
| pytest | Testing |
| black/isort/flake8 | Code quality |

## File Structure

```
qae-claude-mcp-example/
├── README.md                          ← User documentation
├── QUICKSTART.md                      ← 5-minute setup
├── INTEGRATION.md                     ← How to use certificates
├── EXAMPLES.md                        ← 6 real scenarios
├── DEVELOPMENT.md                     ← Extend the server
├── PROJECT_OVERVIEW.md                ← This file
├── LICENSE                            ← Apache 2.0
├── requirements.txt                   ← Dependencies
├── pyproject.toml                     ← Project metadata
├── setup.cfg                          ← Tool config
├── .gitignore                         ← Git rules
├── MANIFEST.in                        ← Package manifest
├── claude_desktop_config.example.json ← MCP config template
└── src/
    ├── __init__.py                    ← Package init
    ├── __main__.py                    ← Entry point
    └── server.py                      ← MCP server (400 lines)
└── tests/
    ├── __init__.py
    └── test_server.py                 ← 15+ tests
```

## Getting Started

### Absolute Minimum (5 min)
```bash
pip install -e .
# Update claude_desktop_config.json
# Restart Claude Desktop
# Start using certify_action tool
```

### Full Setup (15 min)
```bash
pip install -e ".[dev]"
pytest tests/
black src/ tests/
python -m qae_mcp_server  # Test server
# Update configuration
# Verify in Claude
```

### Customize (30+ min)
- Edit `src/qae_mcp_server/server.py` to adjust budget limits
- Add new tools
- Implement domain-specific adapters
- Run integration tests

## Design Philosophy

### Simplicity
- Minimal dependencies (just `mcp` and `qae-safety`)
- Single file server (`src/qae_mcp_server/server.py`)
- No complex orchestration

### Production Quality
- Type hints
- Comprehensive docstrings
- Error handling
- Logging
- Unit tests
- Clean code (lintable)

### Extensibility
- FastMCP makes adding tools trivial
- Custom adapters can be implemented
- Budget/threshold configuration
- Stateful history for auditing

### Determinism
- QAE kernel is deterministic
- Same inputs → same outputs
- Hashes for verification
- Safe for compliance/audit

## Limitations & Notes

### What This Is NOT
- Not a production deployment (you deploy it)
- Not a replacement for human judgment (escalates complex decisions)
- Not a complete safety solution (one component of risk management)
- Not a guarantee (still requires human oversight)

### Assumptions
- `qae-safety` package is installed from PyPI
- Claude Desktop is configured correctly
- Python 3.9+ environment
- Network access for package installation

### Design Choices
- **Lazy initialization**: Certifier created on first tool call (faster startup)
- **In-memory history**: Last 50 certifications (restart to clear)
- **Global state**: Simpler than async/concurrent approach
- **No persistence**: History is ephemeral (add DB layer if needed)

## Next Steps

1. **Quick Start**: Read QUICKSTART.md (5 min)
2. **Setup**: Install and configure (10 min)
3. **Test**: Invoke tools in Claude (5 min)
4. **Learn**: Read INTEGRATION.md and EXAMPLES.md (30 min)
5. **Customize**: Adjust budgets, add tools, extend adapters (1+ hour)

## Support & References

### Documentation
- **QAE Research**: https://doi.org/10.6084/m9.figshare.31742857
- **QAE Platform**: https://qaesubstrate.com
- **MCP Protocol**: https://modelcontextprotocol.io
- **PyPI Package**: https://pypi.org/project/qae-safety/

### Issues
- Check README.md, DEVELOPMENT.md for troubleshooting
- Review test cases in `tests/test_server.py` for usage patterns
- Look at EXAMPLES.md for decision interpretation

## Author & License

**Author**: Northbeam Solutions LLC
**License**: Apache 2.0
**Version**: 0.1.0

This is a community example. The underlying QAE safety kernel is from the QAE fintech risk certification platform.

---

## Summary

This project is a **clean, well-documented, production-quality MCP server** that brings deterministic safety certification to Claude. Use it to:

✓ Evaluate action safety before execution
✓ Enforce safety budgets and rate limits
✓ Maintain audit trails of decisions
✓ Integrate safety into autonomous workflows
✓ Learn how to build MCP servers

Start with QUICKSTART.md. You'll be running in 5 minutes.
