"""
BND Boundary Manager — 3D Balanced Boundary Algorithm (v1.0)

The core inference engine of MindCore, based on the Forward/Reverse Formulas 4D scoring system.

Forward Formula (positive cycle):
    Trajectory = Boundary = Evolution = Cognition = Boundary
    Every step (TRJ) → draws a boundary (BND) → one evolution (EVO) → one layer of cognition (COG) → new boundary

Reverse Formula (decay/break chain):
    Chaos/Disorder → Unknown → Risk → Harm → Death/Extinction
    Break any equals sign, and you survive

4D Scoring:
    BND_score = w1·TRJ + w2·EVO + w3·COG + w4·BALANCE
    Below threshold → reject from BND version chain
    Reverse triggered → auto penalty 50%
"""

import re
import math
from dataclasses import dataclass, field
from typing import Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class BNDResult:
    """BND evaluation result — 4D scores + reverse chain detection"""

    trj_score: float       # Trajectory dimension 0.0-1.0
    evo_score: float       # Evolution dimension 0.0-1.0
    cog_score: float       # Cognition dimension 0.0-1.0
    balance: float         # 3D balance 0.0-1.0 (variance normalized)
    bnd_score: float       # Composite BND score 0.0-1.0
    accepted: bool         # Passed boundary, enters BND version chain
    anti_chain_triggered: bool    # Reverse formula decay chain triggered
    anti_chain_detail: str = ""   # Reverse chain detail "Chaos → Unknown → ..."
    dimensions: dict = field(default_factory=dict)


