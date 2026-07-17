# QuantaRoute Geocoder REST API Documentation

REST API wrapper for the QuantaRoute Geocoder MCP Server. This API makes all MCP tools accessible via HTTP endpoints for mobile and web applications.

## Base URL

```
https://mcp-gc.quantaroute.com/api
```

**Note**: `mcp-gc` stands for MCP Geocoding. This is the REST API wrapper for the QuantaRoute Geocoder MCP Server.

## Authentication

The API supports authentication via API key in two ways:

1. **Request Header** (Recommended for client apps):
   ```
   x-api-key: your-api-key-here
   ```

2. **Environment Variable** (For server-side):
   ```
   QUANTAROUTE_API_KEY=your-api-key-here
   ```

**Priority**: Request header takes precedence over environment variable.

### Getting an API Key

Users need a valid API key from [developers.quantaroute.com](https://developers.quantaroute.com) to use this API. Each user's API key:
- Is validated by the backend API at `api.quantaroute.com`
- Has its own rate limits and usage quota
- Tracks usage separately per API key
- Can be used directly with this REST API wrapper

**How it works**: The REST API wrapper forwards your API key to the backend API for validation. Your usage is tracked against your own API key, not the wrapper's environment variable.

## Endpoints

### Health Check

**GET** `/api/health`

Check API health status.

**Response:**
```json
{
  "success": true,
  "data": {
    "status": "ok",
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

---

### Get API Information

**GET** `/api`

Get API documentation and available endpoints.

**Response:**
```json
{
  "success": true,
  "message": "QuantaRoute Geocoder REST API",
  "version": "1.0.0",
  "endpoints": { ... }
}
```

---

### Geocode Address

**POST** `/api/geocode`

Geocode an address to get DigiPin code and coordinates.

**Request Body:**
```json
{
  "address": "123 Main Street, New Delhi",
  "city": "New Delhi",
  "state": "Delhi",
  "pincode": "110001",
  "country": "India"
}
```

**Required Fields:**
- `address` (string): The address to geocode

**Optional Fields:**
- `city` (string): City name
- `state` (string): State name
- `pincode` (string): Postal code
- `country` (string): Country name (defaults to "India")

**Response:**
```json
{
  "success": true,
  "data": {
    "digipin": "ABC-DEF-1234",
    "latitude": 28.6139,
    "longitude": 77.2090,
    "address": "123 Main Street, New Delhi, Delhi, 110001, India"
  }
}
```

---

### Reverse Geocode

**POST** `/api/reverse-geocode`

Reverse geocode a DigiPin code to get coordinates and address.

**Request Body:**
```json
{
  "digipin": "ABC-DEF-1234"
}
```

**Required Fields:**
- `digipin` (string): DigiPin code (format: XXX-XXX-XXXX)

**Response:**
```json
{
  "success": true,
  "data": {
    "digipin": "ABC-DEF-1234",
    "latitude": 28.6139,
    "longitude": 77.2090,
    "address": "123 Main Street, New Delhi, Delhi, 110001, India"
  }
}
```

---

### Coordinates to DigiPin

**POST** `/api/coordinates-to-digipin`

Convert latitude and longitude coordinates to a DigiPin code.

**Request Body:**
```json
{
  "latitude": 28.6139,
  "longitude": 77.2090
}
```

**Required Fields:**
- `latitude` (number): Latitude coordinate (-90 to 90)
- `longitude` (number): Longitude coordinate (-180 to 180)

**Response:**
```json
{
  "success": true,
  "data": {
    "digipin": "ABC-DEF-1234",
    "latitude": 28.6139,
    "longitude": 77.2090
  }
}
```

---

### Validate DigiPin

**GET** `/api/validate-digipin?digipin=ABC-DEF-1234`

**POST** `/api/validate-digipin`

Validate a DigiPin format and check if it corresponds to a real location.

**GET Request:**
- Query parameter: `digipin` (string)

**POST Request Body:**
```json
{
  "digipin": "ABC-DEF-1234"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "valid": true,
    "digipin": "ABC-DEF-1234",
    "exists": true
  }
}
```

---

### Batch Geocode

**POST** `/api/batch-geocode`

Geocode multiple addresses in a single request (up to 100 addresses).

**Request Body:**
```json
{
  "addresses": [
    {
      "address": "123 Main Street, New Delhi",
      "city": "New Delhi",
      "state": "Delhi"
    },
    {
      "address": "456 Park Avenue, Mumbai",
      "city": "Mumbai",
      "state": "Maharashtra"
    }
  ]
}
```

**Required Fields:**
- `addresses` (array): Array of address objects (1-100 addresses)

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "digipin": "ABC-DEF-1234",
      "latitude": 28.6139,
      "longitude": 77.2090,
      "address": "123 Main Street, New Delhi, Delhi, 110001, India"
    },
    {
      "digipin": "XYZ-ABC-5678",
      "latitude": 19.0760,
      "longitude": 72.8777,
      "address": "456 Park Avenue, Mumbai, Maharashtra, 400001, India"
    }
  ]
}
```

