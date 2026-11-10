"""
Intelligence System for Research MCP v2.0

This module provides advanced memory, reasoning, and learning capabilities
for multi-agent coordination and persistent knowledge management.

Key Components:
- Memory: Persistent storage with semantic search (SQLite + FAISS)
- Reasoning: Chain capture, replay, and pattern recognition
- Skills: Dynamic skill registry and capability matching
- Knowledge Graph: Agent interaction and dependency tracking
- Learning: Adaptive optimization and pattern mining
"""

from .memory.persistence import PersistentMemory
from .memory.embeddings import EmbeddingManager
from .reasoning.chain_capture import ReasoningChainCapture
from .skills.skill_registry import SkillRegistry

__version__ = "2.0.0-alpha.1"
__all__ = [
    "PersistentMemory",
    "EmbeddingManager",
    "ReasoningChainCapture",
    "SkillRegistry"
]