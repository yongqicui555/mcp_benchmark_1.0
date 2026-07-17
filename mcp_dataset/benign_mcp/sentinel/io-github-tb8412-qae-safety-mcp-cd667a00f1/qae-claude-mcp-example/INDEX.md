# Complete File Index

## Quick Navigation

### Getting Started (Read First)
1. **QUICKSTART.md** (6.2 KB) — 5-minute setup guide. Start here.
2. **README.md** (5.9 KB) — Full documentation with API reference
3. **PROJECT_OVERVIEW.md** (9.6 KB) — High-level architecture and features

### Learning & Integration
4. **INTEGRATION.md** (7.7 KB) — How to interpret and use certificates
5. **EXAMPLES.md** (14 KB) — 6 real-world scenarios with detailed walkthroughs
6. **DEVELOPMENT.md** (4.6 KB) — Customize and extend the server

### Reference
7. **LICENSE** (6.0 KB) — Apache 2.0 license
8. **MANIFEST.in** (132 B) — Package manifest

### Configuration
9. **claude_desktop_config.example.json** (135 B) — MCP server configuration template
10. **pyproject.toml** (1.7 KB) — Python project metadata
11. **setup.cfg** (706 B) — Tool configuration
12. **requirements.txt** (29 B) — Dependencies

### Source Code

#### Main Server
- **src/qae_mcp_server/server.py** (343 lines) — Complete MCP server implementation
  - `@server.tool()` decorated functions
  - `certify_action()` — Main certification tool
  - `check_budget()` — Budget status tool
  - `get_certification_history()` — Audit trail tool
  - `_initialize_certifier()` — Lazy init
  - `_get_certifier()` — Singleton getter
  - `main()` — Entry point

#### Package Initialization
- **src/qae_mcp_server/__init__.py** (23 lines) — Package metadata and exports
- **src/qae_mcp_server/__main__.py** (10 lines) — Entry point for `python -m qae_mcp_server`

#### Tests
- **tests/__init__.py** — Test package
- **tests/test_server.py** (299 lines) — 15+ unit tests
  - TestInitialization — Certifier creation
  - TestCertifyActionTool — Action certification
  - TestCheckBudgetTool — Budget queries
  - TestCertificationHistoryTool — History management
  - TestDeterminism — Reproducibility

### Directory Structure
```
qae-claude-mcp-example/
├── Documentation (8 files)
│   ├── QUICKSTART.md ...................... Start here (5 min)
│   ├── README.md .......................... Full reference
│   ├── PROJECT_OVERVIEW.md ............... Architecture overview
│   ├── INTEGRATION.md ..................... How to use certificates
│   ├── EXAMPLES.md ........................ 6 real scenarios
│   ├── DEVELOPMENT.md ..................... Extend/customize
│   └── INDEX.md ........................... This file
│
├── Configuration (4 files)
│   ├── pyproject.toml ..................... Python project metadata
│   ├── setup.cfg .......................... Tool configuration
│   ├── requirements.txt ................... Dependencies
│   └── claude_desktop_config.example.json . MCP config template
│
├── Legal (2 files)
│   ├── LICENSE ............................ Apache 2.0
│   └── MANIFEST.in ........................ Package manifest
│
├── Source Code (2 dirs)
│   ├── src/
│   │   ├── __init__.py ................... Package init
│   │   ├── __main__.py ................... Entry point
│   │   └── server.py ..................... MCP server (343 lines)
│   │
│   └── tests/
│       ├── __init__.py ................... Test package
│       └── test_server.py ................ Unit tests (299 lines)
│
├── .gitignore ............................ Git ignore rules
└── This repository root
```

## File Statistics

| Metric | Value |
|--------|-------|
| Total files | 16 |
| Documentation files | 8 |
| Python source files | 5 |
| Configuration files | 4 |
| Test files | 1 |
| Server implementation (lines) | 343 |
| Test coverage (lines) | 299 |
| Total documentation (KB) | ~65 |
| Total project size (KB) | ~88 |

## How to Use This Index

### I want to get started immediately
→ Read **QUICKSTART.md**

### I want to understand the architecture
→ Read **PROJECT_OVERVIEW.md**, then **README.md**