---

### Autocomplete

**GET** `/api/autocomplete?q=New Delhi&limit=5`

Get address autocomplete suggestions.

**Query Parameters:**
- `q` (string, required): Search query (minimum 3 characters)
- `limit` (number, optional): Maximum number of suggestions (default: 5, max: 10)

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "address": "New Delhi, Delhi, India",
      "digipin": "ABC-DEF-1234"
    },
    {
      "address": "New Delhi Railway Station, New Delhi, Delhi, India",
      "digipin": "XYZ-ABC-5678"
    }
  ]
}
```

---

### Lookup Location from Coordinates

**POST** `/api/lookup-location-from-coordinates`

Get administrative boundaries (pincode, state, division, locality) from coordinates.

**Request Body:**
```json
{
  "latitude": 28.6139,
  "longitude": 77.2090
}
```

**Required Fields:**
- `latitude` (number): Latitude coordinate (-90 to 90)
- `longitude` (number): Longitude coordinate (-180 to 180)

**Response:**
```json
{
  "success": true,
  "data": {
    "pincode": "110001",
    "state": "Delhi",
    "division": "New Delhi Central",
    "locality": "Connaught Place",
    "district": "New Delhi",
    "latitude": 28.6139,
    "longitude": 77.2090
  }
}
```

---

### Lookup Location from DigiPin

**POST** `/api/lookup-location-from-digipin`

Get administrative boundaries from a DigiPin code.

**Request Body:**
```json
{
  "digipin": "ABC-DEF-1234"
}
```

**Required Fields:**
- `digipin` (string): DigiPin code (format: XXX-XXX-XXXX)

**Response:**
```json
{
  "success": true,
  "data": {
    "pincode": "110001",
    "state": "Delhi",
    "division": "New Delhi Central",
    "locality": "Connaught Place",
    "district": "New Delhi",
    "digipin": "ABC-DEF-1234"
  }
}
```

---

### Batch Location Lookup

**POST** `/api/batch-location-lookup`

Batch lookup for multiple locations (up to 100 locations). Each location can be specified by coordinates or DigiPin.

**Request Body:**
```json
{
  "locations": [
    {
      "latitude": 28.6139,
      "longitude": 77.2090
    },
    {
      "digipin": "ABC-DEF-1234"
    }
  ]
}
```

**Required Fields:**
- `locations` (array): Array of location objects (1-100 locations)
  - Each object must have either `latitude` + `longitude` OR `digipin`

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "pincode": "110001",
      "state": "Delhi",
      "division": "New Delhi Central",
      "locality": "Connaught Place",
      "district": "New Delhi",
      "latitude": 28.6139,
      "longitude": 77.2090
    },
    {
      "pincode": "110001",
      "state": "Delhi",
      "division": "New Delhi Central",
      "locality": "Connaught Place",
      "district": "New Delhi",
      "digipin": "ABC-DEF-1234"
    }
  ]
}
```

---

### Find Nearby Boundaries

**POST** `/api/find-nearby-boundaries`

Find nearby postal boundaries within a specified radius.

**Request Body:**
```json
{
  "latitude": 28.6139,
  "longitude": 77.2090,
  "radius_km": 5.0,
  "limit": 10
}
```

**Required Fields:**
- `latitude` (number): Center latitude (-90 to 90)
- `longitude` (number): Center longitude (-180 to 180)

