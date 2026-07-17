# Vercel Deployment Configuration

## Framework

This project is a **Node.js/TypeScript serverless function** project deployed on Vercel. It is NOT a static site framework.

## Project Structure

- **MCP Server**: `src/index.ts` - MCP server for AI assistants (Claude Desktop, Cursor)
- **REST API Wrapper**: `api/[...path].ts` - Serverless function for REST API endpoints
- **Client Library**: `src/client.ts` - QuantaRoute API client used by both MCP and REST API

## Vercel Configuration

The `vercel.json` configures this as a serverless function project:

```json
{
  "version": 2,
  "functions": {
    "api/**/*.ts": {
      "runtime": "@vercel/node@3.0.0"
    }
  },
  "rewrites": [
    {
      "source": "/api/(.*)",
      "destination": "/api/[...path]"
    }
  ]
}
```

## Important Notes

1. **Serverless Functions**: All API endpoints are serverless functions in the `api/` directory.
2. **Public Directory**: The `public/` directory exists only to satisfy Vercel's requirement for an output directory. It contains a simple `index.html` file.
3. **No Build Output**: Vercel compiles TypeScript automatically. The `dist/` directory is only for MCP server distribution via npx.
4. **TypeScript Compilation**: Vercel automatically compiles TypeScript files in `api/` directory.

## Deployment

1. **Install Dependencies**: Vercel runs `npm install` automatically
2. **Compile TypeScript**: Vercel compiles `api/[...path].ts` and `src/client.ts` automatically
3. **Deploy Functions**: Vercel deploys the serverless function to `/api/*` routes

## Troubleshooting

### Error: "No Output Directory named 'public' found"

**Solution**: 
- The `public/` directory has been created with a simple `index.html` file
- The `vercel.json` is configured with `"outputDirectory": "public"`
- This satisfies Vercel's requirement while still using serverless functions

### If Deployment Still Fails

1. **Verify public directory exists**: `ls -la public/`
2. **Check vercel.json**: Ensure `outputDirectory: "public"` is set
3. **Verify files are committed**: `git status public/`
4. **Check Vercel Dashboard**: Verify project settings match vercel.json

## Build Script

The `build` script in `package.json` is ONLY for building the MCP server (`dist/` directory) for distribution via npx. It is NOT used by Vercel for deployment.

Vercel automatically compiles TypeScript for serverless functions and does NOT use the `build` script.

