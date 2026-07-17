#!/usr/bin/env node

/**
 * QuantaRoute Geocoder MCP Server
 * 
 * Provides MCP tools for geocoding addresses, location lookups, and DigiPin processing
 * using the QuantaRoute Geocoding API.
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  ErrorCode,
  McpError,
} from '@modelcontextprotocol/sdk/types.js';
import { QuantaRouteClient } from './client.js';

interface CoordinatesParams {
  latitude: number;
  longitude: number;
}

interface DigiPinParams {
  digipin: string;
}

interface GeocodeParams {
  address: string;
  city?: string;
  state?: string;
  pincode?: string;
  country?: string;
}

interface BatchGeocodeParams {
  addresses: Array<{
    address: string;
    city?: string;
    state?: string;
    pincode?: string;
    country?: string;
  }>;
}

interface BatchLocationParams {
  locations: Array<{
    latitude?: number;
    longitude?: number;
    digipin?: string;
  }>;
}

interface LocationLookupParams {
  latitude: number;
  longitude: number;
}

interface NearbyBoundariesParams {
  latitude: number;
  longitude: number;
  radius_km?: number;
  limit?: number;
}

// Initialize MCP server
const server = new Server(
  {
    name: '@quantaroute/mcp-server',
    version: '1.0.0',
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// Initialize client
const client = new QuantaRouteClient();

// List available tools
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: 'geocode',
        description: 'Geocode an address to get DigiPin code and coordinates. Returns location information including latitude, longitude, and DigiPin.',
        inputSchema: {
          type: 'object',
          properties: {
            address: {
              type: 'string',
              description: 'The address to geocode (required)',
            },
            city: {
              type: 'string',
              description: 'City name (optional)',
            },
            state: {
              type: 'string',
              description: 'State name (optional)',
            },
            pincode: {
              type: 'string',
              description: 'Postal code (optional)',
            },
            country: {
              type: 'string',
              description: 'Country name (optional, defaults to India)',
            },
          },
          required: ['address'],
        },
      },
      {
        name: 'reverse_geocode',
        description: 'Reverse geocode a DigiPin code to get coordinates and address information.',
        inputSchema: {
          type: 'object',
          properties: {
            digipin: {
              type: 'string',
              description: 'The DigiPin code to reverse geocode (format: XXX-XXX-XXXX)',
            },
          },
          required: ['digipin'],
        },
      },
      {
        name: 'coordinates_to_digipin',
        description: 'Convert latitude and longitude coordinates to a DigiPin code.',
        inputSchema: {
          type: 'object',
          properties: {
            latitude: {
              type: 'number',
              description: 'Latitude coordinate (-90 to 90)',
            },
            longitude: {
              type: 'number',
              description: 'Longitude coordinate (-180 to 180)',
            },
          },
          required: ['latitude', 'longitude'],
        },
      },
      {
        name: 'validate_digipin',
        description: 'Validate a DigiPin format and check if it corresponds to a real location.',
        inputSchema: {
          type: 'object',
          properties: {
            digipin: {
              type: 'string',
              description: 'The DigiPin code to validate',
            },
          },
          required: ['digipin'],
        },
      },
      {
        name: 'batch_geocode',
        description: 'Geocode multiple addresses in a single batch request (up to 100 addresses).',
        inputSchema: {
          type: 'object',
          properties: {
            addresses: {
              type: 'array',
              description: 'Array of address objects to geocode',
              items: {
                type: 'object',
                properties: {
                  address: { type: 'string' },
                  city: { type: 'string' },
                  state: { type: 'string' },
                  pincode: { type: 'string' },
                  country: { type: 'string' },
                },
                required: ['address'],
              },
              maxItems: 100,
            },
          },
          required: ['addresses'],
        },
      },
      {
        name: 'autocomplete',
        description: 'Get autocomplete suggestions for addresses (minimum 3 characters).',
        inputSchema: {
          type: 'object',
          properties: {
            query: {
              type: 'string',
              description: 'Search query (minimum 3 characters)',
            },
            limit: {
              type: 'number',
              description: 'Maximum number of suggestions (default: 5, max: 10)',
              default: 5,
            },
          },
          required: ['query'],
        },
      },
      {
        name: 'lookup_location_from_coordinates',
        description: '🚀 REVOLUTIONARY: Get administrative boundaries (pincode, state, division, locality) from coordinates. Provides precision that even government services don\'t offer.',
        inputSchema: {
          type: 'object',
          properties: {
            latitude: {
              type: 'number',
              description: 'Latitude coordinate (-90 to 90)',
            },
            longitude: {
              type: 'number',
              description: 'Longitude coordinate (-180 to 180)',
            },
          },
          required: ['latitude', 'longitude'],
        },
      },
      {
        name: 'lookup_location_from_digipin',
        description: '🚀 REVOLUTIONARY: Get administrative boundaries from a DigiPin code.',
        inputSchema: {
          type: 'object',
          properties: {
            digipin: {
              type: 'string',
              description: 'DigiPin code (format: XXX-XXX-XXXX)',
            },
          },
          required: ['digipin'],
        },
      },
      {
        name: 'batch_location_lookup',
        description: '🚀 REVOLUTIONARY: Batch lookup for multiple locations. Each location can be specified by coordinates or DigiPin (up to 100 locations).',
        inputSchema: {
          type: 'object',
          properties: {
            locations: {
              type: 'array',
              description: 'Array of location objects (each with latitude+longitude OR digipin)',
              items: {
                type: 'object',
                oneOf: [
                  {
                    properties: {
                      latitude: { type: 'number' },
                      longitude: { type: 'number' },
                    },
                    required: ['latitude', 'longitude'],
                  },
                  {
                    properties: {
                      digipin: { type: 'string' },
                    },
                    required: ['digipin'],
                  },
                ],
              },
              maxItems: 100,
            },
          },
          required: ['locations'],
        },
      },
      {
        name: 'find_nearby_boundaries',
        description: 'Find nearby postal boundaries within a specified radius (NOT YET IMPLEMENTED - Coming Soon). The backend endpoint /v1/location/nearby needs to be implemented first.',
        inputSchema: {
          type: 'object',
          properties: {
            latitude: {
              type: 'number',
              description: 'Center latitude',
            },
            longitude: {
              type: 'number',
              description: 'Center longitude',
            },
            radius_km: {
              type: 'number',
              description: 'Search radius in kilometers (default: 5.0, max: 100)',
              default: 5.0,
            },
            limit: {
              type: 'number',
              description: 'Maximum number of results (default: 10, max: 50)',
              default: 10,
            },
          },
          required: ['latitude', 'longitude'],
        },
      },
      {
        name: 'get_usage',
        description: 'Get API usage statistics and quota information.',
        inputSchema: {
          type: 'object',
          properties: {},
        },
      },
      {
        name: 'get_location_statistics',
        description: 'Get live statistics about the Location Lookup service (total boundaries, states, divisions, etc.).',
        inputSchema: {
          type: 'object',
          properties: {},
        },
      },
      {
        name: 'get_health',
        description: 'Check API health status and availability.',
        inputSchema: {
          type: 'object',
          properties: {},
        },
      },
    ],
  };
});

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  if (!args || typeof args !== 'object') {
    throw new McpError(ErrorCode.InvalidParams, 'Invalid arguments');
  }

  try {
    switch (name) {
      case 'geocode': {
        const params = args as unknown as GeocodeParams;
        if (!params.address || typeof params.address !== 'string') {
          throw new McpError(ErrorCode.InvalidParams, 'Address is required');
        }
        const result = await client.geocode(params);
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      case 'reverse_geocode': {
        const params = args as unknown as DigiPinParams;
        if (!params.digipin || typeof params.digipin !== 'string') {
          throw new McpError(ErrorCode.InvalidParams, 'DigiPin is required');
        }
        const result = await client.reverseGeocode(params.digipin);
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      case 'coordinates_to_digipin': {
        const params = args as unknown as CoordinatesParams;
        if (typeof params.latitude !== 'number' || typeof params.longitude !== 'number') {
          throw new McpError(ErrorCode.InvalidParams, 'Latitude and longitude must be numbers');
        }
        if (params.latitude < -90 || params.latitude > 90) {
          throw new McpError(ErrorCode.InvalidParams, 'Latitude must be between -90 and 90');
        }
        if (params.longitude < -180 || params.longitude > 180) {
          throw new McpError(ErrorCode.InvalidParams, 'Longitude must be between -180 and 180');
        }
        const result = await client.coordinatesToDigiPin(params.latitude, params.longitude);
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      case 'validate_digipin': {
        const params = args as unknown as DigiPinParams;
        if (!params.digipin || typeof params.digipin !== 'string') {
          throw new McpError(ErrorCode.InvalidParams, 'DigiPin is required');
        }
        const result = await client.validateDigiPin(params.digipin);
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      case 'batch_geocode': {
        const params = args as unknown as BatchGeocodeParams;
        if (!params.addresses || !Array.isArray(params.addresses) || params.addresses.length === 0) {
          throw new McpError(ErrorCode.InvalidParams, 'Addresses must be a non-empty array');
        }
        if (params.addresses.length > 100) {
          throw new McpError(ErrorCode.InvalidParams, 'Maximum 100 addresses allowed per batch');
        }
        const result = await client.batchGeocode(params.addresses);
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      case 'autocomplete': {
        const params = args as unknown as { query: string; limit?: number };
        if (!params.query || typeof params.query !== 'string' || params.query.length < 3) {
          throw new McpError(ErrorCode.InvalidParams, 'Query must be at least 3 characters long');
        }
        const result = await client.autocomplete(params.query, params.limit);
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      case 'lookup_location_from_coordinates': {
        const params = args as unknown as LocationLookupParams;
        if (typeof params.latitude !== 'number' || typeof params.longitude !== 'number') {
          throw new McpError(ErrorCode.InvalidParams, 'Latitude and longitude must be numbers');
        }
        if (params.latitude < -90 || params.latitude > 90) {
          throw new McpError(ErrorCode.InvalidParams, 'Latitude must be between -90 and 90');
        }
        if (params.longitude < -180 || params.longitude > 180) {
          throw new McpError(ErrorCode.InvalidParams, 'Longitude must be between -180 and 180');
        }
        const result = await client.lookupLocationFromCoordinates(params.latitude, params.longitude);
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      case 'lookup_location_from_digipin': {
        const params = args as unknown as DigiPinParams;
        if (!params.digipin || typeof params.digipin !== 'string') {
          throw new McpError(ErrorCode.InvalidParams, 'DigiPin is required');
        }
        const result = await client.lookupLocationFromDigiPin(params.digipin);
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      case 'batch_location_lookup': {
        const params = args as unknown as BatchLocationParams;
        if (!params.locations || !Array.isArray(params.locations) || params.locations.length === 0) {
          throw new McpError(ErrorCode.InvalidParams, 'Locations must be a non-empty array');
        }
        if (params.locations.length > 100) {
          throw new McpError(ErrorCode.InvalidParams, 'Maximum 100 locations allowed per batch');
        }
        const result = await client.batchLocationLookup(params.locations);
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      case 'find_nearby_boundaries': {
        // TODO: This endpoint is not yet implemented in the backend API
        // The backend endpoint /v1/location/nearby does not exist
        throw new McpError(
          ErrorCode.InternalError,
          'The find_nearby_boundaries feature is not yet implemented in the backend API. The endpoint /v1/location/nearby needs to be implemented first. This feature is coming soon.'
        );
        
        /* Original implementation - Commented out until backend endpoint is available
        const params = args as unknown as NearbyBoundariesParams;
        if (typeof params.latitude !== 'number' || typeof params.longitude !== 'number') {
          throw new McpError(ErrorCode.InvalidParams, 'Latitude and longitude must be numbers');
        }
        const result = await client.findNearbyBoundaries(
          params.latitude,
          params.longitude,
          params.radius_km,
          params.limit
        );
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
        */
      }

      case 'get_usage': {
        const result = await client.getUsage();
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      case 'get_location_statistics': {
        const result = await client.getLocationStatistics();
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      case 'get_health': {
        const result = await client.getHealth();
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      default:
        throw new McpError(ErrorCode.MethodNotFound, `Unknown tool: ${name}`);
    }
  } catch (error: any) {
    if (error instanceof McpError) {
      throw error;
    }
    throw new McpError(ErrorCode.InternalError, `Tool execution failed: ${error.message}`);
  }
});

// Start the server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('QuantaRoute MCP Server running on stdio');
}

main().catch((error) => {
  console.error('Fatal error in main():', error);
  process.exit(1);
});

