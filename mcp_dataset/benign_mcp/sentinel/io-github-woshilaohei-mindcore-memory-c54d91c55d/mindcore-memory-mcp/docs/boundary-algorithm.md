# 3D Balanced Boundary Algorithm — BND Boundary Manager

**The core inference engine of MindCore Memory.**

This is the world's first boundary evaluation system that encodes the "Forward/Reverse Formulas" into executable algorithms. Every memory write is automatically scored across four dimensions (TRJ/EVO/COG/BALANCE). The reverse formula detects decay chains in real time. Memories below threshold are filtered; memories triggering reverse chains are penalized by 50%.

---

## Algorithm Principles

### Forward Formula (Positive Cycle)

```
Trajectory(TRJ) = Boundary(BND) = Evolution(EVO) = Cognition(COG) = Boundary(BND)
```

Every step draws a boundary; every boundary is an evolution; every evolution is a layer of cognition; every layer of cognition draws new boundaries.

### Reverse Formula (Decay/Break Chain)

```
Chaos/Disorder → Unknown → Risk → Harm → Death/Extinction
```

Break any equals sign, and you survive. The algorithm detects 2+ ring chain triggers and automatically applies penalty weighting.

---

## Four-Dimensional Scoring

```
BND_score = 0.28·TRJ + 0.28·EVO + 0.28·COG + 0.16·BALANCE
```

### Dimension Descriptions

| Dimension | Evaluates | Keywords/Patterns |
|-----------|-----------|-------------------|
| **TRJ Trajectory** | Continuity, progress, reference linkage | "based on previous", "continue", "completed" |
| **EVO Evolution** | Growth signals, quantitative improvement, version leap | "fixed", "improved 30%", "v2.0" |
| **COG Cognition** | Root cause analysis, causal reasoning, tag richness | "root cause", "because... therefore..." |
| **BALANCE** | Variance normalization of 3D | balance = 1/(1+var×6) |

### Balance Calculation

```python
variance = Var([TRJ, EVO, COG])
balance = 1.0 / (1.0 + variance * 6.0)
```

Lower variance (more balanced 3D) → higher balance. Unbalanced memories (e.g., only EVO dimension high) automatically lower balance score.

---

## Reverse Formula Detection

Scans memory content, matches five-ring decay chain keywords:

| Ring | Keywords | Weight |
|------|-----------|--------|
| Chaos/Disorder | chaos, disorder, contradiction, uncontrollable | Alert trigger |
| Unknown | unknown, uncertain, missing | Chain trigger → penalty |
| Risk | risk, danger, vulnerability, flaw | Chain trigger → penalty |
| Harm | crash, failure, damage, broken | Chain trigger → penalty |
| Death/Extinction | deprecated, obsolete, eliminated | Chain trigger → penalty |

**Trigger Rule**: 2+ rings hit simultaneously → `BND_score × 0.5`

---

## Decision Rules

```
BND_score >= 0.40 → ACCEPT → enters BND version chain
BND_score <  0.40 → REJECT → retained only in EXP experience layer
Reverse chain 2+ rings triggered → PENALTY → re-evaluate at 50% weight
```

---

## Usage

### Python API

```python
from mindcore_memory import BNDManager

bnd = BNDManager()

# Evaluate a memory
result = bnd.evaluate(
    "Based on the previous BM25 fix, root cause identified as importance contamination, accuracy improved 30%",
    importance=4,
    confidence=0.9,
    tags=["fix", "root-cause"],
)

print(f"BND: {result.bnd_score:.3f}")       # 0.750
print(f"TRJ: {result.trj_score:.3f}")       # 0.630
print(f"EVO: {result.evo_score:.3f}")       # 0.540
print(f"COG: {result.cog_score:.3f}")       # 0.610
print(f"Balance: {result.balance:.3f}")     # 0.980
print(f"Accepted: {result.accepted}")        # True
```

### MCP Tool

```json
{
  "tool": "bnd_check",
  "arguments": {
    "content": "content text",
    "importance": 3,
    "confidence": 0.7,
    "tags": ["tag1", "tag2"]
  }
}
```

### Auto Integration

MemoryEngine injects BNDManager at creation. Every `store()` automatically runs 4D evaluation:

```python
from mindcore_memory import MemoryEngine, BNDManager

engine = MemoryEngine(bnd_manager=BNDManager())
engine.store("...")  # Auto BND evaluation, result stored in metadata
```

---

## Performance

- **Algorithm-only**: Zero LLM calls, zero network requests
- **Single evaluation**: < 1ms (keyword matching + regex + variance)
- **Non-blocking**: Evaluation failure degrades to INFO log, doesn't block main flow
- **Zero external deps**: Python standard library only (re, math, dataclasses)

---

## Design Philosophy

1. **Forward formula as soul** — Trajectory→Boundary→Evolution→Cognition→Boundary, cycle never stops
2. **Reverse formula as shield** — Chaos must be detected, decay chains must be broken
3. **Cognition before action** — BND evaluation is the final cognitive gate before write
4. **Pure algorithm, no LLM** — Inference engine does pattern extraction, not LLM calls

---

## Relationship to Bee Memory

Bee Memory v5.x's "Five-Dimensional Memory Pool (EXP/TRJ/COG/BND/CTX)" is the conceptual prototype:

- EXP → current `memory_store` storage layer
- TRJ/COG/BND → already implemented in BNDManager as 3D scoring
- CTX → corresponds to `memory_context` tool
- Void Engine (collision optimization) → corresponds to DeductionEngine's pattern extraction

**MindCore Memory is the industrial-grade upgrade of Bee Memory.**
