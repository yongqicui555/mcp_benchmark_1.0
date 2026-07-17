import type { VercelRequest, VercelResponse } from '@vercel/node';
// Import client from lib directory (Vercel can access this)
import { QuantaRouteClient } from '../lib/client.js';

// CORS headers
const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization, x-api-key',
  'Content-Type': 'application/json',
};

// Helper to send JSON response
function sendJson(res: VercelResponse, status: number, data: any) {
  Object.entries(corsHeaders).forEach(([key, value]) => {
    res.setHeader(key, value);
  });
  res.status(status).json(data);
}

// Helper to handle errors
function handleError(res: VercelResponse, error: any, status: number = 500) {
  console.error('API Error:', error);
  
  // Determine status code from error message
  if (error.message?.includes('Authentication failed')) {
    status = 401;
  } else if (error.message?.includes('Rate limit exceeded')) {
    status = 429;
  } else if (error.message?.includes('required') || error.message?.includes('must be')) {
    status = 400;
  }
  
  sendJson(res, status, {
    error: error.message || 'Internal server error',
    success: false,
  });
}

// Get API key from request headers or environment
function getApiKey(req: VercelRequest): string {
  // Priority: Request header > Environment variable
  const headerKey = req.headers['x-api-key'] as string;
  const envKey = process.env.QUANTAROUTE_API_KEY;
  
  if (headerKey) {
    return headerKey;
  }
  
  if (envKey) {
    return envKey;
  }
  
  throw new Error('API key is required. Set QUANTAROUTE_API_KEY environment variable or provide x-api-key header');
}

// Create client instance with API key
function createClient(req: VercelRequest): QuantaRouteClient {
  const apiKey = getApiKey(req);
  return new QuantaRouteClient(apiKey);
}

// Handle CORS preflight
function handleCors(req: VercelRequest, res: VercelResponse): boolean {
  if (req.method === 'OPTIONS') {
    Object.entries(corsHeaders).forEach(([key, value]) => {
      res.setHeader(key, value);
    });
    res.status(200).end();
    return true;
  }
  return false;
}

