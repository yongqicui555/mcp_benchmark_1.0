# Real-World Examples

This document provides detailed, realistic examples of using the QAE MCP server for safety certification in common autonomous action scenarios.

## Example 1: Feature Rollout Evaluation

**Scenario**: Claude is helping with a product release decision.

### Setup
You're deciding whether to roll out a new feature (dark mode) to 25% of your user base.

### Claude's Analysis
```
I need to evaluate the safety of rolling out dark mode to 25% of users.

Let me break down the risk dimensions:
- Scope: 0.25 (affects 25% of users - moderate segment)
- Reversibility: 0.85 (simple feature flag toggle - easily reversible in seconds)
- Sensitivity: 0.3 (cosmetic change - low impact on core functionality)

This looks relatively safe. Let me get QAE's assessment.
```

### Tool Invocation
```python
certify_action(
    action_id="feature_darkmode_rollout_25pct",
    agent_id="claude_product_team",
    scope=0.25,
    reversibility=0.85,
    sensitivity=0.3,
    description="Feature rollout: Dark mode to 25% of users via feature flag"
)
```

### Expected Response
```json
{
  "decision": "Certified",
  "zone": "Safe",
  "margins": {
    "scope": 0.75,
    "reversibility": 0.85,
    "sensitivity": 0.70
  },
  "binding_constraint": null,
  "drift_budget": 98.5,
  "certificate_id": "cert_feat_darkmode_20250315_001",
  "deterministic_hash": "sha256:0xabcd...",
  "timestamp": "2025-03-15T14:23:45Z",
  "description": "Feature rollout: Dark mode to 25% of users via feature flag"
}
```

### Claude's Follow-up
```
Excellent news! This rollout is CERTIFIED (Safe zone). All margins are strong:
- Scope margin: 0.75 (25% is manageable)
- Reversibility margin: 0.85 (feature flag is quick to toggle)
- Sensitivity margin: 0.70 (cosmetic changes are low-risk)

There's no binding constraint, meaning all dimensions are comfortably safe.

Recommendation: PROCEED with the rollout. Monitor for 24 hours, then consider
expanding to additional user segments if telemetry looks good.
```

---

## Example 2: Database Migration with Risk

**Scenario**: Claude is advising on a critical database schema change.

### Setup
You need to add a new nullable column to the users table in production. It's necessary for a new feature but affects all users and cannot be easily reversed.

### Claude's Analysis
```
Adding a column to the users table carries risk:
- Scope: 1.0 (affects ALL users - global change)
- Reversibility: 0.25 (requires downtime, backup restore, or migration rollback)
- Sensitivity: 0.75 (if wrong, could block user access)

This is a high-risk operation. Let me check with QAE.
```

### Tool Invocation
```python
certify_action(
    action_id="db_migration_users_table_column_add",
    agent_id="claude_dba_assistant",
    scope=1.0,
    reversibility=0.25,
    sensitivity=0.75,
    description="Schema migration: Add nullable column to users table"
)
```

### Expected Response
```json
{
  "decision": "EscalateToHuman",
  "zone": "Danger",
  "margins": {
    "scope": 0.0,
    "reversibility": 0.25,
    "sensitivity": 0.25
  },
  "binding_constraint": "scope",
  "drift_budget": 97.8,
  "certificate_id": "cert_db_migration_20250315_002",
  "deterministic_hash": "sha256:0xefgh...",
  "timestamp": "2025-03-15T14:25:12Z",
  "description": "Schema migration: Add nullable column to users table"
}
```

### Claude's Follow-up
```
This action requires HUMAN ESCALATION (Danger zone). The binding constraint is SCOPE —
because it affects all users, this needs careful review.

Detailed assessment:
- Scope margin: 0.0 (global impact - affects all users, no way around it)
- Reversibility margin: 0.25 (difficult - would need downtime to roll back)
- Sensitivity margin: 0.25 (high - user access could be blocked if migration fails)

RECOMMENDED ACTIONS:
1. Schedule maintenance window (document it)
2. Perform migration on replica first (verify syntax, timing)
3. Have a tested rollback plan ready (backup, tested restore)
4. Brief the on-call team on what to do if issues arise
5. Monitor replication lag and query performance post-migration
6. Get explicit sign-off from DB team lead before proceeding

This is not blocked, but it REQUIRES human judgment and coordination. Do not
automate this without human oversight.
```

---

## Example 3: Automated Bug Fix with Low Risk

**Scenario**: Claude is autonomously fixing a minor bug in logging.

### Setup
An internal debug endpoint has a typo in error logging. You want to fix it automatically.

### Claude's Analysis
```
This is a low-risk internal fix:
- Scope: 0.05 (only internal logging - no user impact)
- Reversibility: 0.95 (simple code change - can revert in seconds)
- Sensitivity: 0.1 (typo fix - cosmetic, no logic change)

This should be safe to proceed with automatically.
```

