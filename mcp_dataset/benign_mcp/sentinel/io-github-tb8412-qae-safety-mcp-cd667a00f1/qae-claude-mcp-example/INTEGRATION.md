# Integration Guide

## How Claude Uses This Server

When Claude needs to evaluate action safety, it invokes the `certify_action` tool with a proposed action and constraint dimensions. The server returns a safety certificate that Claude uses to decide whether to proceed, modify, or escalate the action.

### Workflow

```
1. Claude proposes an action with parameters
2. Claude invokes certify_action MCP tool
3. MCP server translates to qae_safety API call
4. SafetyCertifier evaluates across constraint channels
5. Safety certificate is returned to Claude
6. Claude reasons about the decision and next steps
```

## Certificate Output Format

Every certification returns this structure:

```json
{
  "decision": "Certified|CertifiedWithWarning|EscalateToHuman|Blocked",
  "zone": "Safe|Caution|Danger",
  "margins": {
    "scope": 0.75,
    "reversibility": 0.45,
    "sensitivity": 0.60
  },
  "binding_constraint": "reversibility",
  "drift_budget": 25.5,
  "certificate_id": "cert_abc123xyz789",
  "deterministic_hash": "sha256:0x...",
  "timestamp": "2025-03-15T14:23:45Z"
}
```

## Decision Interpretation

| Decision | Zone | Meaning | Action |
|----------|------|---------|--------|
| `Certified` | Safe | Safe; all margins > 0.6 | Proceed immediately |
| `CertifiedWithWarning` | Caution | Caution; some margins 0.3–0.6 | Proceed with monitoring |
| `EscalateToHuman` | Danger | Uncertain; margins 0.1–0.3 | Request human approval |
| `Blocked` | Danger | Unsafe; margins ≤ 0.1 | Do not proceed |

## Dimension Semantics

When calling `certify_action`, interpret dimensions as follows:

### Scope [0, 1]
**How many users/entities are affected?**
- 0.0 = Single user or internal operation
- 0.3 = Team or department (10-100 people)
- 0.6 = Product feature affecting thousands
- 1.0 = Global change (all users)

Example scores:
- Adjust user recommendation weight: 0.3
- Deploy to 10% of users: 0.5
- Change API behavior: 0.8
- Modify authentication: 1.0

### Reversibility [0, 1]
**How easily can the action be undone?**
- 0.0 = Permanent (cannot be reversed)
- 0.3 = Difficult to reverse (weeks of work)
- 0.6 = Moderately reversible (hours of work)
- 1.0 = Trivially reversible (seconds)

Example scores:
- Delete production database: 0.0
- Change pricing model: 0.2
- Deploy code change: 0.4 (requires hotfix)
- Toggle feature flag: 0.9
- Adjust log level: 1.0

### Sensitivity [0, 1]
**How much can this impact users/revenue?**
- 0.0 = No user impact
- 0.3 = Minor impact (cosmetic changes)
- 0.6 = Moderate impact (user experience)
- 1.0 = Critical impact (data loss, downtime)

Example scores:
- Fix typo in UI: 0.1
- Change color scheme: 0.2
- Modify search ranking: 0.6
- Change payment processing: 0.95
- Wipe user data: 1.0

## Example Scenarios

### Scenario 1: Deploy Recommendation Update

Action: "Deploy new recommendation algorithm to 10% of production users"

Scoring:
```
scope: 0.5        # Affects 10% of users (moderate segment)
reversibility: 0.4 # Requires rollback if issues (1-2 hours)
sensitivity: 0.7  # High impact on user experience
```

Call:
```python
certify_action(
    action_id="deploy_rec_algo_v2",
    agent_id="claude_ml_team",
    scope=0.5,
    reversibility=0.4,
    sensitivity=0.7,
    description="Deploy new recommendation algorithm to 10% of production users"
)
```

Expected decision: `CertifiedWithWarning` or `EscalateToHuman` (depends on binding constraint margin)

### Scenario 2: Adjust Internal Log Level

Action: "Increase logging verbosity on internal debug servers"

Scoring:
```
scope: 0.1        # Only affects internal systems
reversibility: 1.0 # Can toggle back instantly
sensitivity: 0.2  # No user-facing impact
```

