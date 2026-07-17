FROM python:3.11-slim

WORKDIR /app

# Copy source and install
COPY pyproject.toml README.md ./
COPY src/ src/
RUN pip install --no-cache-dir .

# Default: streamable HTTP transport
ENV TRANSPORT=streamable-http
ENV HOST=0.0.0.0
ENV PORT=8080

EXPOSE 8080

CMD ["sh", "-c", "youfiliate-mcp --transport $TRANSPORT --host $HOST --port $PORT"]
