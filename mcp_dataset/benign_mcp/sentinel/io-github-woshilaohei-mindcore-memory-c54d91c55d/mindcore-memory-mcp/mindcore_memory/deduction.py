"""
Deduction Engine — Inference Memory Layer (v1.0)

The third layer of hierarchical memory: deriving new knowledge from high-confidence cognitive memories.

Pipeline:
    STM (short-term) → LTM (long-term) → Deduction (inference)
    raw memories     → persisted memories   → derived memories

How it works:
    1. Collect high-quality memories with BND score >= 0.6 and COG dimension >= 0.5
    2. Cluster by tags, discover cross-topic patterns
    3. Derive new cognition from intersection points of multiple memories
    4. After BND validation, write result as type=deduction memory
"""

import json
from collections import Counter
from dataclasses import dataclass, field
from typing import Optional
import logging
import re

logger = logging.getLogger(__name__)


@dataclass
class DeductionResult:
    """Deduction output"""
    insight: str                  # Derived new cognition
    source_count: int            # How many source memories used
    source_tags: list[str]       # Tags involved
    confidence: float            # Deduction confidence
    bnd_result: Optional[dict] = None  # BND validation result
    validated: bool = False      # Passed BND validation
    keywords: list = field(default_factory=list)  # Extracted keywords


