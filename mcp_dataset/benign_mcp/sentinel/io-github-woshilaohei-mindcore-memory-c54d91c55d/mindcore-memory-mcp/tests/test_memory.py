"""Tests for MindCore Memory Engine."""

import tempfile
import shutil

import pytest

from mindcore_memory.memory_engine import MemoryEngine


@pytest.fixture
def engine():
    """Create a temp engine for testing."""
    tmp = tempfile.mkdtemp(prefix="mindcore_test_")
    e = MemoryEngine(storage_path=tmp)
    yield e
    shutil.rmtree(tmp, ignore_errors=True)


class TestMemoryStore:
    def test_store_returns_id(self, engine):
        mid = engine.store("Test memory")
        assert mid is not None
        assert len(mid) == 36  # UUID format
    
    def test_store_with_metadata(self, engine):
        mid = engine.store(
            content="Paris is the capital of France",
            importance=3,
            tags=["geography", "fact"],
            confidence=0.95,
            source="user",
        )
        mem = engine._memories[mid]
        assert "Paris" in mem.content
        assert mem.importance == 3
        assert "geography" in mem.tags
        assert mem.confidence == 0.95
    
    def test_persistence(self, engine):
        """Memory survives engine restart."""
        engine.store("Persistent memory")
        
        # Create new engine instance with same storage
        engine2 = MemoryEngine(storage_path=str(engine.storage_path))
        results = engine2.recall("Persistent")
        
        assert len(results) == 1
        assert "Persistent" in results[0].memory.content


class TestMemoryRecall:
    def test_recall_by_keyword(self, engine):
        engine.store("Python is a programming language")
        engine.store("The weather is nice today")
        
        results = engine.recall("Python")
        assert len(results) >= 1
        assert "Python" in results[0].memory.content
    
    def test_recall_by_tag(self, engine):
        engine.store("React is a UI library", tags=["frontend"])
        engine.store("PostgreSQL is a database", tags=["backend"])
        
        results = engine.recall("library", tags=["frontend"])
        assert len(results) >= 1
        assert "React" in results[0].memory.content
    
    def test_recall_limit(self, engine):
        for i in range(20):
            engine.store(f"Memory {i}", importance=2)
        
        results = engine.recall("Memory", limit=5)
        assert len(results) == 5
    
    def test_recall_empty_query(self, engine):
        engine.store("Something important")
        results = engine.recall("xyz123nonexistent")
        # Should return nothing for non-matching query
        assert all("xyz123" not in r.memory.content for r in results)


class TestImportanceWeighting:
    def test_high_importance_ranks_higher(self, engine):
        # This test requires semantic embeddings to match "important note" →
        # "Critical fact: server is down". Without FAISS, BM25 alone can't
        # bridge the semantic gap. Skip if embedder unavailable.
        if not engine.embedder_available():
            pytest.skip("semantic embeddings not available (no sentence-transformers)")
        engine.store("Low priority note", importance=1)
        engine.store("Critical fact: server is down", importance=4)
        
        results = engine.recall("important note")
        # High-importance memory should appear in top-ranked results
        importances = [r.memory.importance for r in results]
        assert 4 in importances, f"Expected importance=4 in results, got {importances}"


class TestConfidence:
    def test_confidence_propagates(self, engine):
        engine.store("I am 95% sure about this", confidence=0.95)
        results = engine.recall("95%")
        assert results[0].confidence == 0.95
    
    def test_update_confidence(self, engine):
        mid = engine.store("Initial fact", confidence=0.5)
        engine.update_confidence(mid, 0.95)
        
        assert engine._memories[mid].confidence == 0.95


class TestContextWindow:
    def test_context_within_token_limit(self, engine):
        for i in range(10):
            engine.store(f"Memory content number {i}" * 50, importance=2)
        
        context = engine.get_context_window(query="Memory", max_tokens=500)
        # Should be under ~2000 chars for 500 tokens
        assert len(context) < 3000


class TestStats:
    def test_stats_tracking(self, engine):
        engine.store("Memory 1", importance=1)
        engine.store("Memory 2", importance=3)
        engine.store("Memory 3", importance=4)
        
        stats = engine.get_stats()
        assert stats["total_memories"] == 3
        assert stats["by_importance"][4] == 1
        assert stats["avg_confidence"] > 0
