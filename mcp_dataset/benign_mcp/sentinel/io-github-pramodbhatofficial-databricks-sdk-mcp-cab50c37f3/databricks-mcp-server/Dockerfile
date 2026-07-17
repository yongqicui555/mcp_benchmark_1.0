FROM python:3.11-slim

WORKDIR /app

# Install package
COPY pyproject.toml README.md LICENSE ./
COPY databricks_mcp/ databricks_mcp/

RUN pip install --no-cache-dir .

# Auth is passed via environment variables:
# DATABRICKS_HOST, DATABRICKS_TOKEN (or OAuth vars)
# Tool filtering via DATABRICKS_MCP_TOOLS_INCLUDE/EXCLUDE

# Default: stdio transport
ENTRYPOINT ["databricks-mcp"]
