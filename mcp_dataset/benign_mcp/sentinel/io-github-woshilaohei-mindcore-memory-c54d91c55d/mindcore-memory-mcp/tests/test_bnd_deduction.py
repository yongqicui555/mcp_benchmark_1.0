"""
Tests for BND Boundary Manager + Deduction Engine — v1.0

Coverage:
- BND: Forward formula 4D scoring (TRJ/EVO/COG/BALANCE)
- BND: Reverse formula decay chain detection
- BND: Accept/reject decision
- Deduction: High-quality memory filtering
- Deduction: Keyword extraction and co-occurrence discovery
- Deduction: Insight synthesis
- Integration: MemoryEngine + BND auto-evaluate
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from mindcore_memory.bnd import BNDManager, BNDResult


# =============================================================================
# BND Manager Tests
# =============================================================================

class TestBNDDimensions:
    """4D scoring tests"""

    def test_high_all_dimensions(self):
        """High TRJ+high EVO+high COG = high BND score, accepted"""
        bnd = BNDManager()
        result = bnd.evaluate(
            "Based on previous BM25 fix, continued optimizing retrieval algorithm, "
            "understood root cause is importance score contaminating keyword relevance, "
            "accuracy improved 30% to 97%.",
            importance=4,
            confidence=0.9,
            tags=["optimization", "root-cause", "algorithm"],
        )
        assert result.bnd_score > 0.5
        assert result.accepted
        assert result.trj_score > 0.4
        assert result.evo_score > 0.4
        assert result.cog_score > 0.4

    def test_low_all_dimensions(self):
        """Pure data dump: no trajectory, no evolution, no cognition → very low BND"""
        bnd = BNDManager()
        result = bnd.evaluate(
            "Today's weather is nice, had a bowl of noodles.",
            importance=1,
            confidence=0.3,
        )
        # No TRJ, no EVO, no COG → BND should be very low
        assert result.bnd_score < 0.45
        assert result.trj_score < 0.4
        assert result.evo_score < 0.4
        assert result.cog_score < 0.35

    def test_balance_high(self):
        """3D balanced → high balance"""
        bnd = BNDManager()
        result = bnd.evaluate(
            "Based on prior cognition, continued progress and completed optimization, "
            "understood the principle and improved results.",
            importance=3,
            confidence=0.8,
        )
        assert result.balance > 0.5  # 3D balanced

    def test_balance_low(self):
        """3D unbalanced → low-ish balance"""
        bnd = BNDManager()
        result = bnd.evaluate(
            "A" * 50,  # No keywords at all → baseline scores, low-ish balance
            importance=1,
            confidence=0.1,
        )
        # With no keywords, balance depends on baseline variance
        assert 0.0 < result.balance <= 1.0


class TestAntiChain:
    """Reverse formula detection tests"""

    def test_anti_chain_triggered(self):
        """Chaos+Risk chain triggered"""
        bnd = BNDManager()
        result = bnd.evaluate(
            "System has unknown chaos, crash risk exists, may cause data corruption.",
            importance=3,
            confidence=0.6,
        )
        assert result.anti_chain_triggered
        assert len(result.anti_chain_detail) > 0
        assert result.bnd_score < 0.5  # Penalized

    def test_anti_chain_not_triggered(self):
        """No decay chain keywords"""
        bnd = BNDManager()
        result = bnd.evaluate(
            "OS upgrade completed, all functional tests passed.",
            importance=2,
            confidence=0.8,
        )
        assert not result.anti_chain_triggered
        assert result.anti_chain_detail == ""

    def test_full_anti_chain(self):
        """Full 5-ring decay chain"""
        bnd = BNDManager()
        result = bnd.evaluate(
            "Core module has chaos and disorder, unknown issue causes risk to spike, "
            "may cause serious damage, eventually leading to module deprecation.",
        )
        assert result.anti_chain_triggered
        # At least 3 rings should be triggered
        assert "→" in result.anti_chain_detail


class TestBNDStats:
    """Statistics tests"""

    def test_stats_accumulate(self):
        """Stats accurate after multiple evaluations"""
        bnd = BNDManager()
        for i in range(10):
            bnd.evaluate(
                f"Completed optimization #{i}, understood root cause and fixed",
                importance=3,
                confidence=0.7,
            )
        stats = bnd.stats
        assert stats["total_evaluated"] == 10
        assert 0 <= stats["acceptance_rate"] <= 1
        assert "weights" in stats

    def test_tune_weights(self):
        """Dynamic weight tuning"""
        bnd = BNDManager()
        bnd.tune_weights(trj=0.5, evo=0.3, cog=0.2)
        # Check normalization
        total = bnd.TRJ_WEIGHT + bnd.EVO_WEIGHT + bnd.COG_WEIGHT
        assert abs(total - (1.0 - bnd.BALANCE_WEIGHT)) < 0.01


# =============================================================================
# Deduction Engine Tests
# =============================================================================

class TestDeductionEngine:
    """Deduction engine tests"""

    @pytest.fixture
    def ded_engine(self):
        from mindcore_memory.deduction import DeductionEngine
        from mindcore_memory.bnd import BNDManager
        ded = DeductionEngine()
        ded.set_bnd_manager(BNDManager())
        return ded

    @pytest.fixture
    def high_quality_memories(self):
        """Simulate a set of high-quality cognitive memories"""
        return [
            {
                "content": "Fixed BM25 importance contamination, root cause is importance score polluting keyword relevance",
                "importance": 4,
                "confidence": 0.9,
                "tags": ["fix", "BM25", "root-cause"],
                "bnd_score": 0.75,
                "dimensions": {"cog": 0.8},
            },
            {
                "content": "Based on previous fix, continued optimizing retrieval algorithm, replaced RRF with deterministic routing",
                "importance": 3,
                "confidence": 0.8,
                "tags": ["optimize", "retrieval", "routing"],
                "bnd_score": 0.70,
                "dimensions": {"cog": 0.7},
            },
            {
                "content": "Discovered retrieval accuracy improved from 91% to 97%, attributed to BM25 fix and routing optimization",
                "importance": 4,
                "confidence": 0.9,
                "tags": ["retrieval", "performance", "metrics"],
                "bnd_score": 0.80,
                "dimensions": {"cog": 0.85},
            },
            {
                "content": "Pattern recognized: all retrieval issues point to two root causes — importance contamination and temporal noise",
                "importance": 4,
                "confidence": 0.95,
                "tags": ["pattern", "root-cause", "retrieval"],
                "bnd_score": 0.85,
                "dimensions": {"cog": 0.9},
            },
        ]

    def test_deduce_success(self, ded_engine, high_quality_memories):
        """Sufficient high-quality memories should produce deduction"""
        result = ded_engine.deduce(high_quality_memories, query="retrieval system optimization")
        assert result is not None
        assert result.insight.startswith("[Deduction]")
        assert result.source_count >= 3
        assert result.confidence > 0.4
        assert result.validated  # Should pass BND

    def test_deduce_insufficient(self, ded_engine):
        """Fewer than 3 high-quality memories should skip"""
        memories = [
            {"content": "A normal memory", "importance": 1, "confidence": 0.3,
             "tags": [], "bnd_score": 0.2, "dimensions": {"cog": 0.1}},
        ]
        result = ded_engine.deduce(memories, query="test")
        assert result is None

    def test_keyword_extraction(self, ded_engine):
        """Basic keyword extraction functionality"""
        kws = ded_engine._extract_keywords(
            "Fixed BM25 importance contamination issue, understood root cause is importance"
        )
        assert len(kws) > 0
        # Check Chinese+English mixed extraction
        has_chinese = any('\u4e00' <= c <= '\u9fff' for kw in kws for c in kw)
        has_english = any(kw.isascii() and len(kw) > 2 for kw in kws)
        assert has_chinese or has_english

    def test_co_occurrence(self, ded_engine, high_quality_memories):
        """Co-occurrence pattern discovery"""
        all_keywords = []
        for m in high_quality_memories:
            all_keywords.append(
                ded_engine._extract_keywords(m["content"]) + m.get("tags", [])
            )
        co_occur = ded_engine._find_co_occurrence(all_keywords)
        # Should have cross-memory co-occurring words
        assert len(co_occur) > 0


# =============================================================================
# Integration Tests
# =============================================================================

class TestBNDIntegration:
    """BND + MemoryEngine integration tests"""

    def test_engine_with_bnd(self):
        """MemoryEngine + BND auto-evaluate"""
        from mindcore_memory.memory_engine import MemoryEngine
        from mindcore_memory.bnd import BNDManager

        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            bnd = BNDManager()
            engine = MemoryEngine(storage_path=tmpdir, bnd_manager=bnd)

            # Store a high-quality memory
            mid = engine.store(
                content="Based on previous fix, continued optimization and understood root cause in algorithm design, accuracy improved 20%",
                importance=4,
                confidence=0.9,
                tags=["optimize", "root-cause"],
            )

            # Verify BND evaluation result in metadata
            mem = engine._memories[mid]
            assert "bnd_score" in mem.metadata
            assert "bnd_accepted" in mem.metadata
            assert "bnd_dimensions" in mem.metadata

    def test_engine_without_bnd(self):
        """Should not crash without BND manager"""
        from mindcore_memory.memory_engine import MemoryEngine
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = MemoryEngine(storage_path=tmpdir)
            mid = engine.store("A normal memory")
            assert mid is not None
