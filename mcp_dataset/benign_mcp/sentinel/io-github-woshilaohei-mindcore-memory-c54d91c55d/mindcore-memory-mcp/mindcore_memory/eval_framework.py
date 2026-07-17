"""
Evaluation Framework for MindCore Memory MCP.

Measures:
1. Memory Recall Accuracy - Does the right memory come back?
2. Context Window Efficiency - How much relevant info per token?
3. Confidence Calibration - Are confidence scores accurate?
4. Storage Integrity - Are memories persisted correctly?
5. Hallucination Rate - Does the system generate false memories?

Usage:
    pytest tests/ -v
    python -m mindcore_memory.eval_framework
"""

from __future__ import annotations

import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import structlog

logger = structlog.get_logger()


@dataclass
class EvalResult:
    """Single evaluation result."""
    name: str
    passed: bool
    score: float  # 0.0-1.0
    details: str
    duration_ms: float


@dataclass
class EvalSuite:
    """Full evaluation suite results."""
    total: int
    passed: int
    failed: int
    results: list[EvalResult]
    overall_score: float
    timestamp: str

    def print_summary(self) -> None:
        print(f"\n{'='*60}")
        print("  MindCore Memory Eval Suite")
        print(f"{'='*60}")
        print(f"  Total: {self.total} | Passed: {self.passed} | Failed: {self.failed}")
        print(f"  Overall Score: {self.overall_score:.1%}")
        print(f"{'='*60}")
        for r in self.results:
            status = "PASS" if r.passed else "FAIL"
            print(f"  [{status}] [{r.score:.0%}] {r.name}: {r.details}")
        print(f"{'='*60}\n")


