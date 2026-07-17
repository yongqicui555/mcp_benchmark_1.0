FROM node:20-alpine

LABEL maintainer="Summit53 <support@summit53.io>"
LABEL description="Summit53 MCP Server — 48 revenue intelligence tools for AI assistants"
LABEL org.opencontainers.image.source="https://github.com/summit53/mcp-server"

WORKDIR /app

COPY package.json ./
RUN npm install --omit=dev

COPY bin/ ./bin/
COPY server.json ./
COPY README.md ./

ENV SUMMIT53_URL=https://api.summit53.io/mcp/

# Note: OAuth flow requires a browser for first-time auth.
# For headless/Docker use, pre-authenticate locally first,
# then mount the cached token directory.
ENTRYPOINT ["node", "bin/cli.mjs"]
