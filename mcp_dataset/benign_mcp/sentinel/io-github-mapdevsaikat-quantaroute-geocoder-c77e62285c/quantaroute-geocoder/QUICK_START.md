# Quick Start Guide

## ✅ What's Been Created

A complete Node.js MCP server for QuantaRoute Geocoding API with:

- ✅ 13 MCP tools covering all major functionality
- ✅ TypeScript implementation with proper types
- ✅ Ready for GitHub deployment via npx
- ✅ **REST API wrapper** - Deployed and ready to use at `https://mcp-gc.quantaroute.com`
- ✅ Complete documentation

## 🚀 Next Steps

### 1. Push to GitHub

```bash
cd mcp-server
git init
git add .
git commit -m "Initial commit: QuantaRoute Geocoder MCP Server"
git remote add origin https://github.com/mapdevsaikat/quantaroute-geocoder.git
git branch -M main
git push -u origin main
```

### 2. Configure MCP Client

Add to `~/.cursor/mcp.json`:

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

### 3. Test It

Restart Cursor/Claude Desktop and try:
- "What's the DigiPin for Biswa Bangla Gate, New Town?"
- "Lookup administrative boundaries for coordinates 28.6139, 77.2090"

## 📋 Available Tools

1. **geocode** - Geocode addresses to DigiPin
2. **reverse_geocode** - Reverse geocode DigiPin to address
3. **coordinates_to_digipin** - Convert coordinates to DigiPin
4. **validate_digipin** - Validate DigiPin format
5. **batch_geocode** - Batch geocode (up to 100 addresses)
6. **autocomplete** - Address autocomplete suggestions
7. **lookup_location_from_coordinates** - 🚀 Revolutionary location lookup
8. **lookup_location_from_digipin** - Lookup from DigiPin
9. **batch_location_lookup** - Batch location lookup
10. **find_nearby_boundaries** - Find nearby postal boundaries [COMING SOON...]
11. **get_usage** - API usage statistics
12. **get_location_statistics** - Location service stats
13. **get_health** - API health check

## 🔑 API Key

Get your API key from: https://developers.quantaroute.com

Free tier test key: `demo_free_key_123`

## 🌐 Using the REST API

The MCP server is also available as a **REST API** for web and mobile applications.

### Base URL
```
https://mcp-gc.quantaroute.com/api
```

### Quick Example

**Get API Information:**
```bash
curl https://mcp-gc.quantaroute.com/api
```

**Geocode an Address:**
```bash
curl -X POST https://mcp-gc.quantaroute.com/api/geocode \
  -H "Content-Type: application/json" \
  -H "x-api-key: your-api-key-here" \
  -d '{
    "address": "Biswa Bangla Gate, New Town",
    "city": "New Town",
    "state": "West Bengal",
    "pincode": "700156"
  }'
```

**Health Check:**
```bash
curl -X GET https://mcp-gc.quantaroute.com/api/health \
  -H "x-api-key: your-api-key-here"
```

**Find Nearby Boundaries: [NOT RELEASED, COMING SOON...]**
```bash
curl -X POST https://mcp-gc.quantaroute.com/api/find-nearby-boundaries \
  -H "Content-Type: application/json" \
  -H "x-api-key: your-api-key-here" \
  -d '{
    "latitude": 22.57845,
    "longitude": 88.42123,
    "radius_km": 5.0,
    "limit": 10
  }'
```

This endpoint finds nearby postal boundaries within a specified radius. Useful for:
- Finding all pincodes within X km of a location
- Discovering nearby administrative boundaries
- Location-based search and discovery

### Authentication

The REST API supports two authentication methods:

1. **Request Header** (Recommended):
   ```
   x-api-key: your-api-key-here
   ```

2. **Environment Variable** (Optional fallback for testing):
   ```
   QUANTAROUTE_API_KEY=your-api-key-here
   ```

**Note**: Users should get their own API key from [developers.quantaroute.com](https://developers.quantaroute.com) and send it in the `x-api-key` header with each request.

### Available REST Endpoints

- `GET /api` - API information and documentation
- `GET /api/health` - Health check
- `GET /api/usage` - Usage statistics
- `GET /api/location-statistics` - Location service statistics
- `GET /api/autocomplete?q=query&limit=5` - Address autocomplete
- `GET /api/validate-digipin?digipin=XXX-XXX-XXXX` - Validate DigiPin
- `POST /api/geocode` - Geocode an address
- `POST /api/reverse-geocode` - Reverse geocode DigiPin
- `POST /api/coordinates-to-digipin` - Convert coordinates to DigiPin
- `POST /api/batch-geocode` - Batch geocode (up to 100 addresses)
- `POST /api/lookup-location-from-coordinates` - Lookup from coordinates
- `POST /api/lookup-location-from-digipin` - Lookup from DigiPin
- `POST /api/batch-location-lookup` - Batch location lookup
- `POST /api/find-nearby-boundaries` - Find nearby boundaries [COMING SOON...]

### JavaScript/TypeScript Example

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

### Python Example

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

## 📚 Full Documentation

See [README.md](./README.md) for complete documentation.

