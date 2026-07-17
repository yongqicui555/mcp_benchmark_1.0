# Deployment Troubleshooting Guide

## Common Deployment Issues

### 1. Module Not Found Errors

**Error**: `Cannot find module '../lib/client.js'`

**Solution**:
- Ensure `lib/client.ts` exists in the repository
- Verify the file is committed to Git (not in .gitignore)
- Check that the import path in `api/[...path].ts` is correct: `import { QuantaRouteClient } from '../lib/client.js';`

**Fix**:
```bash
# Sync client file
npm run sync-client

# Verify file exists
ls -la lib/client.ts

# Commit to Git
git add lib/client.ts
git commit -m "Add lib/client.ts for Vercel deployment"
```

### 2. TypeScript Compilation Errors

**Error**: TypeScript compilation fails during Vercel build

**Solution**:
- Check that all TypeScript files compile locally: `npm run build`
- Verify `tsconfig.json` is correct
- Ensure all dependencies are in `package.json`

**Fix**:
```bash
# Test TypeScript compilation locally
npm run build

# Check for TypeScript errors
npx tsc --noEmit
```

### 3. Missing Environment Variables

**Error**: `API key is required` or authentication errors

**Solution**:
- Set `QUANTAROUTE_API_KEY` in Vercel environment variables
- Go to Vercel Dashboard → Project Settings → Environment Variables
- Add the variable for all environments (Production, Preview, Development)

**Fix**:
```bash
# Set via Vercel CLI
vercel env add QUANTAROUTE_API_KEY

# Or set in Vercel Dashboard
# Settings → Environment Variables → Add New
```

### 4. Function Timeout

**Error**: Function execution timeout

**Solution**:
- Check API response times
- Optimize API calls if needed
- Consider increasing timeout in Vercel settings (if available)

### 5. CORS Issues

**Error**: CORS errors in browser

**Solution**:
- CORS is enabled by default in the API route
- Verify CORS headers are being set correctly
- Check browser console for specific CORS errors

### 6. Build Command Issues

**Error**: Build command fails

**Solution**:
- Vercel doesn't need a build command for serverless functions
- Remove `buildCommand` from `vercel.json` if present
- Vercel compiles TypeScript automatically

### 7. Import Path Issues

**Error**: Module resolution errors

**Solution**:
- Use `.js` extension in imports for ES modules (even for TypeScript files)
- Verify import paths are correct
- Check that `package.json` has `"type": "module"`

**Correct Import**:
```typescript
import { QuantaRouteClient } from '../lib/client.js';
```

**Incorrect Import**:
```typescript
import { QuantaRouteClient } from '../lib/client'; // Missing .js extension
import { QuantaRouteClient } from '../lib/client.ts'; // Don't use .ts extension
```

## Pre-Deployment Checklist

- [ ] `lib/client.ts` exists and is committed to Git
- [ ] `api/[...path].ts` imports from `../lib/client.js`
- [ ] `vercel.json` is configured correctly
- [ ] `QUANTAROUTE_API_KEY` is set in Vercel environment variables
- [ ] All dependencies are in `package.json`
- [ ] TypeScript compiles without errors locally
- [ ] Git repository is up to date

## Testing Deployment Locally

```bash
# Install Vercel CLI
npm i -g vercel

# Test locally
vercel dev

# Test API endpoint
curl http://localhost:3000/api/health
```

## Vercel Deployment Steps

1. **Push to GitHub**:
   ```bash
   git add .
   git commit -m "Fix deployment configuration"
   git push
   ```

2. **Deploy via Vercel Dashboard**:
   - Go to Vercel Dashboard
   - Import project from GitHub
   - Set environment variables
   - Deploy

3. **Verify Deployment**:
   ```bash
   curl https://your-project.vercel.app/api/health
   ```

## Getting Help

If you're still experiencing issues:

1. Check Vercel build logs in the dashboard
2. Verify all files are committed to Git
3. Test locally with `vercel dev`
4. Check Vercel documentation: https://vercel.com/docs
5. Open an issue on GitHub: https://github.com/mapdevsaikat/quantaroute-geocoder/issues

