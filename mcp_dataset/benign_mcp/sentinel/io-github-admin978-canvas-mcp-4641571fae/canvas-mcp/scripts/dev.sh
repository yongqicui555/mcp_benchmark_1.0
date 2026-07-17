#!/usr/bin/env bash
# Run canvas-local-mcp with secrets injected from Bitwarden Secrets Manager.
# Prefix CANVAS_ in BWS is stripped → app sees CANVAS_BASE_URL, CANVAS_TOKEN.
set -e
exec ~/scripts/bws-run-with-prefix.sh \
  BWS_TOKEN_CLIENT_CANVAS_MCP \
  BWS_PROJECT_CLIENT_CANVAS_MCP \
  CANVAS_ \
  -- canvas-local-mcp "$@"