### Tool Invocation
```python
certify_action(
    action_id="fix_logging_typo_debug_endpoint",
    agent_id="claude_code_repair",
    scope=0.05,
    reversibility=0.95,
    sensitivity=0.1,
    description="Fix: Correct typo in debug endpoint logging message"
)
```

### Expected Response
```json
{
  "decision": "Certified",
  "zone": "Safe",
  "margins": {
    "scope": 0.95,
    "reversibility": 0.95,
    "sensitivity": 0.90
  },
  "binding_constraint": null,
  "drift_budget": 97.5,
  "certificate_id": "cert_fix_logging_20250315_003",
  "deterministic_hash": "sha256:0xijkl...",
  "timestamp": "2025-03-15T14:27:33Z",
  "description": "Fix: Correct typo in debug endpoint logging message"
}
```

### Claude's Follow-up
```
CERTIFIED (Safe zone). This is a safe fix with no binding constraints:
- Scope margin: 0.95 (internal only, zero user impact)
- Reversibility margin: 0.95 (code change is trivial to revert)
- Sensitivity margin: 0.90 (cosmetic logging fix)

PROCEEDING with automated fix:
1. Committing fix to branch
2. Running unit tests
3. Submitting PR for review
4. No downtime or user communication required

Fix is complete. Awaiting code review.
```

---

## Example 4: Revenue-Impacting Price Change

**Scenario**: Claude is assisting with a pricing strategy decision.

### Setup
You want to raise prices by 15% for new customers (existing customers stay at old price). This could affect conversion rates but is reversible via coupons.

### Claude's Analysis
```
Price changes have significant impact:
- Scope: 0.6 (affects new customer cohort - moderate segment)
- Reversibility: 0.5 (can be reversed via promotional coupons/discounts - 1-2 days work)
- Sensitivity: 0.85 (directly impacts conversion and revenue)

This is in the caution zone. Let me check safety.
```

### Tool Invocation
```python
certify_action(
    action_id="pricing_increase_new_customers_15pct",
    agent_id="claude_revenue_team",
    scope=0.6,
    reversibility=0.5,
    sensitivity=0.85,
    description="Pricing change: Increase new customer pricing by 15%"
)
```

### Expected Response
```json
{
  "decision": "CertifiedWithWarning",
  "zone": "Caution",
  "margins": {
    "scope": 0.4,
    "reversibility": 0.5,
    "sensitivity": 0.15
  },
  "binding_constraint": "sensitivity",
  "drift_budget": 96.9,
  "certificate_id": "cert_pricing_change_20250315_004",
  "deterministic_hash": "sha256:0xmnop...",
  "timestamp": "2025-03-15T14:30:08Z",
  "description": "Pricing change: Increase new customer pricing by 15%"
}
```

### Claude's Follow-up
```
This action is CERTIFIED WITH WARNING (Caution zone).

Assessment:
- Scope margin: 0.4 (affects new customer cohort - moderate)
- Reversibility margin: 0.5 (reversible but requires promotion setup)
- **Binding constraint: SENSITIVITY (margin: 0.15)**

The sensitivity constraint is tight because pricing directly affects revenue
and customer acquisition.

RECOMMENDED SAFEGUARDS:
1. Run A/B test with 10% of traffic first (2-week test)
2. Set reversion trigger: If conversion drops >20%, activate discount coupons
3. Monitor daily: New customer acquisition, conversion rate, LTV impact
4. Daily review for 7 days before expanding to 100%
5. Have finance team on standby to adjust if needed
6. Communicate plan to executive sponsors

You may proceed, but with CLOSE MONITORING. This is not a set-and-forget change.
```

---

## Example 5: Batch Job with Moderate Risk

**Scenario**: Claude is scheduling a batch cleanup job.

### Setup
A daily job to delete expired sessions. It affects all users' sessions and is somewhat difficult to reverse (would require restoring from backup).

### Claude's Analysis
```
Batch job risk assessment:
- Scope: 0.8 (affects all users' sessions - global)
- Reversibility: 0.3 (would need to restore from backup if issues)
- Sensitivity: 0.6 (could force user re-login if overly aggressive)

Mixed risk profile. Let me check.
```

### Tool Invocation
```python
certify_action(
    action_id="batch_cleanup_expired_sessions",
    agent_id="claude_infrastructure",
    scope=0.8,
    reversibility=0.3,
    sensitivity=0.6,
    description="Batch job: Daily cleanup of expired user sessions"
)
```

### Expected Response
```json
{
  "decision": "CertifiedWithWarning",
  "zone": "Caution",
  "margins": {
    "scope": 0.2,
    "reversibility": 0.3,
    "sensitivity": 0.4
  },
  "binding_constraint": "scope",
  "drift_budget": 96.2,
  "certificate_id": "cert_batch_cleanup_20250315_005",
  "deterministic_hash": "sha256:0xqrst...",
  "timestamp": "2025-03-15T14:32:55Z",
  "description": "Batch job: Daily cleanup of expired user sessions"
}
```

