import axios, { AxiosInstance } from 'axios';

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

export class QuantaRouteClient {
  private client: AxiosInstance;
  private apiKey: string;
  private baseUrl: string;

  constructor(apiKey?: string, baseUrl: string = 'https://api.quantaroute.com') {
    this.apiKey = apiKey || process.env.QUANTAROUTE_API_KEY || '';
    this.baseUrl = baseUrl;
    
    this.client = axios.create({
      baseURL: this.baseUrl,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
        'User-Agent': '@quantaroute/mcp-server/1.0.0',
      },
    });

    // Set API key interceptor if provided
    if (this.apiKey) {
      this.client.interceptors.request.use((config) => {
        config.headers['x-api-key'] = this.apiKey;
        return config;
      });
    }
  }

  private async makeRequest(method: 'GET' | 'POST', endpoint: string, data?: any, params?: any) {
    try {
      const response = await this.client.request({
        method,
        url: endpoint,
        data,
        params,
      });
      return response.data;
    } catch (error: any) {
      if (error.response) {
        const status = error.response.status;
        const message = error.response.data?.message || error.message;
        
        if (status === 401) {
          throw new Error(`Authentication failed: ${message}`);
        }
        if (status === 429) {
          throw new Error(`Rate limit exceeded: ${message}`);
        }
        throw new Error(`API error (${status}): ${message}`);
      }
      throw new Error(`Request failed: ${error.message}`);
    }
  }

  async geocode(params: GeocodeParams) {
    const data: any = {
      address: params.address,
      country: params.country || 'India',
    };
    if (params.city) data.city = params.city;
    if (params.state) data.state = params.state;
    if (params.pincode) data.pincode = params.pincode;

    const response = await this.makeRequest('POST', '/v1/digipin/geocode', data);
    return response.data || response;
  }

  async reverseGeocode(digipin: string) {
    const response = await this.makeRequest('POST', '/v1/digipin/reverse', { digipin });
    return response.data || response;
  }

  async coordinatesToDigiPin(latitude: number, longitude: number) {
    const response = await this.makeRequest('POST', '/v1/digipin/coordinates-to-digipin', {
      latitude,
      longitude,
    });
    return response.data || response;
  }

  async validateDigiPin(digipin: string) {
    const response = await this.makeRequest('GET', `/v1/digipin/validate/${digipin}`);
    return response.data || response;
  }

  async batchGeocode(addresses: BatchGeocodeParams['addresses']) {
    const response = await this.makeRequest('POST', '/v1/digipin/batch', { addresses });
    return response.data || response;
  }

  async autocomplete(query: string, limit: number = 5) {
    const response = await this.makeRequest('GET', '/v1/digipin/autocomplete', undefined, {
      q: query,
      limit: Math.min(limit, 10),
    });
    return response.data || response;
  }

  async lookupLocationFromCoordinates(latitude: number, longitude: number) {
    const response = await this.makeRequest('POST', '/v1/location/lookup', {
      latitude,
      longitude,
    });
    return response.data || response;
  }

  async lookupLocationFromDigiPin(digipin: string) {
    const response = await this.makeRequest('POST', '/v1/location/lookup', { digipin });
    return response.data || response;
  }

  async batchLocationLookup(locations: BatchLocationParams['locations']) {
    const response = await this.makeRequest('POST', '/v1/location/batch-lookup', { locations });
    return response.data || response;
  }

  async findNearbyBoundaries(latitude: number, longitude: number, radius_km: number = 5.0, limit: number = 10) {
    const response = await this.makeRequest('GET', '/v1/location/nearby', undefined, {
      lat: latitude,
      lng: longitude,
      radius: radius_km,
      limit: Math.min(limit, 50),
    });
    return response.data || response;
  }

  async getUsage() {
    const response = await this.makeRequest('GET', '/v1/digipin/usage');
    return response.data || response;
  }

  async getLocationStatistics() {
    const response = await this.makeRequest('GET', '/v1/location/stats');
    return response.data || response;
  }

  async getHealth() {
    const response = await this.makeRequest('GET', '/health');
    return response.data || response;
  }
}

