# Deployment Guide

This guide explains how to deploy the QuantaRoute Geocoder REST API to Vercel.

## Prerequisites

1. **Vercel Account**: Sign up at [vercel.com](https://vercel.com)
2. **Vercel CLI** (optional): Install globally with `npm i -g vercel`
3. **QuantaRoute API Key**: Get your API key from [developers.quantaroute.com](https://developers.quantaroute.com)

## Deployment Steps

### Option 1: Deploy via Vercel CLI

1. **Install Vercel CLI** (if not already installed):
   ```bash
   npm i -g vercel
   ```

2. **Login to Vercel**:
   ```bash
   vercel login
   ```

3. **Deploy to Vercel**:
   ```bash
   cd /path/to/mcp-server
   vercel
   ```

4. **Set Environment Variable**:
   ```bash
   vercel env add QUANTAROUTE_API_KEY
   ```
   Enter your QuantaRoute API key when prompted.

5. **Deploy to Production**:
   ```bash
   vercel --prod
   ```

### Option 2: Deploy via Vercel Dashboard

1. **Push to GitHub**:
   - Push your code to a GitHub repository

2. **Import Project in Vercel**:
   - Go to [vercel.com/new](https://vercel.com/new)
   - Import your GitHub repository
   - Vercel will auto-detect the project settings

3. **Configure Environment Variables**:
   - Go to Project Settings → Environment Variables
   - Add `QUANTAROUTE_API_KEY` with your API key value
   - Select all environments (Production, Preview, Development)

4. **Deploy**:
   - Click "Deploy" button
   - Wait for deployment to complete

## Environment Variables

### Required

- `QUANTAROUTE_API_KEY`: Your QuantaRoute API key

### Optional

- None (all configuration is handled via environment variables or request headers)

## API Usage

Once deployed and configured with custom domain, your API will be available at:

```
https://mcp-gc.quantaroute.com/api
```

**Note**: `mcp-gc` stands for MCP Geocoding. Configure the custom domain `mcp-gc.quantaroute.com` in Vercel project settings.

### Example Request

```bash
curl -X POST https://mcp-gc.quantaroute.com/api/geocode \
  -H "Content-Type: application/json" \
  -H "x-api-key: your-api-key" \
  -d '{
    "address": "123 Main Street, New Delhi",
    "city": "New Delhi",
    "state": "Delhi"
  }'
```

## Custom Domain

To use the custom domain `mcp-gc.quantaroute.com`:

1. **DNS Configuration**: Add a CNAME record in your DNS provider:
   ```
   Type: CNAME
   Name: mcp-gc
   Value: (Vercel will provide - usually cname.vercel-dns.com)
   TTL: Auto or 3600
   ```

2. **Vercel Configuration**:
   - Go to your Vercel project settings
   - Navigate to "Domains"
   - Add `mcp-gc.quantaroute.com`
   - Follow the DNS configuration instructions provided by Vercel

3. **Wait for DNS Propagation**: Usually 5-30 minutes

4. **Verify SSL**: Vercel automatically provisions SSL certificates

**Domain Naming Convention**:
- `mcp-gc.quantaroute.com` - Geocoding MCP Server (this project)
- `mcp-re.quantaroute.com` - Routing Engine MCP Server (future)

## Monitoring

### Vercel Dashboard

- View deployment logs in the Vercel dashboard
- Monitor function execution time and errors
- Check API usage and performance

### API Health Check

Check API health:

```bash
curl https://mcp-gc.quantaroute.com/api/health
```

## Troubleshooting

### Deployment Issues

1. **Build Failures**:
   - Check that all dependencies are in `package.json`
   - Verify TypeScript compilation succeeds locally
   - Check Vercel build logs for specific errors

2. **Function Timeout**:
   - Vercel serverless functions have a timeout limit
   - Check function execution time in Vercel dashboard
   - Optimize API calls if needed

3. **Environment Variables**:
   - Verify `QUANTAROUTE_API_KEY` is set correctly
   - Check that it's available in the correct environment (Production/Preview)
   - Re-deploy after adding environment variables

### Runtime Issues

1. **Authentication Errors**:
   - Verify API key is correct
   - Check that API key is set in environment variables
   - Ensure `x-api-key` header is sent correctly in requests

2. **CORS Issues**:
   - CORS is enabled by default for all origins
   - If you need to restrict CORS, modify `corsHeaders` in `api/[...path].ts`

3. **Rate Limiting**:
   - Check API usage via `/api/usage` endpoint
   - Verify you're within your QuantaRoute API quota
   - Consider implementing client-side rate limiting

## Local Development

To test locally before deploying:

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Set environment variable**:
   ```bash
   export QUANTAROUTE_API_KEY=your-api-key
   ```

3. **Run Vercel dev server**:
   ```bash
   vercel dev
   ```

4. **Test API**:
   ```bash
   curl http://localhost:3000/api/health
   ```

   **Note**: When deployed with custom domain, use `https://mcp-gc.quantaroute.com/api/health`

## Production Best Practices

1. **API Key Security**:
   - Never commit API keys to version control
   - Use environment variables for all secrets
   - Rotate API keys regularly

2. **Rate Limiting**:
   - Implement client-side rate limiting
   - Monitor API usage via `/api/usage` endpoint
   - Set up alerts for high usage

3. **Error Handling**:
   - Implement proper error handling in client applications
   - Log errors for debugging
   - Provide meaningful error messages to users

4. **Monitoring**:
   - Set up monitoring and alerts
   - Track API usage and performance
   - Monitor error rates

## Support

For issues or questions:

- **GitHub Issues**: https://github.com/mapdevsaikat/quantaroute-geocoder/issues
- **API Documentation**: See [API.md](./API.md)
- **QuantaRoute Support**: https://quantaroute.com

