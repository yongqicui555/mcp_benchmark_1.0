# QuantaRoute MCP Server

A Model Context Protocol (MCP) server that provides AI assistants (Claude Desktop, Cursor, and more) with powerful geocoding, location lookup, and DigiPin processing capabilities using the QuantaRoute Geocoding API.

**Package**: `@quantaroute/mcp-server` (MCP Server for AI Agents)  
**SDK**: [`quantaroute-geocoding`](https://www.npmjs.com/package/quantaroute-geocoding) (Node.js/TypeScript SDK)

**✅ Fully compatible with Claude Desktop and Cursor**

## Features

### 🗺️ Geocoding Tools
- **Geocode addresses** to DigiPin codes and coordinates
- **Reverse geocode** DigiPin codes to addresses
- **Convert coordinates** to DigiPin codes
- **Validate DigiPin** format and location
- **Batch geocode** multiple addresses (up to 100)
- **Autocomplete** address suggestions

### 🚀 Revolutionary Location Lookup with Nominatim + Pincode + Digipin
- **Lookup administrative boundaries** from coordinates (pincode, state, division, locality)
- **Lookup from DigiPin** codes
- **Batch location lookup** for multiple locations
- **Find nearby boundaries** within a radius [COMING SOON...]
- Access to **36,000+ postal boundaries** across India

### 📊 Utility Tools
- **Get API usage** statistics
- **Get location statistics** (boundaries, states, divisions)
- **Check API health** status

## Installation

This MCP server is compatible with **Claude Desktop** and **Cursor**. Follow the instructions below for your platform.

### For Claude Desktop

1. **Locate the Claude Desktop configuration file:**
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
   - **Linux**: `~/.config/Claude/claude_desktop_config.json`

2. **Edit the configuration file** and add:

```json
{
  "mcpServers": {
    "quantaroute": {
      "command": "npx",
      "args": [
        "-y",
        "@quantaroute/mcp-server"
      ],
      "env": {
        "QUANTAROUTE_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

3. **Save and restart Claude Desktop** to apply the changes.

### For Cursor

Add to your MCP configuration file (`~/.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "quantaroute": {
      "command": "npx",
      "args": [
        "-y",
        "@quantaroute/mcp-server"
      ],
      "env": {
        "QUANTAROUTE_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

Restart Cursor after making changes.

### Environment Variables

- `QUANTAROUTE_API_KEY` (required): Your QuantaRoute API key
  - Get your API key from: https://developers.quantaroute.com
  - Free tier test key: `demo_free_key_123` (for testing)

## Available Tools

### `geocode`
Geocode an address to get DigiPin code and coordinates.

**Parameters:**
- `address` (required): The address to geocode
- `city` (optional): City name
- `state` (optional): State name
- `pincode` (optional): Postal code
- `country` (optional): Country name (defaults to India)

**Example:**
```json
{
  "address": "Rohra Address, New Town",
  "city": "New Town",
  "state": "West Bengal",
  "pincode": "700163"
}
```

### `reverse_geocode`
Reverse geocode a DigiPin code to get coordinates and address.

**Parameters:**
- `digipin` (required): DigiPin code (format: XXX-XXX-XXXX)

### `coordinates_to_digipin`
Convert latitude and longitude to DigiPin code.

**Parameters:**
- `latitude` (required): Latitude (-90 to 90)
- `longitude` (required): Longitude (-180 to 180)

### `lookup_location_from_coordinates`
🚀 **REVOLUTIONARY**: Get administrative boundaries from coordinates.

Returns: pincode, state, division, locality, district, population density, and more.

**Parameters:**
- `latitude` (required): Latitude coordinate
- `longitude` (required): Longitude coordinate

### `lookup_location_from_digipin`
Get administrative boundaries from a DigiPin code.

**Parameters:**
- `digipin` (required): DigiPin code

### `batch_location_lookup`
Batch lookup for multiple locations (up to 100).

**Parameters:**
- `locations` (required): Array of location objects
  - Each object can have `latitude` + `longitude` OR `digipin`

### `batch_geocode`
Geocode multiple addresses in a single request (up to 100).

**Parameters:**
- `addresses` (required): Array of address objects

### `autocomplete`
Get address autocomplete suggestions.

**Parameters:**
- `query` (required): Search query (minimum 3 characters)
- `limit` (optional): Max suggestions (default: 5, max: 10)

### `find_nearby_boundaries [COMING SOON...]`
Find nearby postal boundaries within a radius.

**Parameters:**
- `latitude` (required): Center latitude
- `longitude` (required): Center longitude
- `radius_km` (optional): Search radius in km (default: 5.0, max: 100)
- `limit` (optional): Max results (default: 10, max: 50)

### `validate_digipin`
Validate DigiPin format and check if it's a real location.

**Parameters:**
- `digipin` (required): DigiPin code to validate

### `get_usage`
Get API usage statistics and quota information.

### `get_location_statistics`
Get live statistics about the Location Lookup service.

### `get_health`
Check API health status.

## REST API Wrapper

This project includes a REST API wrapper that makes all MCP tools accessible via HTTP endpoints for mobile and web applications.

### Features

- ✅ **RESTful API**: All MCP tools exposed as HTTP endpoints
- ✅ **Authentication**: API key via header or environment variable
- ✅ **CORS Support**: Ready for web and mobile apps
- ✅ **Vercel Ready**: Optimized for serverless deployment
- ✅ **Error Handling**: Comprehensive error handling and validation

### Quick Start

The REST API is **already deployed** and ready to use at:

**Base URL**: `https://mcp-gc.quantaroute.com/api`

**Note**: `mcp-gc` stands for MCP Geocoding. This follows the naming convention:
- `mcp-gc.quantaroute.com` - Geocoding MCP Server (this project)

#### Using the REST API

**1. Get API Information:**
```bash
curl https://mcp-gc.quantaroute.com/api
```

**2. Geocode an Address:**
```bash
curl -X POST https://mcp-gc.quantaroute.com/api/geocode \
  -H "Content-Type: application/json" \
  -H "x-api-key: your-api-key-here" \
  -d '{
    "address": "Rohra Address, New Town",
    "city": "New Town",
    "state": "West Bengal",
    "pincode": "700163"
  }'
```

**3. Health Check:**
```bash
curl -X GET https://mcp-gc.quantaroute.com/api/health \
  -H "x-api-key: your-api-key-here"
```

**4. Find Nearby Boundaries:[NOT RELEASED, COMING SOON...]**
```bash
curl -X POST https://mcp-gc.quantaroute.com/api/find-nearby-boundaries \
  -H "Content-Type: application/json" \
  -H "x-api-key: your-api-key-here" \
  -d '{
    "latitude": 28.6139,
    "longitude": 77.2090,
    "radius_km": 5.0,
    "limit": 10
  }'
```

This endpoint finds nearby postal boundaries within a specified radius. Useful for:
- Finding all pincodes within X km of a location
- Discovering nearby administrative boundaries
- Location-based search and discovery

#### JavaScript/TypeScript Example

```javascript
// Geocode an address
const response = await fetch('https://mcp-gc.quantaroute.com/api/geocode', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'x-api-key': 'your-api-key-here'
  },
  body: JSON.stringify({
    address: 'Rohra Address, Action Area I',
    city: 'New Town',
    state: 'West Bengal'
  })
});

const data = await response.json();
console.log(data);
```

#### Python Example

```python
import requests

# Geocode an address
response = requests.post(
    'https://mcp-gc.quantaroute.com/api/geocode',
    headers={
        'Content-Type': 'application/json',
        'x-api-key': 'your-api-key-here'
    },
    json={
        'address': 'Rohra Address, Action Area I, Ghuni',
        'city': 'New Town',
        'state': 'West Bengal'
    }
)

data = response.json()
print(data)
```

#### Deploying Your Own Instance

If you want to deploy your own instance:

1. **Deploy to Vercel**:
   ```bash
   vercel
   ```

2. **Set Environment Variable** (optional, for testing):
   ```bash
   vercel env add QUANTAROUTE_API_KEY
   ```

3. **Configure Custom Domain** (optional):
   - Add your custom domain in Vercel
   - Configure DNS CNAME record pointing to Vercel
   - Wait for DNS propagation and SSL certificate

### API Documentation

For complete REST API documentation, see [API.md](./API.md).

**Available Endpoints:**
- `GET /api` - API information
- `GET /api/health` - Health check
- `GET /api/usage` - Usage statistics
- `GET /api/location-statistics` - Location service statistics
- `GET /api/autocomplete?q=query` - Address autocomplete
- `GET /api/validate-digipin?digipin=XXX-XXX-XXXX` - Validate DigiPin
- `POST /api/geocode` - Geocode an address
- `POST /api/reverse-geocode` - Reverse geocode DigiPin
- `POST /api/coordinates-to-digipin` - Convert coordinates to DigiPin
- `POST /api/batch-geocode` - Batch geocode addresses
- `POST /api/lookup-location-from-coordinates` - Lookup from coordinates
- `POST /api/lookup-location-from-digipin` - Lookup from DigiPin
- `POST /api/batch-location-lookup` - Batch location lookup
- `POST /api/find-nearby-boundaries` - Find nearby boundaries [COMING SOON...]

### Authentication

The API supports authentication in two ways:

1. **Request Header** (Recommended for production):
   ```
   x-api-key: your-api-key-here
   ```
   - Users should get their own API key from [developers.quantaroute.com](https://developers.quantaroute.com)
   - Send the API key in the `x-api-key` header with each request
   - Each user's API key is validated by the backend API and usage is tracked separately

2. **Environment Variable** (Optional fallback for testing):
   ```
   QUANTAROUTE_API_KEY=your-api-key-here
   ```
   - Only used if no `x-api-key` header is provided
   - Useful for testing and development
   - Not recommended for production use

**Priority**: The request header takes precedence over the environment variable.

**Getting an API Key**: 
- Visit [developers.quantaroute.com](https://developers.quantaroute.com)
- Sign up and get your API key
- Use it in the `x-api-key` header for all API requests

## Development

### Prerequisites
- Node.js 18+
- TypeScript 5+

### Setup

```bash
# Install dependencies
npm install

# Build the project
npm run build

# Run in development mode
npm run dev
```

### Project Structure

```
mcp-server/
├── src/
│   ├── index.ts          # Main MCP server implementation
│   └── client.ts         # QuantaRoute API client
├── api/
│   └── [...path].ts      # REST API wrapper (Vercel serverless function)
├── dist/                 # Compiled JavaScript (generated)
├── package.json
├── tsconfig.json
├── vercel.json           # Vercel configuration
├── README.md
└── API.md                # REST API documentation
```

## API Documentation

Full API documentation: https://api.quantaroute.com/v1/digipin/docs

## License

MIT License

## Support

- **Website**: https://quantaroute.com
- **API Docs**: https://api.quantaroute.com/v1/digipin/docs
- **Issues**: https://github.com/mapdevsaikat/quantaroute-geocoder/issues

## Supported Platforms

✅ **Claude Desktop** - Fully supported  
✅ **Cursor** - Fully supported  
✅ **Other MCP-compatible clients** - Should work with any MCP-compatible application

## Example Usage in AI Assistants

Once configured, AI assistants (Claude, Cursor AI, etc.) can use tools like:

### Example 1: Geocoding
```
User: "What's the DigiPin for Biswa Bangla Gate, New Town?"

Assistant: [Uses geocode tool]
The DigiPin code for that address is 2TF-39M-JT5F, located at coordinates 22.5788545, 88.4716628.
Full Address: Biswa Bangla Gate, New Town, Biswa Bangla Sarani, Action Area I, New Town, Bidhannagar, North 24 Parganas, West Bengal, 700156, India
```

### Example 2: Location Lookup
```
User: "What administrative boundaries are at coordinates 28.6139, 77.2090?"

Assistant: [Uses lookup_location_from_coordinates tool]
That location is in:
- Pincode: 110001
- State: Delhi
- Division: New Delhi Central
- Locality: Connaught Place
- District: New Delhi
```

### Example 3: Reverse Geocoding
```
User: "What's the address for DigiPin 2TF-3FT-J825?"

Assistant: [Uses reverse_geocode tool]
The DigiPin 2TF-3FT-J825 corresponds to:
- Address: FE Block, Sector III, Bidhannagar, North 24 Parganas, West Bengal, 700106, India
- Coordinates: 22.580587°N, 88.419001°E
```

## Troubleshooting

### Claude Desktop Issues

1. **Server not appearing in Claude Desktop:**
   - Verify the config file path is correct for your OS
   - Check that the JSON syntax is valid
   - Restart Claude Desktop completely

2. **"Command not found" errors:**
   - Ensure Node.js 18+ is installed: `node --version`
   - Verify `npx` is available: `which npx`

3. **API authentication errors:**
   - Check that `QUANTAROUTE_API_KEY` is set correctly in the config
   - Verify the API key is valid at https://api.quantaroute.com

### Cursor Issues

1. **MCP server not loading:**
   - Check `~/.cursor/mcp.json` exists and has valid JSON
   - Restart Cursor completely
   - Check Cursor's MCP logs for errors

2. **Tools not available:**
   - Verify the server is running (check Cursor's MCP status)
   - Ensure API key is configured correctly

