"""
MindCore Memory MCP Server - v0.1.9 Production-Hardened.

Supports both stdio (local/IDE) and Streamable HTTP transports.
Both transports share the same tool registry for consistency.

Security:
- Bearer token authentication on HTTP
- Origin validation on HTTP
- Input validation via Pydantic
- No arbitrary file system access
"""

from __future__ import annotations

from typing import Any

import argparse
import json
import os
import time
import threading

import structlog
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    CallToolResult,
)

from .memory_engine import MemoryEngine
from .bnd import BNDManager
from .deduction import DeductionEngine

logger = structlog.get_logger()

# Server instance
server = Server("mindcore-memory-mcp")

# Global engine instance
_engine: MemoryEngine | None = None
_bnd_manager: BNDManager | None = None
_deduction_engine: DeductionEngine | None = None


def _get_bnd_manager() -> BNDManager:
    global _bnd_manager
    if _bnd_manager is None:
        _bnd_manager = BNDManager()
    return _bnd_manager


def _get_deduction_engine() -> DeductionEngine:
    global _deduction_engine
    if _deduction_engine is None:
        _deduction_engine = DeductionEngine()
        _deduction_engine.set_bnd_manager(_get_bnd_manager())
    return _deduction_engine

# Rate limiter (L-004 fix): token bucket
_RATE_LIMIT = 100     # max requests per window
_RATE_WINDOW = 60     # window in seconds
_rates: dict[str, list[float]] = {}
_rate_lock = threading.Lock()


def _check_rate(client_id: str = "default") -> bool:
    """Return True if within rate limit, False if exceeded."""
    now = time.time()
    with _rate_lock:
        timestamps = _rates.get(client_id, [])
        timestamps = [t for t in timestamps if now - t < _RATE_WINDOW]
        if len(timestamps) >= _RATE_LIMIT:
            _rates[client_id] = timestamps
            return False
        timestamps.append(now)
        _rates[client_id] = timestamps
        # Cleanup old entries periodically
        if len(_rates) > 1000:
            stale = [k for k, v in _rates.items() if not v or now - v[-1] > _RATE_WINDOW * 2]
            for k in stale:
                del _rates[k]
        return True


def get_engine() -> MemoryEngine:
    """Get or create the memory engine."""
    global _engine
    if _engine is None:
        storage_path = os.environ.get("MINDCORE_MEMORY_PATH")
        # L-003 fix: optional encryption key from env
        import base64
        encrypt_key = None
        raw_key = os.environ.get("MINDCORE_ENCRYPT_KEY")
        if raw_key:
            try:
                encrypt_key = base64.urlsafe_b64decode(raw_key.encode("ascii"))
            except Exception:
                logger.warning("invalid_encrypt_key", hint="Must be base64-encoded 32-byte key")
        _engine = MemoryEngine(storage_path=storage_path, encrypt_key=encrypt_key)
    return _engine


# =============================================================================
# Tool Definitions (MCP Protocol)
# =============================================================================