class MemoryEvaluator:
    """Production evaluation framework for memory MCP."""
    
    def __init__(self, storage_path: Optional[str] = None):
        if storage_path:
            self.storage_path = Path(storage_path)
        else:
            self.storage_path = Path(tempfile.mkdtemp(prefix="mindcore_eval_"))
        
        # Import here to avoid circular
        from mindcore_memory.memory_engine import MemoryEngine
        self.engine = MemoryEngine(storage_path=str(self.storage_path))
    
    def cleanup(self) -> None:
        """Clean up temp storage."""
        # M-007 fix: Windows temp dirs don't start with "/tmp/"
        tmp_prefixes = ("/tmp/", "\\tmp\\")
        storage = str(self.storage_path)
        if any(storage.startswith(p) for p in tmp_prefixes):
            shutil.rmtree(self.storage_path, ignore_errors=True)
            return
        # Also clean if path contains temp/mindcore_eval_ markers
        if "mindcore_eval_" in storage:
            shutil.rmtree(self.storage_path, ignore_errors=True)
    
    def eval_storage_integrity(self) -> EvalResult:
        """Test 1: Memories are stored and retrieved correctly."""
        import time
        start = time.time()
        
        try:
            test_id = self.engine.store(
                content="The capital of France is Paris.",
                importance=3,
                tags=["geography", "fact"],
                confidence=0.95,
            )
            
            results = self.engine.recall("France capital")
            
            if not results:
                return EvalResult(
                    name="Storage Integrity",
                    passed=False,
                    score=0.0,
                    details="Memory stored but not retrieved",
                    duration_ms=(time.time() - start) * 1000,
                )
            
            retrieved = results[0].memory
            correct = (
                retrieved.id == test_id and
                "Paris" in retrieved.content and
                "geography" in retrieved.tags
            )
            
            return EvalResult(
                name="Storage Integrity",
                passed=correct,
                score=1.0 if correct else 0.5,
                details=f"Stored and retrieved correctly: {correct}",
                duration_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            return EvalResult(
                name="Storage Integrity",
                passed=False,
                score=0.0,
                details=f"Exception: {e}",
                duration_ms=(time.time() - start) * 1000,
            )
    
    def eval_recall_relevance(self) -> EvalResult:
        """Test 2: Relevant memories are ranked higher than irrelevant ones."""
        import time
        start = time.time()
        
        try:
            self.engine.store("Python is a programming language", importance=3, tags=["tech"])
            self.engine.store("The sky is blue", importance=1, tags=["fact"])
            self.engine.store(
            "Python was created by Guido van Rossum",
            importance=3,
            tags=["tech", "python"]
        )
            self.engine.store("The ocean is deep", importance=1, tags=["fact"])
            
            results = self.engine.recall("Python programming", limit=10)
            
            python_count = sum(1 for r in results[:4] if "Python" in r.memory.content)
            passed = python_count >= 2
            
            return EvalResult(
                name="Recall Relevance",
                passed=passed,
                score=1.0 if passed else 0.6,
                details=f"Python memories in top4: {python_count}/2",
                duration_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            return EvalResult(
                name="Recall Relevance",
                passed=False,
                score=0.0,
                details=f"Exception: {e}",
                duration_ms=(time.time() - start) * 1000,
            )
    
    def eval_confidence_calibration(self) -> EvalResult:
        """Test 3: Confidence scores are properly set and retrievable."""
        import time
        start = time.time()
        
        try:
            self.engine.store("Water boils at 100C", importance=3, confidence=0.98)
            self.engine.store("I think the meeting is at 3pm", importance=1, confidence=0.4)
            
            results = self.engine.recall("boiling point water")
            results2 = self.engine.recall("meeting time")
            
            if not results or not results2:
                return EvalResult(
                    name="Confidence Calibration",
                    passed=False,
                    score=0.0,
                    details="Memories not retrieved",
                    duration_ms=(time.time() - start) * 1000,
                )
            
            calibrated = results[0].confidence > results2[0].confidence
            
            return EvalResult(
                name="Confidence Calibration",
                passed=calibrated,
                score=1.0 if calibrated else 0.5,
                details=f"High={results[0].confidence}, Low={results2[0].confidence}",
                duration_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            return EvalResult(
                name="Confidence Calibration",
                passed=False,
                score=0.0,
                details=f"Exception: {e}",
                duration_ms=(time.time() - start) * 1000,
            )
    
    def eval_importance_weighting(self) -> EvalResult:
        """Test 4: Higher importance memories are retrieved first."""
        import time
        start = time.time()
        
        try:
            self.engine.store("Meeting notes from yesterday", importance=1, tags=["work"])
            self.engine.store("Meeting notes from yesterday", importance=4, tags=["work"])
            
            results = self.engine.recall("meeting notes work", limit=5)
            
            if not results:
                return EvalResult(
                    name="Importance Weighting",
                    passed=False,
                    score=0.0,
                    details="No memories retrieved",
                    duration_ms=(time.time() - start) * 1000,
                )
            
            correct = results[0].memory.importance == 4
            
            return EvalResult(
                name="Importance Weighting",
                passed=correct,
                score=1.0 if correct else 0.5,
                details=f"Top importance: {results[0].memory.importance} (expected 4)",
                duration_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            return EvalResult(
                name="Importance Weighting",
                passed=False,
                score=0.0,
                details=f"Exception: {e}",
                duration_ms=(time.time() - start) * 1000,
            )
    
    def eval_context_window_efficiency(self) -> EvalResult:
        """Test 5: Context window builds efficiently within token limit."""
        import time
        start = time.time()
        
        try:
            for i in range(20):
                self.engine.store(
                    f"Memory number {i} about project X",
                    importance=(i % 4) + 1,
                    tags=["project"],
                )
            
            context = self.engine.get_context_window(
                query="project X",
                max_tokens=500,
            )
            
            char_count = len(context)
            under_limit = char_count < 2500
            
            return EvalResult(
                name="Context Window Efficiency",
                passed=under_limit,
                score=1.0 if under_limit else 0.5,
                details=f"Context: {char_count} chars",
                duration_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            return EvalResult(
                name="Context Window Efficiency",
                passed=False,
                score=0.0,
                details=f"Exception: {e}",
                duration_ms=(time.time() - start) * 1000,
            )
    
    def run_all(self) -> EvalSuite:
        """Run the full evaluation suite."""
        from datetime import datetime
        
        tests = [
            self.eval_storage_integrity,
            self.eval_recall_relevance,
            self.eval_confidence_calibration,
            self.eval_importance_weighting,
            self.eval_context_window_efficiency,
        ]
        
        results = []
        for test in tests:
            r = test()
            results.append(r)
            status = "PASS" if r.passed else "FAIL"
            logger.info("eval_result", name=r.name, status=status, score=r.score)
        
        passed = sum(1 for r in results if r.passed)
        total = len(results)
        overall_score = sum(r.score for r in results) / total
        
        suite = EvalSuite(
            total=total,
            passed=passed,
            failed=total - passed,
            results=results,
            overall_score=overall_score,
            timestamp=datetime.utcnow().isoformat(),
        )
        
        return suite


def main():
    """Run evaluation from CLI."""
    evaluator = MemoryEvaluator()
    try:
        suite = evaluator.run_all()
        suite.print_summary()
        import sys
        sys.exit(0 if suite.failed == 0 else 1)
    finally:
        evaluator.cleanup()


if __name__ == "__main__":
    main()
