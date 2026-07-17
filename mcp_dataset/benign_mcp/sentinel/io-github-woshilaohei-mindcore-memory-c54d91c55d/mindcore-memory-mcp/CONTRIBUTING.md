# Contributing to MindCore Memory MCP

Thank you for your interest in contributing! MindCore Memory is an open source project and welcomes all forms of contributions — code, docs, bug reports, feature ideas, and community support.

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to 1410770089@qq.com.

---

## Development Setup

### Prerequisites
- Python 3.10+
- Git

### Setup

```bash
# Clone
git clone https://github.com/woshilaohei/mindcore-memory-mcp.git
cd mindcore-memory-mcp

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -e ".[dev,semantic]"

# Run tests
pytest tests/ -v
```

### Running the MCP server locally

```bash
# Stdio mode
python -m mindcore_memory.server

# HTTP mode
python -m mindcore_memory.http_app
```

### Project Structure

```
mindcore-memory-mcp/
├── mindcore_memory/       # Main package
│   ├── __init__.py        # Package exports
│   ├── memory_engine.py   # Core memory engine (store/recall/delete)
│   ├── server.py          # MCP stdio server
│   ├── http_app.py        # HTTP server with /health /metrics
│   ├── bnd.py             # 3D Boundary Balance algorithm
│   ├── deduction.py       # Deduction reasoning engine
│   ├── slo.py             # SLO tracking (P95/P99)
│   ├── metrics.py         # Prometheus metrics collector
│   ├── circuit_breaker.py # Circuit breaker (3-state)
│   └── retry.py           # Exponential backoff retry
├── tests/                 # Test suite (118+ tests)
├── docs/                  # Documentation
│   ├── comparison.md      # Competitive comparison
│   └── boundary-algorithm.md  # BND algorithm deep dive
├── .github/workflows/     # CI/CD (ci.yml + publish-mcp.yml)
├── pyproject.toml         # Package config
├── CHANGELOG.md           # Version history
├── CONTRIBUTING.md        # You are here
├── CODE_OF_CONDUCT.md     # Community standards
├── SECURITY.md            # Security policy
├── SUPPORT.md             # Getting help
└── LICENSE                # MIT
```

---

## How to Contribute

### Found an Issue?

1. Check [open issues](https://github.com/woshilaohei/mindcore-memory-mcp/issues)
2. Look for `good first issue` labels — they're beginner-friendly
3. If your issue isn't listed, open a new one

### Want to Add a Feature?

1. **Open an issue first** to discuss your idea before writing code
2. Fork the repository
3. Create a branch: `git checkout -b feat/your-feature-name`
4. Write code + tests
5. Run tests: `pytest tests/ -v`
6. Commit with conventional format: `git commit -m 'feat: add your feature'`
7. Push and open a Pull Request

### Writing Your First PR?

1. Find an issue labeled `good first issue`
2. Comment "I'd like to work on this" to claim it
3. Follow the setup steps above
4. Ask questions in the issue — we're happy to help!

---

## Pull Request Guidelines

### Commit Format
We use [Conventional Commits](https://www.conventionalcommits.org/):
- `feat:` — New feature
- `fix:` — Bug fix
- `docs:` — Documentation changes
- `refactor:` — Code restructuring (no behavior change)
- `test:` — Adding or updating tests
- `chore:` — Build/config/tooling changes

### PR Checklist
- [ ] Tests pass (`pytest tests/ -v`)
- [ ] New code has tests
- [ ] Documentation updated if needed
- [ ] PR description explains what changed and why

---

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_memory.py -v

# Run tests with coverage
pytest tests/ -v --cov=mindcore_memory --cov-report=term

# Run a single test
pytest tests/test_bnd_deduction.py::test_bnd_score -v
```

## Reporting Bugs

Please open an [issue](https://github.com/woshilaohei/mindcore-memory-mcp/issues) with:

- **Description**: Clear explanation of the problem
- **Steps to reproduce**: Exact commands or code to trigger the bug
- **Expected vs actual**: What you expected to happen, what actually happened
- **Environment**: OS, Python version (`python --version`), package version (`pip show mindcore-memory`)

---

## Community

- [GitHub Discussions](https://github.com/woshilaohei/mindcore-memory-mcp/discussions) — Q&A, ideas, community support
- Email: 1410770089@qq.com

## License

By contributing, you agree that your code will be licensed under the [MIT License](LICENSE).
