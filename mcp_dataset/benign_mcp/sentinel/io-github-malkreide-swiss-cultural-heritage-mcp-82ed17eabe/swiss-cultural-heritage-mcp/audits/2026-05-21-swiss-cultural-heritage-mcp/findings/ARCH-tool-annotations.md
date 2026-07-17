# Finding — ARCH / Tool annotations consistency

**Check:** ARCH-009 (Tool annotations) + ARCH-001 (naming) — combined
**Status:** PARTIAL
**Severity:** low
**File:** `src/swiss_cultural_heritage_mcp/server.py:926-934, 759-768`

## Evidence

### Naming — PASS
All seven tools use the snake_case convention with a consistent `heritage_*` prefix. No spaces, dots, or mixed conventions.

### Annotations — minor inconsistencies

1. `heritage_cross_search` is declared with `"idempotentHint": False` (line 932), but its implementation is a pure read-only fan-out across three idempotent GET endpoints. There is no side effect that would justify `False`. This contradicts the other six tools (all `idempotentHint: True`) and confuses callers/agents that branch on idempotency.

2. `heritage_list_nb_collections` (line 769) takes `response_format: str = "markdown"` as a raw string, while every other tool uses the `ResponseFormat` `StrEnum` and a Pydantic input model. Result: no validation, no `extra="forbid"`, no schema-level enumeration in the tool surface.

### Description quality — PASS
Tool docstrings include use-cases and parameter context (well above the "semantic-empty" bar in ARCH-001).

## Impact

- Low. Mostly cosmetic, but the `idempotentHint` mismatch could affect retry behaviour of more sophisticated MCP clients.

## Remediation

1. Set `idempotentHint: True` on `heritage_cross_search`.
2. Refactor `heritage_list_nb_collections` to take a Pydantic input model with `response_format: ResponseFormat = ResponseFormat.MARKDOWN`, matching the rest of the server.

**Effort:** XS (< 1 hour)