@server.list_tools()
async def list_tools() -> list[Tool]:
    """List all available tools."""
    return [
        Tool(
            name="memory_store",
            description="Store a new memory that should be remembered long-term.",
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "The memory content to store. Be specific and factual.",
                    },
                    "importance": {
                        "type": "integer",
                        "description": "Importance: 1=episodic, 2=working, 3=semantic, 4=critical",
                        "minimum": 1,
                        "maximum": 4,
                        "default": 2,
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Tags for categorization and retrieval.",
                    },
                    "session_id": {
                        "type": "string",
                        "description": "Session identifier to group related memories.",
                    },
                    "confidence": {
                        "type": "number",
                        "description": "Confidence level 0.0-1.0. Lower if uncertain.",
                        "minimum": 0.0,
                        "maximum": 1.0,
                        "default": 0.5,
                    },
                    "source": {
                        "type": "string",
                        "description": "Source of this memory: 'user', 'agent', or 'tool'.",
                        "default": "agent",
                    },
                },
                "required": ["content"],
            },
        ),
        Tool(
            name="memory_recall",
            description="Recall memories relevant to the query.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The query to search memories.",
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter by tags (optional).",
                    },
                    "session_id": {
                        "type": "string",
                        "description": "Filter by session (optional).",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max results to return. Default: 10",
                        "default": 10,
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="memory_context",
            description="Build a context window from relevant memories for LLM input.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "What is the current task or question?",
                    },
                    "max_tokens": {
                        "type": "integer",
                        "description": "Approximate max tokens for the context. Default: 2000",
                        "default": 2000,
                    },
                    "session_id": {
                        "type": "string",
                        "description": "Prioritize memories from this session.",
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="memory_update_confidence",
            description="Update a memory confidence score after correction.",
            inputSchema={
                "type": "object",
                "properties": {
                    "memory_id": {
                        "type": "string",
                        "description": "The memory ID to update.",
                    },
                    "confidence": {
                        "type": "number",
                        "description": "New confidence level 0.0-1.0.",
                        "minimum": 0.0,
                        "maximum": 1.0,
                    },
                },
                "required": ["memory_id", "confidence"],
            },
        ),
        Tool(
            name="memory_stats",
            description="Get stats: total count, importance distribution, avg confidence.",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="memory_delete",
            description="Delete a memory by its ID. Irreversible — use with caution.",
            inputSchema={
                "type": "object",
                "properties": {
                    "memory_id": {
                        "type": "string",
                        "description": "The memory ID to delete.",
                    },
                },
                "required": ["memory_id"],
            },
        ),
        Tool(
            name="bnd_check",
            description="Evaluate content through the 3D Boundary balance algorithm (Forward/Reverse Formula). Returns 4D scores (TRJ/EVO/COG/BALANCE) and accept/reject decision.",
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "Content to evaluate through the boundary algorithm.",
                    },
                    "importance": {
                        "type": "integer",
                        "description": "User-assigned importance 1-4.",
                        "minimum": 1,
                        "maximum": 4,
                        "default": 2,
                    },
                    "confidence": {
                        "type": "number",
                        "description": "Confidence 0.0-1.0.",
                        "minimum": 0.0,
                        "maximum": 1.0,
                        "default": 0.5,
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Tags for cognition dimension scoring.",
                    },
                },
                "required": ["content"],
            },
        ),
        Tool(
            name="bnd_stats",
            description="Get BND manager stats: acceptance rate, score distributions, anti-chain triggers.",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="deduce",
            description="Run the Deduction engine on stored memories to derive new cognitive insights. Finds patterns across high-quality COG memories.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "What domain or question to focus deduction on.",
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter deduction sources by tags (optional).",
                    },
                },
                "required": ["query"],
            },
        ),
    ]


# =============================================================================
# Tool Implementations
# =============================================================================

