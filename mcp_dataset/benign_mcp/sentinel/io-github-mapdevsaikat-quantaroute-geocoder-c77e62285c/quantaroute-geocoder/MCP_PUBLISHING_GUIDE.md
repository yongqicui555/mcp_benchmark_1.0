# MCP Registry Publishing Guide

## 📦 Package Naming Strategy

### Your Packages
- **SDK/Client Library**: `quantaroute-geocoding` (already published)
  - For developers building apps with QuantaRoute API
  - Usage: `npm install quantaroute-geocoding`

- **MCP Server**: `@quantaroute/mcp-server` (NEW - needs publishing)
  - For AI assistants (Claude, Cursor) to use Quantaroute API
  - Usage: `npx @quantaroute/mcp-server`

### Clear Distinction
This naming makes it crystal clear:
- `quantaroute-geocoding` = SDK for developers
- `@quantaroute/mcp-server` = MCP server for AI agents

---

## ✅ Changes Made

### 1. Updated `package.json`
- ✅ Renamed: `quantaroute-geocoder` → `@quantaroute/mcp-server`
- ✅ Added: `"mcpName": "io.github.mapdevsaikat/quantaroute-geocoder"`
- ✅ Updated bin command: `quantaroute-mcp-server`

### 2. Created `server.json`
- ✅ Metadata file for MCP Registry
- ✅ Includes all server capabilities and environment variables
- ✅ Proper categories and tags for discoverability

### 3. Updated README.md
- ✅ Clear package distinction at the top
- ✅ Updated all installation examples
- ✅ Changed from git URL to npm package

### 4. Created GitHub Actions Workflow
- ✅ Auto-publish to npm and MCP Registry on version tags
- ✅ Located at `.github/workflows/publish-mcp.yml`

---

## 🚀 Publishing Steps

### First-Time Setup

#### 1. Create npm Organization (One-time)
```bash
# Login to npm
npm login

# Create the @quantaroute organization on npmjs.com
# Visit: https://www.npmjs.com/org/create
# Organization name: quantaroute
```

#### 2. Install mcp-publisher CLI
```bash
# macOS/Linux
curl -L "https://github.com/modelcontextprotocol/registry/releases/latest/download/mcp-publisher_$(uname -s | tr '[:upper:]' '[:lower:]')_$(uname -m | sed 's/x86_64/amd64/;s/aarch64/arm64/').tar.gz" | tar xz mcp-publisher && sudo mv mcp-publisher /usr/local/bin/

# Or via Homebrew
brew install mcp-publisher

# Verify
mcp-publisher --help
```

#### 3. Setup GitHub Secrets (for automated publishing)
Go to your repo settings: https://github.com/mapdevsaikat/quantaroute-geocoder/settings/secrets/actions

Add secret:
- Name: `NPM_TOKEN`
- Value: Your npm access token (create at https://www.npmjs.com/settings/tokens)

---

### Manual Publishing (First Release)

```bash
cd /Users/saikatmaiti/Documents/TechNova/quantaroute-geocoder

# 1. Build the project
npm install
npm run build

# 2. Publish to npm
npm publish --access public

# 3. Authenticate with MCP Registry
mcp-publisher login github
# Follow the prompts to authorize via GitHub

# 4. Publish to MCP Registry
mcp-publisher publish
```

---

### Automated Publishing (After First Release)

Once you've done the first manual publish, future releases are automatic:

```bash
# 1. Make your changes
git add .
git commit -m "Add new features"

# 2. Bump version and create tag
npm version patch  # or minor, or major
# This creates a git tag like v1.0.1

# 3. Push with tags
git push && git push --tags

# 🎉 GitHub Actions automatically:
#    - Builds the project
#    - Publishes to npm
#    - Publishes to MCP Registry
```

---

## 📋 Version Bump Guidelines

```bash
# Bug fixes and small changes
npm version patch  # 1.0.0 → 1.0.1

# New features (backward compatible)
npm version minor  # 1.0.1 → 1.1.0

# Breaking changes
npm version major  # 1.1.0 → 2.0.0
```

---

## 🔍 Verification After Publishing

### Check npm
```bash
# View package page
open https://www.npmjs.com/package/@quantaroute/mcp-server

# Test installation
npx @quantaroute/mcp-server --help
```

### Check MCP Registry
```bash
# Search via API
curl "https://registry.modelcontextprotocol.io/v0.1/servers?search=quantaroute"

# Or visit the registry website
open https://registry.modelcontextprotocol.io
```

### Test in Claude Desktop
```json
{
  "mcpServers": {
    "quantaroute": {
      "command": "npx",
      "args": ["-y", "@quantaroute/mcp-server"],
      "env": {
        "QUANTAROUTE_API_KEY": "free_test_key_hash_12345"
      }
    }
  }
}
```

---

## 🎯 User Experience Comparison

### Before (Less Clear)
```bash
# SDK
npm install quantaroute-geocoding

# MCP Server (unclear naming)
npx quantaroute-geocoder
```

### After (Crystal Clear)
```bash
# SDK - for developers
npm install quantaroute-geocoding

# MCP Server - for AI agents
npx @quantaroute/mcp-server
```

---

## 📊 Benefits of New Naming

1. **Clear Purpose**: `@quantaroute/mcp-server` immediately tells users it's an MCP server
2. **Organization**: Scoped package (`@quantaroute/`) shows professional branding
3. **Future-Proof**: Easy to add more packages under `@quantaroute/` scope
4. **Discoverability**: MCP Registry will list it clearly
5. **No Confusion**: Distinct from the SDK package

---

## 🆘 Troubleshooting

### "Cannot publish to @quantaroute scope"
- Create the organization on npmjs.com first: https://www.npmjs.com/org/create
- Ensure you're logged in: `npm whoami`

### "Registry validation failed"
- Ensure `mcpName` in `package.json` matches `name` in `server.json`
- Both should use `io.github.mapdevsaikat/quantaroute-geocoder`

### "Permission denied to publish"
- Your GitHub account must match the namespace prefix
- `io.github.mapdevsaikat/` requires you to be logged in as `mapdevsaikat`

### GitHub Actions Fails
- Check you've added `NPM_TOKEN` secret in repo settings
- Ensure the token has "Automation" or "Publish" permissions

---

## 📝 Next Steps

1. ✅ Review the changes made to your files
2. ⏳ Create `@quantaroute` organization on npmjs.com
3. ⏳ Perform first manual publish to npm
4. ⏳ Authenticate and publish to MCP Registry
5. ⏳ Test installation with `npx @quantaroute/mcp-server`
6. ⏳ Verify in MCP Registry at https://registry.modelcontextprotocol.io
7. ⏳ Future releases: Just tag and push (automated!)

---

## 🎉 Marketing Message

Once published, promote it as:

> **QuantaRoute now has two packages:**
> 
> 🔧 **`quantaroute-geocoding`** - Node.js SDK for developers  
> 🤖 **`@quantaroute/mcp-server`** - MCP Server for AI agents
> 
> Same powerful API, two ways to integrate!

---

## 📞 Support

- Documentation: https://quantaroute.com
- GitHub: https://github.com/mapdevsaikat/quantaroute-geocoder
- Email: hello@quantaroute.com
