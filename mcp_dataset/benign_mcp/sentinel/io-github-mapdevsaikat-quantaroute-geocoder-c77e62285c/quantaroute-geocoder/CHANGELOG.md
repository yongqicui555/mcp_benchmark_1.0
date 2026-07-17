# Changelog

All notable changes to the QuantaRoute MCP Server will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-02-12

### Changed
- **BREAKING**: Renamed package from `quantaroute-geocoder` to `@quantaroute/mcp-server`
  - This provides clearer distinction from the SDK package `quantaroute-geocoding`
  - Users should update their MCP configuration to use `npx @quantaroute/mcp-server`
- Updated binary command name to `quantaroute-mcp-server`
- Updated server name in MCP initialization

### Added
- Added `mcpName` field to package.json for MCP Registry compliance
- Created `server.json` for MCP Registry publishing
- Added GitHub Actions workflow for automated publishing to npm and MCP Registry
- Added comprehensive MCP_PUBLISHING_GUIDE.md with publishing instructions
- Added categories and tags for better discoverability in MCP Registry

### Package Names
- **MCP Server** (this package): `@quantaroute/mcp-server` - for AI agents
- **SDK**: `quantaroute-geocoding` - for developers

### Migration Guide

#### Before (old package name)
```json
{
  "mcpServers": {
    "quantaroute": {
      "command": "npx",
      "args": ["-y", "git+https://github.com/mapdevsaikat/quantaroute-geocoder.git"],
      "env": {
        "QUANTAROUTE_API_KEY": "your-key"
      }
    }
  }
}
```

#### After (new package name)
```json
{
  "mcpServers": {
    "quantaroute": {
      "command": "npx",
      "args": ["-y", "@quantaroute/mcp-server"],
      "env": {
        "QUANTAROUTE_API_KEY": "your-key"
      }
    }
  }
}
```

## [0.1.0] - 2026-01-XX (Pre-release)

### Added
- Initial MCP server implementation with 13 tools
- Geocoding capabilities (address to DigiPin, coordinates to DigiPin)
- Reverse geocoding (DigiPin to address)
- Location lookup with administrative boundaries (19,000+ postal boundaries)
- Batch processing for multiple addresses and locations
- Address autocomplete functionality
- DigiPin validation
- API usage statistics
- Location service statistics
- REST API wrapper for Vercel deployment
- Full TypeScript support
- Comprehensive documentation

### Features
- ✅ Claude Desktop compatibility
- ✅ Cursor compatibility
- ✅ Stdio transport for MCP communication
- ✅ Environment variable configuration for API keys
- ✅ CORS-enabled REST API endpoints
- ✅ Error handling with proper MCP error codes
- ✅ Input validation for all tools
- ✅ Support for India's 19,000+ postal boundaries
- ✅ Revolutionary location lookup (pincode, state, division, locality)
