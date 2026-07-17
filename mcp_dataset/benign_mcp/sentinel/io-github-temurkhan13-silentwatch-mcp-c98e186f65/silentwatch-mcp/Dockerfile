# Dockerfile — silentwatch-mcp
#
# Build: docker build -t silentwatch-mcp .
# Run:   docker run -i silentwatch-mcp
#
# The MCP server speaks stdio JSON-RPC. Pipe MCP messages on stdin; receive responses on stdout.

FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml README.md LICENSE ./
COPY src/ ./src/

RUN pip install --no-cache-dir .

ENTRYPOINT ["silentwatch-mcp"]