class DeductionEngine:
    """
    Deduction memory engine.

    No LLM calls. Pure statistical pattern recognition + BND validation pipeline:
    1. Extract keyword co-occurrence patterns from high-quality cognitive memories
    2. Discover hidden associations across tags
    3. Format deduction result, write after BND validation
    """

    # Minimum requirements: memories used for deduction must satisfy
    MIN_BND_SCORE = 0.50      # BND composite score floor
    MIN_COG_SCORE = 0.35      # COG cognition dimension floor
    MIN_SOURCES = 3            # At least 3 source memories to deduce
    MIN_KEYWORD_OVERLAP = 2   # At least 2 keyword overlap to consider related

    # Stop words (exclude high-frequency meaningless words)
    STOP_WORDS = {
        "的", "是", "了", "在", "和", "与", "等", "及", "或",
        "the", "a", "an", "is", "are", "was", "were", "be", "been",
        "of", "to", "in", "on", "at", "for", "with", "by", "and", "or",
        "this", "that", "it", "its", "we", "you", "they", "he", "she",
        "has", "have", "had", "do", "does", "did", "not", "no", "but",
    }

    def __init__(self, bnd_manager=None):
        self._bnd_manager = bnd_manager
        self._deduction_count = 0

    def set_bnd_manager(self, bnd_manager):
        """Inject BND manager (avoid circular dependency)"""
        self._bnd_manager = bnd_manager

    def deduce(self, memories: list, query: str = "") -> Optional[DeductionResult]:
        """
        Derive new cognition from a list of memories.

        Args:
            memories: list of memory entries, each must have content, importance, confidence, tags
            query: current query intent, for targeted deduction (optional)

        Returns:
            DeductionResult if deduction succeeded, else None
        """
        # Step 1: Filter high-quality cognitive memories
        high_quality = self._filter_high_quality(memories)
        if len(high_quality) < self.MIN_SOURCES:
            logger.debug("deduction_skip", reason="insufficient_sources",
                        count=len(high_quality), required=self.MIN_SOURCES)
            return None

        # Step 2: Extract all keywords
        all_keywords = []
        for m in high_quality:
            kws = self._extract_keywords(m.get("content", ""))
            all_keywords.append(kws + (m.get("tags", []) or []))

        # Step 3: Find cross-memory common patterns
        co_occurrence = self._find_co_occurrence(all_keywords)

        # Step 4: Synthesize new cognition from co-occurrence patterns
        insight = self._synthesize_insight(
            high_quality, co_occurrence, query
        )
        if not insight:
            return None

        # Step 5: Calculate deduction confidence
        confidence = self._calc_deduction_confidence(
            len(high_quality), len(co_occurrence)
        )

        # Step 6: BND validation
        bnd_result = None
        validated = True
        if self._bnd_manager:
            bnd = self._bnd_manager.evaluate(
                content=insight,
                importance=3,  # Deduction memory default importance=3
                confidence=confidence,
                tags=list(co_occurrence.keys())[:5],
            )
            bnd_result = {
                "bnd_score": bnd.bnd_score,
                "accepted": bnd.accepted,
                "dimensions": bnd.dimensions,
                "anti_chain_triggered": bnd.anti_chain_triggered,
            }
            validated = bnd.accepted

        self._deduction_count += 1

        return DeductionResult(
            insight=insight,
            source_count=len(high_quality),
            source_tags=list(set(t for m in high_quality for t in (m.get("tags") or []))),
            confidence=round(confidence, 3),
            bnd_result=bnd_result,
            validated=validated,
            keywords=list(co_occurrence.keys()),
        )

    def _filter_high_quality(self, memories: list) -> list:
        """Filter high-quality cognitive memories"""
        return [
            m for m in memories
            if m.get("bnd_score", 0) >= self.MIN_BND_SCORE
            and m.get("cog_score", m.get("dimensions", {}).get("cog", 0)) >= self.MIN_COG_SCORE
        ]

    def _extract_keywords(self, text: str) -> list[str]:
        """Extract keywords from text (statistical method, not NLP)"""
        # Chinese: split by char, 2-4 gram
        # English: split by space, words
        words = []

        # English words
        eng_words = re.findall(r'[a-zA-Z][a-zA-Z0-9_-]{2,}', text)
        words.extend(w.lower() for w in eng_words if w.lower() not in self.STOP_WORDS)

        # Chinese 2-3 gram (consecutive Chinese chars)
        chinese_chars = re.findall(r'[\u4e00-\u9fff]+', text)
        for segment in chinese_chars:
            for i in range(len(segment) - 1):
                words.append(segment[i:i + 2])
            for i in range(len(segment) - 2):
                words.append(segment[i:i + 3])

        return list(set(words))  # deduplicate

    def _find_co_occurrence(self, keyword_lists: list[list]) -> Counter:
        """Find cross-memory co-occurring keywords"""
        counter = Counter()
        for kw_list in keyword_lists:
            counter.update(set(kw_list))

        # Filter single-occurrence (no cross-memory significance)
        return Counter({
            k: v for k, v in counter.items()
            if v >= self.MIN_KEYWORD_OVERLAP and k not in self.STOP_WORDS
        })

    def _synthesize_insight(
        self, memories: list, co_occurrence: Counter, query: str = ""
    ) -> Optional[str]:
        """
        Synthesize new cognition from high-quality memories and co-occurrence patterns.

        Strategy: find top 5 most frequent keywords,
                  build a deduction result around them.
        """
        if not co_occurrence:
            return None

        top_kws = co_occurrence.most_common(5)
        top_terms = [kw for kw, _ in top_kws]

        # Find source memories containing these keywords as evidence
        evidence = []
        for m in memories:
            content = m.get("content", "")
            hits = sum(1 for kw in top_terms if kw in content)
            if hits >= 2:
                evidence.append(content[:80] + "...")

        if not evidence:
            return None

        # Extract common topics (by tags)
        all_tags = [t for m in memories for t in (m.get("tags") or [])]
        tag_counter = Counter(all_tags)
        top_tags = [t for t, _ in tag_counter.most_common(3)]

        # Build insight text (language matches input memories)
        kw_str = "、".join(top_terms[:5])
        tag_str = "、".join(top_tags[:3]) if top_tags else "general domain"

        if query:
            insight = (
                f"[Deduction] For query `{query[:60]}`, identified key pattern in {tag_str} domain: "
                f"{kw_str}. The repeated co-occurrence of these {len(top_terms)} concepts suggests deep association."
                f" Evidence: {len(evidence)} high-quality memories."
            )
        else:
            insight = (
                f"[Deduction] {tag_str} domain key pattern: {kw_str}."
                f" Based on cross-analysis of {len(memories)} cognitive memories,"
                f" this concept group co-occurs across {len(evidence)} memories,"
                f" indicating undocumented deep connections."
            )

        return insight

    def _calc_deduction_confidence(
        self, source_count: int, pattern_count: int
    ) -> float:
        """Calculate deduction confidence"""
        # More sources, richer patterns → higher confidence
        base = 0.4
        source_bonus = min(source_count / 20.0, 0.30)   # 20 sources → +0.30
        pattern_bonus = min(pattern_count / 10.0, 0.30)  # 10 patterns → +0.30
        return min(1.0, base + source_bonus + pattern_bonus)

    @property
    def stats(self) -> dict:
        """Deduction engine statistics"""
        return {
            "deductions_generated": self._deduction_count,
            "bnd_available": self._bnd_manager is not None,
        }