### I want to integrate with Claude
→ Read **QUICKSTART.md**, then **INTEGRATION.md**

### I want to see examples
→ Read **EXAMPLES.md** (6 realistic scenarios)

### I want to extend the server
→ Read **DEVELOPMENT.md**, then edit **src/qae_mcp_server/server.py**

### I want to run tests
→ Run `pytest tests/test_server.py`

### I want to deploy to production
→ Read **DEVELOPMENT.md** (sections on packaging and deployment)

### I need API reference
→ See **README.md** (API Reference section)

### I need to troubleshoot
→ See **DEVELOPMENT.md** (Troubleshooting section)

## Key Concepts

### Three Constraint Dimensions

All actions are evaluated across three dimensions in [0, 1]:

1. **Scope**: How many users/systems affected?
   - 0 = Single user
   - 0.5 = Team/department
   - 1.0 = All users

2. **Reversibility**: How easily can you undo this?
   - 0 = Permanent (cannot reverse)
   - 0.5 = Reversible (1-2 hours effort)
   - 1.0 = Trivial (seconds)

3. **Sensitivity**: How much can this impact users/revenue?
   - 0 = No impact
   - 0.5 = Moderate impact
   - 1.0 = Critical impact

### Four Decision Zones

Every certificate has a decision and zone:

| Decision | Zone | Margin | Action |
|----------|------|--------|--------|
| Certified | Safe | > 0.6 | Proceed immediately |
| CertifiedWithWarning | Caution | 0.3-0.6 | Proceed with safeguards |
| EscalateToHuman | Danger | 0.1-0.3 | Get human approval |
| Blocked | Danger | ≤ 0.1 | Do not proceed |

### Three Tools Exposed to Claude

1. **certify_action(action_id, agent_id, scope, reversibility, sensitivity)**
   - Evaluates action safety
   - Returns: certificate with decision, margins, hash

2. **check_budget()**
   - Returns budget status
   - Prevents budget exhaustion

3. **get_certification_history(limit=10)**
   - Retrieves recent certifications
   - Enables auditing

## Dependencies

### Production
- **qae-safety** ≥ 0.1.1 — QAE safety kernel (PyPI)
- **mcp** ≥ 1.0.0 — Model Context Protocol SDK

### Development (optional)
- **pytest** ≥ 7.0 — Testing
- **black** ≥ 23.0 — Code formatting
- **isort** ≥ 5.0 — Import sorting
- **flake8** ≥ 6.0 — Linting
- **mypy** ≥ 1.0 — Type checking

## Installation Methods

### Quick Install
```bash
pip install -e .
```

### Development Install
```bash
pip install -e ".[dev]"
```

### Manual
```bash
pip install qae-safety mcp
```

## Entry Points

### Run as Module
```bash
python -m qae_mcp_server
```

### Run via Entry Point (after `pip install -e .`)
```bash
qae-mcp-server
```

### Use in Claude Desktop
Configure `claude_desktop_config.json` and restart Claude Desktop.

## Testing

### Run All Tests
```bash
pytest tests/
```

### Run with Coverage
```bash
pytest --cov=qae_mcp_server tests/
```

### Run Specific Test Class
```bash
pytest tests/test_server.py::TestCertifyActionTool
```

## Code Quality

### Format Code
```bash
black src/ tests/
```

### Sort Imports
```bash
isort src/ tests/
```

### Lint
```bash
flake8 src/ tests/
```

### Type Check
```bash
mypy src/
```

### All Checks
```bash
black --check src/ tests/ && isort --check src/ tests/ && flake8 src/ tests/ && mypy src/
```

## License

Apache License 2.0. See **LICENSE** file.

## Author

Northbeam Solutions LLC
https://northbeam.solutions

## References

- **QAE Research**: https://doi.org/10.6084/m9.figshare.31742857
- **QAE Platform**: https://qaesubstrate.com
- **MCP Protocol**: https://modelcontextprotocol.io
- **PyPI Package**: https://pypi.org/project/qae-safety/

---

**Last Updated**: 2025-03-15
**Project Version**: 0.1.0
**Status**: Production-Ready ✓