class BNDManager:
    """
    3D Balanced Boundary Manager.

    Every memory write goes through 4D evaluation:
    1. Trajectory (TRJ) — continuity and progress
    2. Evolution (EVO) — represents growth and improvement
    3. Cognition (COG) — represents deep understanding
    4. Balance (BALANCE) — whether 3D is balanced

    Also detects reverse formula: if memory triggers 2+ rings of decay chain,
    automatically applies 50% penalty.
    """

    # 4D weights — default uniform, dynamically adjustable
    TRJ_WEIGHT = 0.28
    EVO_WEIGHT = 0.28
    COG_WEIGHT = 0.28
    BALANCE_WEIGHT = 0.16

    # BND acceptance threshold
    BND_THRESHOLD = 0.40

    # === Forward Formula: Keyword Dictionary ===

    # Trajectory dimension — continuity / reference / progress
    TRJ_REFERENCE_KW = [
        "基于", "如上", "前述", "上次", "之前", "继续", "跟进",
        "based on", "following", "previously", "continue", "next step",
    ]
    TRJ_PROGRESS_KW = [
        "完成", "通过", "发布", "部署", "上线", "合并", "推送", "提交",
        "completed", "passed", "released", "deployed", "merged", "pushed",
    ]

    # Evolution dimension — growth / fix / quantitative improvement
    EVO_GROWTH_KW = [
        "修复", "优化", "升级", "改进", "突破", "解决", "实现", "完成",
        "fixed", "optimized", "upgraded", "improved", "solved", "completed",
        "resolved", "实现", "达成", "交付",
    ]
    EVO_METRIC_PATTERN = (
        r'(?:提升|提高|增加|增长|降低|减少|improve|increase|decrease|reduce|boost)'
        r'[^\\d]*(\\d+(?:\\.\\d+)?)'
    )

    # Cognition dimension — root cause / pattern recognition / deep understanding
    COG_INSIGHT_KW = [
        "根因", "原理", "本质", "认知", "理解", "发现", "模式", "规律",
        "root cause", "principle", "insight", "pattern", "discovered",
        "认识到", "领悟", "推断", "机制",
    ]
    COG_CAUSAL_KW = [
        "因为", "所以", "导致", "造成", "归因", "因此", "由此可见",
        "because", "therefore", "causes", "due to", "hence",
    ]

    # === Reverse Formula: Decay Chain Keywords ===

    ANTI_CHAIN = {
        "Chaos(disorder)": ["混乱", "无序", "矛盾", "冲突", "不可控",
                        "chaos", "disorder", "contradiction", "inconsistent"],
        "Unknown(unknown)": ["未知", "不确定", "不知道", "未覆盖", "无数据",
                        "unknown", "uncertain", "unclear", "missing"],
        "Risk(risk)": ["风险", "危险", "隐患", "漏洞", "脆弱",
                      "risk", "danger", "vulnerability", "threat"],
        "Harm(harm)": ["崩溃", "失败", "损坏", "中断", "不可用",
                      "crash", "fail", "broken", "down", "unavailable"],
        "Death(death)": ["废弃", "过时", "淘汰", "淘汰", "不再维护",
                      "deprecated", "obsolete", "dead", "retired"],
    }

    def __init__(self):
        self._version = 1
        self._accepted_count = 0
        self._rejected_count = 0
        self._anti_chain_triggers = 0
        self._score_history: list[dict] = []  # Last 100 score records

    def evaluate(
        self,
        content: str,
        importance: int = 2,
        confidence: float = 0.5,
        tags: list = None,
        related_count: int = 0,
    ) -> BNDResult:
        """
        Execute 4D scoring + reverse chain detection on a memory.

        Args:
            content: memory text content
            importance: user-marked importance 1-4
            confidence: confidence level 0.0-1.0
            tags: tag list (used to detect tag richness)
            related_count: number of related memories (trajectory dimension reference)

        Returns:
            BNDResult with 4D scores and accept/reject decision
        """
        content_lower = content.lower()

        # === Dimension 1: Trajectory TRJ ===
        trj = self._score_trajectory(content_lower, importance, related_count)

        # === Dimension 2: Evolution EVO ===
        evo = self._score_evolution(content_lower)

        # === Dimension 3: Cognition COG ===
        cog = self._score_cognition(content_lower, confidence, tags)

        # === Dimension 4: Balance BALANCE ===
        scores = [trj, evo, cog]
        mean = sum(scores) / 3
        variance = sum((s - mean) ** 2 for s in scores) / 3
        # Higher variance = more unbalanced → lower balance
        balance = 1.0 / (1.0 + variance * 6.0)

        # === Composite BND Score ===
        bnd = (
            self.TRJ_WEIGHT * trj
            + self.EVO_WEIGHT * evo
            + self.COG_WEIGHT * cog
            + self.BALANCE_WEIGHT * balance
        )
        bnd = max(0.0, min(1.0, bnd))

        # === Reverse Formula Detection ===
        anti_result = self._check_anti_chain(content_lower)

        # Reverse triggered → 50% penalty
        if anti_result["triggered"]:
            bnd *= 0.5
            self._anti_chain_triggers += 1

        accepted = bnd >= self.BND_THRESHOLD

        if accepted:
            self._accepted_count += 1
        else:
            self._rejected_count += 1

        # Record score history
        self._score_history.append({
            "trj": round(trj, 3),
            "evo": round(evo, 3),
            "cog": round(cog, 3),
            "balance": round(balance, 3),
            "bnd": round(bnd, 3),
            "accepted": accepted,
            "anti": anti_result["triggered"],
        })
        if len(self._score_history) > 100:
            self._score_history.pop(0)

        return BNDResult(
            trj_score=round(trj, 3),
            evo_score=round(evo, 3),
            cog_score=round(cog, 3),
            balance=round(balance, 3),
            bnd_score=round(bnd, 3),
            accepted=accepted,
            anti_chain_triggered=anti_result["triggered"],
            anti_chain_detail=anti_result["detail"],
            dimensions={
                "trj": round(trj, 3),
                "evo": round(evo, 3),
                "cog": round(cog, 3),
                "balance": round(balance, 3),
            },
        )

    def _score_trajectory(
        self, content_lower: str, importance: int, related_count: int
    ) -> float:
        """Score trajectory dimension: memory continuity and progress"""
        score = 0.35  # baseline

        # Reference: does it reference prior knowledge
        ref_count = sum(1 for kw in self.TRJ_REFERENCE_KW if kw in content_lower)
        score += min(ref_count * 0.10, 0.25)

        # Progress: does it record clear state change
        prog_count = sum(1 for kw in self.TRJ_PROGRESS_KW if kw in content_lower)
        score += min(prog_count * 0.08, 0.20)

        # Related memory count → high trajectory density
        if related_count > 0:
            score += min(related_count * 0.03, 0.10)

        # Importance weighting
        score += (importance - 2) * 0.04

        return max(0.0, min(1.0, score))

    def _score_evolution(self, content_lower: str) -> float:
        """Score evolution dimension: does memory represent growth or improvement"""
        score = 0.30  # baseline

        # Growth signals
        growth_count = sum(1 for kw in self.EVO_GROWTH_KW if kw in content_lower)
        score += min(growth_count * 0.12, 0.40)

        # Quantitative improvement (e.g. "improved 30%")
        if re.search(self.EVO_METRIC_PATTERN, content_lower):
            score += 0.15

        # Version upgrade marker
        versions = re.findall(r'v(\d+\.\d+)', content_lower)
        if versions:
            score += min(len(versions) * 0.06, 0.10)

        # Leap pattern: from X → Y
        if re.search(r'(?:从|from)\s*.+\s*(?:到|→|=>|to)\s*', content_lower):
            score += 0.10

        return max(0.0, min(1.0, score))

    def _score_cognition(
        self, content_lower: str, confidence: float, tags: list = None
    ) -> float:
        """Score cognition dimension: does memory represent deep understanding"""
        score = 0.25  # baseline

        # Insight keywords
        insight_count = sum(1 for kw in self.COG_INSIGHT_KW if kw in content_lower)
        score += min(insight_count * 0.15, 0.40)

        # Causal reasoning chain
        causal_count = sum(1 for kw in self.COG_CAUSAL_KW if kw in content_lower)
        score += min(causal_count * 0.08, 0.15)

        # Confidence weighting: low confidence cognition is unreliable
        score += confidence * 0.12

        # Tag richness → high cognition
        if tags and len(tags) >= 3:
            score += 0.08

        return max(0.0, min(1.0, score))

    def _check_anti_chain(self, content_lower: str) -> dict:
        """
        Reverse formula detection: Chaos → Unknown → Risk → Harm → Death

        Scan memory content, detect how many rings of decay chain are triggered.
        2+ rings chain-triggered → alert
        """
        chain = []

        for label, keywords in self.ANTI_CHAIN.items():
            if any(kw in content_lower for kw in keywords):
                chain.append(label)

        triggered = len(chain) >= 2
        detail = " → ".join(chain) if triggered else ""

        return {"triggered": triggered, "detail": detail}

    def tune_weights(self, trj: float = None, evo: float = None,
                     cog: float = None) -> None:
        """Dynamically tune 3D weights, must sum to 1 - BALANCE_WEIGHT"""
        total = self.TRJ_WEIGHT + self.EVO_WEIGHT + self.COG_WEIGHT
        if trj is not None:
            self.TRJ_WEIGHT = trj
        if evo is not None:
            self.EVO_WEIGHT = evo
        if cog is not None:
            self.COG_WEIGHT = cog
        # Normalize
        new_total = self.TRJ_WEIGHT + self.EVO_WEIGHT + self.COG_WEIGHT
        if new_total != total and new_total > 0:
            scale = (1.0 - self.BALANCE_WEIGHT) / new_total
            self.TRJ_WEIGHT *= scale
            self.EVO_WEIGHT *= scale
            self.COG_WEIGHT *= scale

    @property
    def stats(self) -> dict:
        """BND manager statistics"""
        total = max(1, self._accepted_count + self._rejected_count)
        return {
            "version": self._version,
            "accepted": self._accepted_count,
            "rejected": self._rejected_count,
            "total_evaluated": self._accepted_count + self._rejected_count,
            "acceptance_rate": round(self._accepted_count / total, 3),
            "anti_chain_triggers": self._anti_chain_triggers,
            "threshold": self.BND_THRESHOLD,
            "weights": {
                "TRJ": round(self.TRJ_WEIGHT, 3),
                "EVO": round(self.EVO_WEIGHT, 3),
                "COG": round(self.COG_WEIGHT, 3),
                "BALANCE": round(self.BALANCE_WEIGHT, 3),
            },
            "recent_scores": self._score_history[-10:] if self._score_history else [],
        }