### Claude's Follow-up
```
CERTIFIED WITH WARNING (Caution zone). Binding constraint: SCOPE.

Because this affects all users' sessions, careful planning is needed.

REQUIREMENTS FOR DEPLOYMENT:
1. Schedule during low-traffic window (2-4 AM UTC)
2. Dry run first: test on staging database
3. Implement gradual cleanup:
   - Run 1x daily, not all at once
   - Only delete sessions > 30 days old (not 7 days)
4. Monitoring:
   - Alert on abnormal login failures
   - Track session cleanup rate
   - Monitor user session churn
5. Rollback plan:
   - Can restore sessions from backup if needed
   - Have DBA on standby first run

Schedule: Start tomorrow (2025-03-16) at 02:00 UTC. Monitor for 3 days before
reducing oversight.
```

---

## Example 6: Immediate Block: Data Export

**Scenario**: Claude is presented with a risky data operation.

### Setup
A request to export all user email addresses to a CSV file for "marketing research." This is high-risk across all dimensions.

### Claude's Analysis
```
This is a red flag:
- Scope: 1.0 (all user data - global)
- Reversibility: 0.0 (once exported, cannot undo data exposure)
- Sensitivity: 1.0 (PII exposure - critical)

This should be blocked. Let me confirm.
```

### Tool Invocation
```python
certify_action(
    action_id="export_all_user_emails_csv",
    agent_id="claude_data_team",
    scope=1.0,
    reversibility=0.0,
    sensitivity=1.0,
    description="Export all user email addresses to CSV for marketing research"
)
```

### Expected Response
```json
{
  "decision": "Blocked",
  "zone": "Danger",
  "margins": {
    "scope": 0.0,
    "reversibility": 0.0,
    "sensitivity": 0.0
  },
  "binding_constraint": "all",
  "drift_budget": 95.8,
  "certificate_id": "cert_blocked_data_export_20250315_006",
  "deterministic_hash": "sha256:0xuvwx...",
  "timestamp": "2025-03-15T14:35:22Z",
  "description": "Export all user email addresses to CSV for marketing research"
}
```

### Claude's Follow-up
```
THIS ACTION IS BLOCKED (Danger zone).

Assessment:
- Scope margin: 0.0 (ALL user data - cannot be scoped down)
- Reversibility margin: 0.0 (PII EXPOSURE - cannot be undone)
- Sensitivity margin: 0.0 (CRITICAL - regulatory violation risk)

DECISION: DO NOT PROCEED. This action violates multiple safety constraints:
1. **Privacy**: Exporting all emails exposes PII
2. **Compliance**: GDPR/CCPA violations if not properly governed
3. **Irreversibility**: Once exposed, data cannot be "unexposed"

ALTERNATIVE SAFE APPROACHES:
- Use aggregated anonymized data instead
- Implement proper data governance request (with approval workflow)
- Use third-party marketing platform (doesn't require raw exports)
- Request explicit GDPR consent from users before export
- Consult legal/compliance team

This request requires formal governance review before proceeding.
```

---

## Summary Table

| Example | Action | Decision | Zone | Binding Constraint | Recommendation |
|---------|--------|----------|------|-------------------|-----------------|
| 1 | Dark mode 25% | Certified | Safe | None | Proceed immediately |
| 2 | DB migration | Escalate | Danger | Scope | Require human review |
| 3 | Logging fix | Certified | Safe | None | Automate if tests pass |
| 4 | Price +15% | Warning | Caution | Sensitivity | Proceed with monitoring |
| 5 | Batch cleanup | Warning | Caution | Scope | Schedule carefully |
| 6 | Email export | Blocked | Danger | All | Reject, escalate |

---

## Decision Flow for Claude

Use this mental model when integrating QAE certificates into decisions:

```
┌─ Get Certificate ─┐
│                   │
├─ Decision = Certified?
│   ├─ Yes → Safe margins, no constraints
│   │        Action: PROCEED (high confidence)
│   │
├─ Decision = CertifiedWithWarning?
│   ├─ Yes → Some margins tight, may have binding constraint
│   │        Action: PROCEED with SAFEGUARDS
│   │        - Monitor metrics closely
│   │        - Have rollback plan
│   │        - Set escalation triggers
│   │
├─ Decision = EscalateToHuman?
│   ├─ Yes → Significant risk, needs human judgment
│   │        Action: ESCALATE to expert/owner
│   │        - Present certificate details
│   │        - Offer recommendations
│   │        - Wait for human approval
│   │
└─ Decision = Blocked?
    ├─ Yes → Unacceptable risk across multiple dimensions
             Action: REJECT, offer alternatives
             - Explain binding constraints
             - Suggest safer approaches
             - Escalate if persistent

```

---

## References

- **QAE Safety Kernel**: https://qaesubstrate.com
- **Constraint Semantics**: See parent repository documentation
- **Research Paper**: https://doi.org/10.6084/m9.figshare.31742857