Call:
```python
certify_action(
    action_id="adjust_debug_logs",
    agent_id="claude_devops",
    scope=0.1,
    reversibility=1.0,
    sensitivity=0.2,
    description="Increase logging verbosity on internal debug servers"
)
```

Expected decision: `Certified` (all margins > 0.6)

### Scenario 3: Schema Change

Action: "Modify user profile database schema (add column)"

Scoring:
```
scope: 1.0        # Affects all users
reversibility: 0.3 # Difficult to rollback (requires migration)
sensitivity: 0.8  # Could break user data access if wrong
```

Call:
```python
certify_action(
    action_id="schema_migration_2025_03_15",
    agent_id="claude_dba",
    scope=1.0,
    reversibility=0.3,
    sensitivity=0.8,
    description="Modify user profile database schema (add column)"
)
```

Expected decision: `EscalateToHuman` (high scope + low reversibility = human review needed)

## Budget Management

The server enforces safety budgets:
- **Budget limit**: 100 certifications per period (default)
- **Rate limit**: 50 certifications per hour (default)
- **Period**: 24 hours (resets daily)

When approaching limits:
```python
# Check budget
budget = check_budget()
if budget["budget_remaining"] < 10:
    # Approaching limit; consider escalating or batching actions
    pass
```

Customize in `src/qae_mcp_server/server.py`:
```python
adapter = AgenticAdapter(
    budget_limit=200.0,  # Increase to 200/day
    rate_limit=100.0,    # Increase to 100/hour
)
```

## Error Handling

The server returns error responses for invalid inputs:

```json
{
  "error": "scope must be in [0, 1], got 1.5",
  "action_id": "act_123",
  "timestamp": "2025-03-15T14:23:45Z"
}
```

Common errors:
- **Invalid dimension value**: Must be in [0, 1]
- **Missing qae-safety package**: Install with `pip install qae-safety`
- **Budget exhausted**: Wait for reset or increase limits

## Audit Trail

All certifications are logged and retrievable:

```python
history = get_certification_history(limit=20)
# Returns:
# {
#   "certifications": [
#     {
#       "certificate_id": "cert_xyz789",
#       "action_id": "act_456",
#       "agent_id": "claude_v3",
#       "decision": "CertifiedWithWarning",
#       "zone": "Caution",
#       "timestamp": "2025-03-15T14:15:32Z"
#     },
#     ...
#   ],
#   "total_count": 42
# }
```

Use this to:
- Review recent decisions
- Identify patterns (e.g., frequent escalations)
- Audit trail for compliance
- Debug decision reasoning

## Determinism Guarantees

The QAE kernel is deterministic:
- **Same inputs → Same output always**
- No random sampling or stochastic behavior
- Hashes allow reproducibility verification
- Safe for:
  - Audit trails
  - Compliance reviews
  - Regression testing
  - Reproducible research

Verify determinism:
```python
cert1 = certify_action(...same params...)
cert2 = certify_action(...same params...)
assert cert1["deterministic_hash"] == cert2["deterministic_hash"]
```

## Claude Conversation Integration

Example Claude conversation flow:

**User**: "Deploy the new search algorithm to 5% of users. Is this safe?"

**Claude**: "Let me evaluate the safety of this deployment using QAE certification."

[Claude invokes certify_action tool]

**Response from MCP server**:
```json
{
  "decision": "CertifiedWithWarning",
  "zone": "Caution",
  "margins": {
    "scope": 0.5,
    "reversibility": 0.4,
    "sensitivity": 0.65
  },
  "binding_constraint": "reversibility"
}
```

**Claude**: "The deployment is **cautiously safe** (Caution zone). The binding constraint is reversibility — we can only score 0.4/1.0 because rolling back would take 1-2 hours. I recommend:
1. Have a rollback plan ready (documented, tested)
2. Monitor user metrics closely during rollout
3. Schedule a follow-up review after 24 hours
4. If issues arise, trigger immediate rollback

Would you like me to proceed with these safeguards in place?"

## References

- **Safety Certificate Schema**: See `README.md` — API Reference section
- **Constraint Channels**: See parent QAE documentation
- **Research Paper**: https://doi.org/10.6084/m9.figshare.31742857
- **MCP Protocol**: https://modelcontextprotocol.io/introduction
