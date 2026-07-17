# MindCore Memory MCP

> Production-hardened MCP memory server with hybrid BM25+FAISS search, circuit breaker, and BND boundary evaluation.

## Quick Start

```bash
pip install mindcore-memory
mindcore-memory
```

## MCP Client Configuration

### Claude Desktop / Cursor / Cline

```json
{
  "mcpServers": {
    "mindcore-memory": {
      "command": "python",
      "args": ["-m", "mindcore_memory.server"]
    }
  }
}
```

## Features

### 🔍 Hybrid Search
BM25 keyword + FAISS semantic embedding = best precision + recall.

### 🛡️ Circuit Breaker
Protects against cascading failures in FAISS/embedding operations.

### 📊 SLO Tracking
P95 latency monitoring for every operation.

### 🧠 BND Boundary Evaluation
Every memory write goes through 4D scoring based on DEA (Dualistic Evolution Algorithm).

### 🔒 Encrypted Storage
Optional Fernet encryption for PII protection.

## API

### Tools
- `memory_store` — Store a memory (importance 1-4, with tags and confidence)
- `memory_recall` — Search memories by semantic query
- `memory_context` — Build a context window for LLM input
- `memory_update_confidence` — Correct a memory's confidence score
- `memory_stats` — View memory statistics
- `memory_delete` — Delete a memory

## Installation Options

```bash
# Minimal (BM25 only)
pip install mindcore-memory

# With semantic search
pip install mindcore-memory[semantic]

# With Chinese tokenization
pip install mindcore-memory[chinese]

# With encryption
pip install mindcore-memory[encrypt]

# Full install
pip install mindcore-memory[full]
```

## Links
- [GitHub](https://github.com/woshilaohei/mindcore-memory-mcp)
- [PyPI](https://pypi.org/project/mindcore-memory/)
- [MCP Registry](https://registry.modelcontextprotocol.io)
