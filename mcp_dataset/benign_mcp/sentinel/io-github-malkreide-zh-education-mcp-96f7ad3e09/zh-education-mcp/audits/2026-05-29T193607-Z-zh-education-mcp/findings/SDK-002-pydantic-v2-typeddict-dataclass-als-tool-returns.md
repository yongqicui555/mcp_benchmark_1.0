## Finding: SDK-002 — Pydantic v2 / TypedDict / Dataclass als Tool-Returns

**Severity:** medium
**Status:** open
**Check-Status:** partial
**Server:** zh-education-mcp
**Check-Reference:** SDK-002
**PDF-Reference:** Sec 3.1

### Observed Behavior / Evidence
- Pydantic v2 in dependencies; Input-Modelle mit Field-Defaults und ConfigDict (server.py:133-268)
- ResponseFormat als StrEnum (Literal-artig)

### Gaps (Abweichung vom Best-Practice-Katalog)
- Tools haben Return-Annotation -> str (Markdown/JSON-String) statt strukturierter BaseModel/TypedDict/dict-Rückgaben ⇒ kein Output-Schema für den LLM
- Kein konsistenter Response-Envelope (source/provenance/results/count)

### Effort Estimate
M  (S < 1d · M 1-3d · L 1-2w · XL >2w)
