# Publishing Guide

This guide walks you through publishing the MCP Dice Roller to PyPI and the MCP Registry.

## Prerequisites

1. **PyPI Account** - Create at https://pypi.org/account/register/
2. **GitHub Account** - You already have this (vandewilly)
3. **mcp-publisher CLI** - Install for registry publishing

## Step 1: Create GitHub Repository

```bash
cd /Users/vandewillyoliveiradasilva/dev/personal/mcp-dice-roller

# Initialize git
git init
git add .
git commit -m "Initial commit: MCP Dice Roller server"

# Create repo on GitHub (using gh cli or web interface)
gh repo create mcp-dice-roller --public --source=. --push
```

## Step 2: Configure PyPI Trusted Publishing

Instead of using API tokens, we'll use PyPI's "Trusted Publishing" which is more secure.

1. Go to https://pypi.org/manage/account/publishing/
2. Click "Add a new pending publisher"
3. Fill in:
   - **PyPI Project Name:** `mcp-dice-roller`
   - **Owner:** `vandewilly`
   - **Repository name:** `mcp-dice-roller`
   - **Workflow name:** `publish.yml`
   - **Environment name:** (leave blank)

## Step 3: Create a Release

```bash
# Tag a release
git tag v0.1.0
git push origin v0.1.0

# Or use GitHub web interface:
# 1. Go to your repo
# 2. Click "Releases" → "Create a new release"
# 3. Tag: v0.1.0
# 4. Title: v0.1.0 - Initial Release
# 5. Click "Publish release"
```

The GitHub Action will automatically publish to PyPI!

## Step 4: Verify PyPI Publication

```bash
# Wait a minute for PyPI to index
pip install mcp-dice-roller

# Test it works
python -c "from mcp_dice_roller import __version__; print(__version__)"
```

## Step 5: Install mcp-publisher CLI

```bash
# On macOS with Homebrew
brew tap anthropics/tap
brew install mcp-publisher

# Or download binary from:
# https://github.com/modelcontextprotocol/publisher/releases
```

## Step 6: Authenticate with GitHub

```bash
mcp-publisher login github
```

This will open a browser for GitHub OAuth authentication.

## Step 7: Publish to MCP Registry

```bash
cd /Users/vandewillyoliveiradasilva/dev/personal/mcp-dice-roller
mcp-publisher publish
```

## Step 8: Verify Registry Publication

```bash
curl "https://registry.modelcontextprotocol.io/v0/servers?search=dice-roller"
```

You should see your server in the results!

## Updating

For future releases:

1. Update version in:
   - `pyproject.toml`
   - `src/mcp_dice_roller/__init__.py`
   - `server.json`

2. Commit and tag:
   ```bash
   git add .
   git commit -m "Bump version to X.Y.Z"
   git tag vX.Y.Z
   git push origin main --tags
   ```

3. Create GitHub release (triggers PyPI publish)

4. Update MCP Registry:
   ```bash
   mcp-publisher publish
   ```

## Testing Locally

Before publishing, test the server locally:

```bash
# Install in development mode
pip install -e .

# Run tests
pip install pytest
pytest -v

# Test the server manually
python -m mcp_dice_roller
```

## Troubleshooting

### PyPI publish fails
- Check trusted publishing is configured correctly
- Verify workflow file name matches (`publish.yml`)
- Check the package name isn't already taken

### MCP Registry publish fails
- Ensure `server.json` is valid (check schema)
- Verify GitHub authentication is active
- Check package is published on PyPI first

### Server doesn't start
- Ensure `mcp` package is installed
- Check Python version (3.10+)
- Run with verbose logging to see errors