**Optional Fields:**
- `radius_km` (number): Search radius in kilometers (default: 5.0, max: 100)
- `limit` (number): Maximum number of results (default: 10, max: 50)

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "pincode": "110001",
      "state": "Delhi",
      "division": "New Delhi Central",
      "locality": "Connaught Place",
      "distance_km": 0.5
    },
    {
      "pincode": "110002",
      "state": "Delhi",
      "division": "New Delhi Central",
      "locality": "Karol Bagh",
      "distance_km": 2.3
    }
  ]
}
```

---

### Get Usage Statistics

**GET** `/api/usage`

Get API usage statistics and quota information.

**Response:**
```json
{
  "success": true,
  "data": {
    "requests_today": 150,
    "requests_limit": 1000,
    "remaining_requests": 850,
    "quota_reset": "2024-01-02T00:00:00Z"
  }
}
```

---

### Get Location Statistics

**GET** `/api/location-statistics`

Get live statistics about the Location Lookup service.

**Response:**
```json
{
  "success": true,
  "data": {
    "total_boundaries": 36000,
    "states": 36,
    "divisions": 500,
    "localities": 15000
  }
}
```

---

## Error Responses

All endpoints return errors in the following format:

```json
{
  "success": false,
  "error": "Error message describing what went wrong"
}
```

### Common Error Codes

- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Invalid or missing API key
- `429 Too Many Requests`: Rate limit exceeded
- `404 Not Found`: Endpoint not found
- `500 Internal Server Error`: Server error

---

## CORS

The API supports CORS and can be accessed from web applications. The following headers are allowed:

- `Content-Type`
- `Authorization`
- `x-api-key`

---

## Rate Limiting

Rate limiting is enforced by the QuantaRoute API. Check the `usage` endpoint to see your current usage and limits.

---

## Examples

### JavaScript/TypeScript (Fetch API)

```javascript
// Geocode an address
const response = await fetch('https://mcp-gc.quantaroute.com/api/geocode', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'x-api-key': 'your-api-key-here'
  },
  body: JSON.stringify({
    address: '123 Main Street, New Delhi',
    city: 'New Delhi',
    state: 'Delhi'
  })
});

const data = await response.json();
console.log(data);
```

### cURL

```bash
# Geocode an address
curl -X POST https://mcp-gc.quantaroute.com/api/geocode \
  -H "Content-Type: application/json" \
  -H "x-api-key: your-api-key-here" \
  -d '{
    "address": "123 Main Street, New Delhi",
    "city": "New Delhi",
    "state": "Delhi"
  }'

# Autocomplete
curl -X GET "https://mcp-gc.quantaroute.com/api/autocomplete?q=New Delhi&limit=5" \
  -H "x-api-key: your-api-key-here"
```

### React Native

```javascript
import axios from 'axios';

const api = axios.create({
  baseURL: 'https://mcp-gc.quantaroute.com/api',
  headers: {
    'Content-Type': 'application/json',
    'x-api-key': 'your-api-key-here'
  }
});

// Geocode an address
const geocodeAddress = async (address) => {
  try {
    const response = await api.post('/geocode', {
      address: address,
      country: 'India'
    });
    return response.data;
  } catch (error) {
    console.error('Geocoding error:', error.response?.data || error.message);
    throw error;
  }
};
```

---

## Deployment

### Vercel Deployment

1. **Install Vercel CLI** (if not already installed):
   ```bash
   npm i -g vercel
   ```

2. **Deploy to Vercel**:
   ```bash
   vercel
   ```

3. **Set Environment Variable** (Optional):
   ```bash
   vercel env add QUANTAROUTE_API_KEY
   ```
   Enter your API key when prompted. This is optional - users can provide their own API keys via the `x-api-key` header.

4. **Configure Custom Domain** (Recommended):
   - Add `mcp-gc.quantaroute.com` as custom domain in Vercel project settings
   - Configure DNS CNAME record pointing to Vercel
   - Wait for DNS propagation and SSL certificate

5. **Deploy to Production**:
   ```bash
   vercel --prod
   ```

### Environment Variables

Set the following environment variable in your Vercel project (optional):

- `QUANTAROUTE_API_KEY`: Your QuantaRoute API key (optional fallback)

**Important Notes**:
- **Users provide their own API keys**: Clients should provide their API key via the `x-api-key` header. Get API keys from [developers.quantaroute.com](https://developers.quantaroute.com).
- **Environment variable is optional**: The `QUANTAROUTE_API_KEY` environment variable is only used as a fallback when no `x-api-key` header is provided.
- **Priority**: Request header (`x-api-key`) takes precedence over environment variable.
- **Usage tracking**: Each user's API key usage is tracked separately by the backend API.

---

## Support

- **API Documentation**: https://api.quantaroute.com/v1/digipin/docs
- **GitHub**: https://github.com/mapdevsaikat/quantaroute-geocoder
- **Website**: https://quantaroute.com

---

## License

MIT License

