import type { VercelRequest, VercelResponse } from '@vercel/node';

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
  // Handle CORS preflight
  if (handleCors(req, res)) {
    return;
  }

  // Only handle GET requests for root endpoint
  if (req.method !== 'GET') {
    return sendJson(res, 405, {
      success: false,
      error: 'Method not allowed',
      message: 'Only GET method is allowed for /api endpoint',
    });
  }

  // Return API documentation
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

