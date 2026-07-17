# Contributing to prufa-mcp

Thanks for being here. The MCP server is intentionally small — the heavy
lifting (Playwright runner, deterministic checks, report rendering) lives
in the [hosted product](https://prufa.dev). This repo is the thin client
and the install surface.

## Good first issues

We seed a few `good first issue` tickets on day 1 — pick one, comment to
claim it, and we'll review the PR within 24 hours.

## Local development

```bash
git clone https://github.com/prufa-dev/prufa-mcp
cd prufa-mcp
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Pull request process

1. Open an issue describing the change (unless it's a typo / doc fix).
2. Fork, branch, commit. One logical change per commit.
3. Open a PR. Reference the issue.
4. We review within 24 hours. We may push back; we don't merge without a green CI.
5. We use [Conventional Commits](https://www.conventionalcommits.org/).

## Code of conduct

Be kind. We're all here to ship QA agents for vibe-coded apps. Don't be
a jerk in issues or PRs.
