---
title: "Production-Hardened MCP Memory Server with Hybrid Search and Circuit Breaker"
published: false
description: "MindCore Memory — an MCP server that gives AI agents persistent, production-grade memory with BM25+FAISS hybrid search, circuit breaker protection, and BND boundary evaluation."
tags: mcp, memory, ai, python, opensource
---

## The Problem: AI Agents Have No Memory

Every time you start a new conversation with Claude, Cursor, or any AI coding agent — it forgets everything. Your project context, your preferences, yesterday's bug fix — all gone.

## The Solution: MindCore Memory MCP

MindCore Memory is an MCP (Model Context Protocol) server that gives AI agents **persistent, production-grade long-term memory**.

### What Makes It Different

**1. Hybrid Search (BM25 + FAISS)**
Keyword precision meets semantic understanding. Exact matches don't get lost, and conceptual searches still work.

**2. Circuit Breaker Protection**
If FAISS or embedding operations fail, the circuit breaker prevents cascading failures. Your agent keeps running.

**3. SLO Tracking**
Every operation tracks P95 latency. You know exactly how fast your memory system is.

**4. BND Boundary Evaluation (专利级)**
Based on the Dualistic Evolution Algorithm (DEA), every memory write goes through 4D scoring: Trajectory, Evolution, Cognition, and Balance. The system learns what's worth remembering.

**5. Optional Encryption**
Fernet-based content encryption for PII protection. Enterprise-ready.

### Quick Start

```bash
pip install mindcore-memory
mindcore-memory
```

Add to your MCP client:

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

### Available Tools

| Tool | Purpose |
|------|---------|
| `memory_store` | Store memories with importance scoring (1-4) |
| `memory_recall` | Semantic search with tag/session filters |
| `memory_context` | Build context window for LLM input |
| `memory_update_confidence` | Correct and refine memory confidence |
| `memory_stats` | View memory statistics |
| `memory_delete` | Remove memories |

### Production Ready

- ✅ 118 tests passing
- ✅ CI/CD pipeline (GitHub Actions)
- ✅ Published on PyPI
- ✅ MCP Registry ready
- ✅ MIT License

## Links

- GitHub: https://github.com/woshilaohei/mindcore-memory-mcp
- PyPI: https://pypi.org/project/mindcore-memory/
- Documentation: https://woshilaohei.github.io/mindcore-memory-mcp/