def _sanitize_arguments(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """H-001 fix: validate and sanitize all tool arguments before processing."""
    result: dict[str, Any] = {}

    if name == "memory_store":
        result["content"] = str(arguments.get("content", ""))
        result["importance"] = max(1, min(4, int(arguments.get("importance", 2))))
        result["tags"] = _sanitize_tags(arguments.get("tags"))
        result["session_id"] = _sanitize_session_id(arguments.get("session_id"))
        result["confidence"] = max(0.0, min(1.0, float(arguments.get("confidence", 0.5))))
        result["source"] = str(arguments.get("source", "agent"))[:32]
        result["metadata"] = _sanitize_metadata(arguments.get("metadata"))

    elif name == "memory_recall":
        result["query"] = str(arguments.get("query", ""))
        result["tags"] = _sanitize_tags(arguments.get("tags"))
        result["session_id"] = _sanitize_session_id(arguments.get("session_id"))
        result["limit"] = max(1, min(100, int(arguments.get("limit", 10))))

    elif name == "memory_context":
        result["query"] = str(arguments.get("query", ""))
        result["max_tokens"] = max(1, min(100_000, int(arguments.get("max_tokens", 2000))))
        result["session_id"] = _sanitize_session_id(arguments.get("session_id"))

    elif name == "memory_update_confidence":
        result["memory_id"] = str(arguments.get("memory_id", ""))[:64]
        result["confidence"] = max(0.0, min(1.0, float(arguments.get("confidence", 0.5))))

    elif name == "memory_delete":
        result["memory_id"] = str(arguments.get("memory_id", ""))[:64]

    elif name == "memory_stats":
        pass  # no arguments

    elif name == "bnd_check":
        result["content"] = str(arguments.get("content", ""))
        result["importance"] = max(1, min(4, int(arguments.get("importance", 2))))
        result["confidence"] = max(0.0, min(1.0, float(arguments.get("confidence", 0.5))))
        result["tags"] = _sanitize_tags(arguments.get("tags"))

    elif name == "bnd_stats":
        pass  # no arguments

    elif name == "deduce":
        result["query"] = str(arguments.get("query", ""))
        result["tags"] = _sanitize_tags(arguments.get("tags"))

    return result


def _sanitize_tags(tags: Any) -> list[str]:
    """Sanitize tag list: only strings, max 100 chars each, max 50 tags."""
    if not isinstance(tags, list):
        return []
    cleaned = []
    for t in tags:
        if t is None:
            continue
        s = str(t)[:100].strip()
        if s and s not in cleaned:
            cleaned.append(s)
        if len(cleaned) >= 50:
            break
    return cleaned


def _sanitize_string(value: Any, max_len: int = 256) -> str | None:
    """Sanitize optional string field."""
    if value is None:
        return None
    s = str(value)[:max_len].strip()
    return s if s else None


def _sanitize_session_id(value: Any) -> str | None:
    """L-008 fix: validate session_id format (alphanumeric + : _ -)."""
    if value is None:
        return None
    import re
    s = str(value)[:128].strip()
    if not s:
        return None
    if not re.match(r'^[a-zA-Z0-9:_\-]+$', s):
        raise ValueError(
            f"session_id contains invalid characters. "
            f"Only alphanumeric, colon, underscore and hyphen allowed: '{s}'"
        )
    return s


def _sanitize_metadata(metadata: Any) -> dict[str, Any]:
    """Sanitize metadata: shallow dict only, max 20 keys."""
    if not isinstance(metadata, dict):
        return {}
    result = {}
    for k, v in metadata.items():
        if len(result) >= 20:
            break
        key = str(k)[:64]
        if isinstance(v, (str, int, float, bool)):
            result[key] = v
        elif isinstance(v, list):
            result[key] = [str(x)[:256] for x in v[:10]]
        elif v is None:
            result[key] = None
        else:
            result[key] = str(v)[:256]
    return result


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> CallToolResult:
    """Execute a tool call."""
    # L-004 fix: rate limiting
    if not _check_rate():
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"Rate limit exceeded: max {_RATE_LIMIT} requests per {_RATE_WINDOW}s. Please slow down."
            )],
            isError=True,
        )

    engine = get_engine()

    # H-001 fix: sanitize all inputs before processing
    args = _sanitize_arguments(name, arguments)

    try:
        if name == "memory_store":
            memory_id = engine.store(
                content=args["content"],
                importance=args["importance"],
                tags=args["tags"],
                session_id=args.get("session_id"),
                confidence=args["confidence"],
                source=args["source"],
            )
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps({
                    "status": "stored",
                    "memory_id": memory_id,
                }, ensure_ascii=False))],
                isError=False,
            )
        
        elif name == "memory_recall":
            results = engine.recall(
                query=args["query"],
                tags=args["tags"],
                session_id=args.get("session_id"),
                limit=args["limit"],
            )
            
            output = {
                "count": len(results),
                "results": [
                    {
                        "memory_id": r.memory.id,
                        "content": r.memory.content,
                        "relevance": round(r.relevance_score, 3),
                        "confidence": round(r.confidence, 3),
                        "importance": r.memory.importance,
                        "tags": r.memory.tags,
                        "created_at": r.memory.created_at,
                        "snippet": r.snippet,
                    }
                    for r in results
                ],
            }
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(output, ensure_ascii=False))],
                isError=False,
            )
        
        elif name == "memory_context":
            context = engine.get_context_window(
                query=args["query"],
                max_tokens=args["max_tokens"],
                session_id=args.get("session_id"),
            )
            return CallToolResult(
                content=[TextContent(type="text", text=context)],
                isError=False,
            )
        
        elif name == "memory_update_confidence":
            success = engine.update_confidence(
                memory_id=args["memory_id"],
                confidence=args["confidence"],
            )
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps({
                    "success": success,
                    "memory_id": args["memory_id"],
                    "confidence": args["confidence"],
                }, ensure_ascii=False))],
                isError=False,
            )
        
        elif name == "memory_stats":
            stats = engine.get_stats()
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(stats, ensure_ascii=False))],
                isError=False,
            )

        elif name == "memory_delete":
            success = engine.delete(memory_id=args["memory_id"])
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps({
                    "success": success,
                    "memory_id": args["memory_id"],
                }, ensure_ascii=False))],
                isError=False,
            )

        elif name == "bnd_check":
            bnd_mgr = _get_bnd_manager()
            result = bnd_mgr.evaluate(
                content=args["content"],
                importance=args["importance"],
                confidence=args["confidence"],
                tags=args.get("tags"),
            )
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps({
                    "bnd_score": result.bnd_score,
                    "accepted": result.accepted,
                    "dimensions": result.dimensions,
                    "balance": result.balance,
                    "anti_chain_triggered": result.anti_chain_triggered,
                    "anti_chain_detail": result.anti_chain_detail,
                }, ensure_ascii=False))],
                isError=False,
            )

        elif name == "bnd_stats":
            bnd_mgr = _get_bnd_manager()
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(
                    bnd_mgr.stats, ensure_ascii=False
                ))],
                isError=False,
            )

        elif name == "deduce":
            engine = get_engine()
            # Fetch high-quality memories as deduction sources
            source_memories = engine.recall(
                query=args["query"],
                tags=args.get("tags"),
                limit=50,
            )
            # Convert to dict list
            memory_dicts = [
                {
                    "content": r.memory.content,
                    "importance": r.memory.importance,
                    "confidence": r.confidence,
                    "tags": r.memory.tags,
                    "bnd_score": getattr(r, "bnd_score", r.relevance_score),
                }
                for r in source_memories
            ]
            ded_engine = _get_deduction_engine()
            result = ded_engine.deduce(memory_dicts, query=args["query"])

            if result is None:
                return CallToolResult(
                    content=[TextContent(type="text", text=json.dumps({
                        "status": "insufficient_sources",
                        "message": "Not enough high-quality COG memories to derive insight. "
                                   "Need at least 3 memories with BND >= 0.5 and COG >= 0.35.",
                    }, ensure_ascii=False))],
                    isError=False,
                )

            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps({
                    "status": "deduction_generated",
                    "insight": result.insight,
                    "source_count": result.source_count,
                    "source_tags": result.source_tags,
                    "confidence": result.confidence,
                    "validated": result.validated,
                    "bnd_result": result.bnd_result,
                    "keywords": result.keywords,
                }, ensure_ascii=False))],
                isError=False,
            )
        
        else:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Unknown tool: {name}")],
                isError=True,
            )
    
    except ValueError as e:
        # Expected validation errors: safe to return details
        logger.warning("tool_validation_error", tool=name, error=str(e))
        return CallToolResult(
            content=[TextContent(type="text", text=str(e))],
            isError=True,
        )
    except Exception as e:
        # H-002 fix: sanitize error output — never leak file paths or internals
        logger.error("tool_error", tool=name, error=str(e), exc_info=True)
        return CallToolResult(
            content=[TextContent(
                type="text",
                text="Internal error occurred while processing your request. "
                     "Please check the memory store is accessible and try again."
            )],
            isError=True,
        )


# =============================================================================
# Entry Points
# =============================================================================

async def main_stdio():
    """Run as stdio MCP server (for Claude Desktop, VS Code, etc.)."""
    # structlog uses defaults (structured JSON to stderr)
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


def main():
    """CLI entry point."""
    # structlog uses defaults
    parser = argparse.ArgumentParser(description="MindCore Memory MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default="stdio",
        help="Transport mode. stdio for local IDE integration, http for remote.",
    )
    parser.add_argument("--host", default="127.0.0.1", help="HTTP host")
    parser.add_argument("--port", type=int, default=8080, help="HTTP port")
    parser.add_argument("--token", help="Bearer token for HTTP auth")
    args = parser.parse_args()
    
    if args.transport == "stdio":
        import asyncio
        asyncio.run(main_stdio())
    else:
        # HTTP mode (for remote deployment)
        import uvicorn
        from .http_app import create_http_app
        app = create_http_app(token=args.token)
        uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