export default async function handler(req: VercelRequest, res: VercelResponse) {
  // Debug: Log that function was called
  console.log('=== FUNCTION CALLED ===');
  console.log('Method:', req.method);
  console.log('URL:', req.url);
  console.log('Query:', JSON.stringify(req.query));
  console.log('Headers:', JSON.stringify(req.headers));
  
  // Handle CORS preflight
  if (handleCors(req, res)) {
    return;
  }

  const { method, query, body, url } = req;
  
  // Debug logging (remove in production if needed)
  console.log('Request URL:', url);
  console.log('Query params:', JSON.stringify(query));
  
  // Handle both array and string path formats
  let path: string[] = [];
  if (Array.isArray(query.path)) {
    path = query.path;
  } else if (typeof query.path === 'string') {
    path = query.path ? query.path.split('/').filter(Boolean) : [];
  }
  
  // If path is empty or undefined, try to extract from URL
  if ((!path || path.length === 0) && url) {
    try {
      const urlPath = new URL(url, 'http://localhost').pathname;
      // Remove /api prefix and split
      const cleanPath = urlPath.startsWith('/api') ? urlPath.substring(4) : urlPath;
      const parts = cleanPath.split('/').filter(Boolean);
      path = parts;
    } catch (e) {
      // If URL parsing fails, treat as root
      path = [];
    }
  }
  
  const endpoint = path && path.length > 0 ? path[0] : '';
  
  // Debug: Log the parsed endpoint
  console.log('Parsed endpoint:', endpoint);
  console.log('Path array:', JSON.stringify(path));

  try {
    // Root endpoint - show API documentation (no API key required)
    // Check if endpoint is empty OR if URL is exactly /api
    const isRootEndpoint = (endpoint === '' || endpoint === undefined) && method === 'GET';
    if (isRootEndpoint) {
      return sendJson(res, 200, {
        success: true,
        message: 'QuantaRoute Geocoder REST API',
        version: '1.0.0',
        documentation: 'https://github.com/mapdevsaikat/quantaroute-geocoder',
        authentication: {
          method: 'API Key',
          header: 'x-api-key',
          env: 'QUANTAROUTE_API_KEY',
          note: 'API key can be provided via x-api-key header or QUANTAROUTE_API_KEY environment variable. Get your API key from https://developers.quantaroute.com',
          getApiKey: 'https://developers.quantaroute.com',
        },
        endpoints: {
          'GET /api': 'Get API information (this endpoint)',
          'GET /api/health': 'Health check',
          'GET /api/usage': 'Get API usage statistics',
          'GET /api/location-statistics': 'Get location lookup statistics',
          'GET /api/autocomplete?q=query&limit=5': 'Get address autocomplete suggestions',
          'GET /api/validate-digipin?digipin=XXX-XXX-XXXX': 'Validate DigiPin format',
          'POST /api/geocode': 'Geocode an address',
          'POST /api/reverse-geocode': 'Reverse geocode a DigiPin',
          'POST /api/coordinates-to-digipin': 'Convert coordinates to DigiPin',
          'POST /api/validate-digipin': 'Validate DigiPin format',
          'POST /api/batch-geocode': 'Geocode multiple addresses',
          'POST /api/lookup-location-from-coordinates': 'Get location details from coordinates',
          'POST /api/lookup-location-from-digipin': 'Get location details from DigiPin',
          'POST /api/batch-location-lookup': 'Batch location lookup',
          'POST /api/find-nearby-boundaries': 'Find nearby postal boundaries (NOT YET IMPLEMENTED - Coming Soon)',
        },
      });
    }

    // Create client instance with API key from request or environment
    const client = createClient(req);

    // Health check
    if (endpoint === 'health' && method === 'GET') {
      const result = await client.getHealth();
      return sendJson(res, 200, { success: true, data: result });
    }

    // Get usage statistics
    if (endpoint === 'usage' && method === 'GET') {
      const result = await client.getUsage();
      return sendJson(res, 200, { success: true, data: result });
    }

    // Get location statistics
    if (endpoint === 'location-statistics' && method === 'GET') {
      const result = await client.getLocationStatistics();
      return sendJson(res, 200, { success: true, data: result });
    }

    // Geocode
    if (endpoint === 'geocode' && method === 'POST') {
      if (!body || !body.address) {
        return sendJson(res, 400, {
          success: false,
          error: 'Address is required',
        });
      }
      const result = await client.geocode(body);
      return sendJson(res, 200, { success: true, data: result });
    }

    // Reverse geocode
    if (endpoint === 'reverse-geocode' && method === 'POST') {
      if (!body || !body.digipin) {
        return sendJson(res, 400, {
          success: false,
          error: 'DigiPin is required',
        });
      }
      const result = await client.reverseGeocode(body.digipin);
      return sendJson(res, 200, { success: true, data: result });
    }

    // Coordinates to DigiPin
    if (endpoint === 'coordinates-to-digipin' && method === 'POST') {
      if (typeof body?.latitude !== 'number' || typeof body?.longitude !== 'number') {
        return sendJson(res, 400, {
          success: false,
          error: 'Latitude and longitude are required and must be numbers',
        });
      }
      if (body.latitude < -90 || body.latitude > 90) {
        return sendJson(res, 400, {
          success: false,
          error: 'Latitude must be between -90 and 90',
        });
      }
      if (body.longitude < -180 || body.longitude > 180) {
        return sendJson(res, 400, {
          success: false,
          error: 'Longitude must be between -180 and 180',
        });
      }
      const result = await client.coordinatesToDigiPin(body.latitude, body.longitude);
      return sendJson(res, 200, { success: true, data: result });
    }

    // Validate DigiPin (GET method with query parameter)
    if (endpoint === 'validate-digipin') {
      if (method === 'GET') {
        const digipin = query.digipin as string;
        if (!digipin) {
          return sendJson(res, 400, {
            success: false,
            error: 'DigiPin query parameter is required',
          });
        }
        const result = await client.validateDigiPin(digipin);
        return sendJson(res, 200, { success: true, data: result });
      }
      // Also support POST for consistency
      if (method === 'POST') {
        if (!body || !body.digipin) {
          return sendJson(res, 400, {
            success: false,
            error: 'DigiPin is required',
          });
        }
        const result = await client.validateDigiPin(body.digipin);
        return sendJson(res, 200, { success: true, data: result });
      }
    }

    // Batch geocode
    if (endpoint === 'batch-geocode' && method === 'POST') {
      if (!body || !Array.isArray(body.addresses) || body.addresses.length === 0) {
        return sendJson(res, 400, {
          success: false,
          error: 'Addresses must be a non-empty array',
        });
      }
      if (body.addresses.length > 100) {
        return sendJson(res, 400, {
          success: false,
          error: 'Maximum 100 addresses allowed per batch',
        });
      }
      const result = await client.batchGeocode(body.addresses);
      return sendJson(res, 200, { success: true, data: result });
    }

    // Autocomplete
    if (endpoint === 'autocomplete' && method === 'GET') {
      const queryParam = req.query.q as string;
      const limit = req.query.limit ? parseInt(req.query.limit as string, 10) : 5;
      
      if (!queryParam || queryParam.length < 3) {
        return sendJson(res, 400, {
          success: false,
          error: 'Query parameter "q" must be at least 3 characters long',
        });
      }
      if (limit > 10) {
        return sendJson(res, 400, {
          success: false,
          error: 'Limit cannot exceed 10',
        });
      }
      const result = await client.autocomplete(queryParam, limit);
      return sendJson(res, 200, { success: true, data: result });
    }

    // Lookup location from coordinates
    if (endpoint === 'lookup-location-from-coordinates' && method === 'POST') {
      if (typeof body?.latitude !== 'number' || typeof body?.longitude !== 'number') {
        return sendJson(res, 400, {
          success: false,
          error: 'Latitude and longitude are required and must be numbers',
        });
      }
      if (body.latitude < -90 || body.latitude > 90) {
        return sendJson(res, 400, {
          success: false,
          error: 'Latitude must be between -90 and 90',
        });
      }
      if (body.longitude < -180 || body.longitude > 180) {
        return sendJson(res, 400, {
          success: false,
          error: 'Longitude must be between -180 and 180',
        });
      }
      const result = await client.lookupLocationFromCoordinates(body.latitude, body.longitude);
      return sendJson(res, 200, { success: true, data: result });
    }

    // Lookup location from DigiPin
    if (endpoint === 'lookup-location-from-digipin' && method === 'POST') {
      if (!body || !body.digipin) {
        return sendJson(res, 400, {
          success: false,
          error: 'DigiPin is required',
        });
      }
      const result = await client.lookupLocationFromDigiPin(body.digipin);
      return sendJson(res, 200, { success: true, data: result });
    }

    // Batch location lookup
    if (endpoint === 'batch-location-lookup' && method === 'POST') {
      if (!body || !Array.isArray(body.locations) || body.locations.length === 0) {
        return sendJson(res, 400, {
          success: false,
          error: 'Locations must be a non-empty array',
        });
      }
      if (body.locations.length > 100) {
        return sendJson(res, 400, {
          success: false,
          error: 'Maximum 100 locations allowed per batch',
        });
      }
      const result = await client.batchLocationLookup(body.locations);
      return sendJson(res, 200, { success: true, data: result });
    }

    // Find nearby boundaries - NOT YET IMPLEMENTED IN BACKEND
    // TODO: Implement /v1/location/nearby endpoint in backend API
    // The backend endpoint /v1/location/nearby does not exist yet
    if (endpoint === 'find-nearby-boundaries' && method === 'POST') {
      return sendJson(res, 501, {
        success: false,
        error: 'Not Implemented',
        message: 'The find-nearby-boundaries endpoint is not yet implemented in the backend API. This feature is coming soon.',
        endpoint: 'find-nearby-boundaries',
        status: 'experimental',
        note: 'This feature is marked as experimental and will be available in a future release. The backend endpoint /v1/location/nearby needs to be implemented first.'
      });
    }
    
    /* Original implementation - Commented out until backend endpoint /v1/location/nearby is implemented
    if (endpoint === 'find-nearby-boundaries' && method === 'POST') {
      if (typeof body?.latitude !== 'number' || typeof body?.longitude !== 'number') {
        return sendJson(res, 400, {
          success: false,
          error: 'Latitude and longitude are required and must be numbers',
        });
      }
      if (body.latitude < -90 || body.latitude > 90) {
        return sendJson(res, 400, {
          success: false,
          error: 'Latitude must be between -90 and 90',
        });
      }
      if (body.longitude < -180 || body.longitude > 180) {
        return sendJson(res, 400, {
          success: false,
          error: 'Longitude must be between -180 and 180',
        });
      }
      const radius_km = typeof body.radius_km === 'number' ? body.radius_km : 5.0;
      const limit = typeof body.limit === 'number' ? body.limit : 10;
      
      if (radius_km > 100) {
        return sendJson(res, 400, {
          success: false,
          error: 'Radius cannot exceed 100 km',
        });
      }
      if (limit > 50) {
        return sendJson(res, 400, {
          success: false,
          error: 'Limit cannot exceed 50',
        });
      }
      
      const result = await client.findNearbyBoundaries(body.latitude, body.longitude, radius_km, limit);
      return sendJson(res, 200, { success: true, data: result });
    }
    */

    // Unknown endpoint
    return sendJson(res, 404, {
      success: false,
      error: `Endpoint '${endpoint}' not found`,
      message: 'See GET /api for available endpoints',
      endpoint: endpoint || '(root)',
      method: method,
      availableEndpoints: [
        'GET /api',
        'GET /api/health',
        'GET /api/usage',
        'GET /api/location-statistics',
        'GET /api/autocomplete?q=query&limit=5',
        'GET /api/validate-digipin?digipin=XXX-XXX-XXXX',
        'POST /api/geocode',
        'POST /api/reverse-geocode',
        'POST /api/coordinates-to-digipin',
        'POST /api/validate-digipin',
        'POST /api/batch-geocode',
        'POST /api/lookup-location-from-coordinates',
        'POST /api/lookup-location-from-digipin',
        'POST /api/batch-location-lookup',
        'POST /api/find-nearby-boundaries (NOT YET IMPLEMENTED)',
      ],
    });
  } catch (error: any) {
    handleError(res, error);
  }
}
