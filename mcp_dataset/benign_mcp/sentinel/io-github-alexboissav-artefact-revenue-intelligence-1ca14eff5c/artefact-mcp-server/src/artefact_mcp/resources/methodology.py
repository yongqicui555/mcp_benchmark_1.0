"""
Static methodology resources for the Artefact Revenue Intelligence MCP server.

Exposed as MCP resources so AI assistants can reference the scoring models,
tier definitions, segment definitions, and SPICED framework.
"""

SCORING_MODEL = """# ICP Scoring Model (14.5 Points)

## Firmographic Fit (5 points)
- **Industry** (2 pts): Primary target = 2.0, Adjacent = 1.0, Tangential = 0.5, Outside = 0
- **Revenue Range** (1.5 pts): Sweet spot ($1.6M-$70M) = 1.5, Acceptable = 1.0, Stretch = 0.5, Outside = 0
- **Employee Count** (1 pt): Ideal (10-200) = 1.0, Borderline = 0.5, Outside = 0
- **Geography** (0.5 pts): Primary (Canada) = 0.5, Secondary (US) = 0.25, Outside = 0

## Behavioral Fit (5 points)
- **Tech Stack Match** (2 pts): Full core (HubSpot+) = 2.0, Most = 1.5, Partial = 1.0, Minimal = 0.5, None = 0
- **Growth Signals** (1.5 pts): Multiple (3+) = 1.5, Some (2) = 1.0, Weak (1) = 0.5, None = 0
- **Content Engagement** (1 pt): Active = 1.0, Occasional = 0.5, None = 0
- **Purchase Frequency** (0.5 pts): Regular = 0.5, Occasional = 0.25, Never = 0

## Strategic Fit (4.5 points)
- **Decision-Maker Access** (2 pts): C-suite = 2.0, Director = 1.5, Manager = 1.0, Indirect = 0.5, None = 0
- **Budget Authority** (1.5 pts): Dedicated = 1.5, Shared = 1.0, Possible = 0.5, None = 0
- **Strategic Alignment** (1 pt): Strong = 1.0, Partial = 0.5, Misaligned = 0

## Exclusions
Industries excluded from scoring: Agencies, Consulting firms, B2C/Retail, Non-profits, Staffing, Events Services, VC/PE

## 5 Discriminators (Must Have 4 of 5)
1. HubSpot Active User (Mandatory)
2. Revenue Architecture Conviction (Mandatory)
3. Marketing Function Engaged (Mandatory)
4. Clear Growth Targets (High)
5. Multiple Stakeholders (High)
"""

TIER_DEFINITIONS = """# ICP Tier Definitions

## Tier 1: Ideal (12.0 - 14.5 points)
- **Color:** Green | **HubSpot:** tier_1_ideal
- Pursue aggressively. Same-day response. Senior team, custom proposals, full pricing.
- Expected: 40-60% win rate, shortest cycle, highest LTV
- Distribution: 10-15% of addressable market

## Tier 2: Strong (9.0 - 11.9 points)
- **Color:** Blue | **HubSpot:** tier_2_strong
- Active pursuit. 24h response. Standard team, selective discounting.
- Expected: 25-40% win rate, moderate cycle, good LTV
- Distribution: 20-30% of addressable market

## Tier 3: Moderate (6.0 - 8.9 points)
- **Color:** Yellow | **HubSpot:** tier_3_moderate
- Selective — inbound or strategic only. 48h response. Junior team.
- Expected: 10-25% win rate, longer cycle, lower LTV
- Distribution: 30-40% of addressable market

## Tier 4: Poor (0 - 5.9 points)
- **Color:** Red | **HubSpot:** tier_4_poor
- Deprioritize — nurture only. No SLA. Fully automated.
- Expected: <10% win rate, longest cycle, lowest LTV
- Distribution: 20-30% of addressable market

## Health Check
- Tier 1: 10-15% (>25% or <5% = adjust thresholds)
- Tier 1+2: 30-45% (>60% or <20% = review criteria)
- Tier 4: 20-30% (>50% or <10% = revisit model)
"""

RFM_SEGMENTS = """# RFM Segment Definitions (11 Segments)

| Segment | R | F | Total | Action |
|---------|---|---|-------|--------|
| **Champions** | >=4 | >=4 | >=13 | Reward loyalty, ask for referrals |
| **Loyal Customers** | >=3 | >=3 | >=11 | Cross-sell, maintain relationship |
| **Potential Loyalists** | >=4 | 2-3 | >=9 | Nurture with targeted content |
| **New Customers** | =5 | =1 | >=8 | Exceptional onboarding |
| **Promising** | =4 | =1 | >=7 | Second purchase incentive |
| **Need Attention** | =3 | 2-3 | 7-10 | Re-engagement campaigns |
| **About to Sleep** | 2-3 | 1-2 | 5-8 | Win-back campaigns |
| **At Risk** | <=2 | >=3 | >=8 | Urgent outreach, investigate |
| **Can't Lose Them** | 1-2 | >=4 | >=10 | Executive outreach, service recovery |
| **Hibernating** | <=2 | <=2 | <=6 | Low-cost re-engagement |
| **Lost** | =1 | =1 | <=4 | Remove from active campaigns |

## Scoring Scales (1-5)
- **Recency:** Days since last purchase (lower = better). Default: <=30=5, 31-90=4, 91-180=3, 181-365=2, 366+=1
- **Frequency:** Transaction count (higher = better). Default: 10+=5, 5-9=4, 3-4=3, 2=2, 1=1
- **Monetary:** Revenue percentile (higher = better). Default: Top 20%=5, 60-80%=4, 40-60%=3, 20-40%=2, Bottom 20%=1

## Industry Presets
- **B2B Service:** Longer recency windows (60/180/365/730 days)
- **SaaS:** Shorter recency windows (30/60/90/180 days)
- **Manufacturing:** Longest cycles (90/365/730/1095 days)
"""

SPICED_FRAMEWORK = """# SPICED Discovery Framework

SPICED is Artefact Ventures' discovery methodology for extracting deal intelligence.

| Letter | Dimension | What to Extract |
|--------|-----------|-----------------|
| **S** | Situation | Current state — growth plateau, operational silos, tech stack, team structure |
| **P** | Pain | Core pain — revenue predictability, invisible ROI, departmental silos, manual processes |
| **I** | Impact | Quantified impact — $2-5M revenue lost annually, missed opportunities, team churn |
| **C** | Critical Event | Trigger — investor pressure, competitive threat, missed quarter, leadership change |
| **E** | Economic Buyer | Decision maker — typically CEO + CFO, 2-3 month decision cycle |
| **D** | Decision Process | Committee of 3-4, needs cross-functional alignment, approval workflow |

## Key Personas

### François - SMB CEO
- Pain: Revenue predictability, invisible marketing ROI
- Trigger: Investor pressure, competitive threat
- Cycle: 2-3 months, committee decision

### Martin - VP Sales
- Pain: Chaotic pipeline, underperforming team
- Trigger: Missed quarter, lost top performer
- Cycle: 2-4 weeks, needs CEO approval

## Qualification Signals

### Great Fit
- HubSpot active with data
- Leadership convinced on revenue architecture
- Marketing + Sales alignment
- Clear growth targets with timeline
- 2-3+ stakeholders engaged

### Poor Fit
- NOT convinced on CRM value
- NO marketing role/function
- NO clear vision or targets
- Single decision maker resistant to change
- Looking for "just a tool"
"""


VALUE_ENGINES = """# Value Engines Framework

Every business operates three distinct Value Engines, each requiring dedicated processes, roles, and metrics.

## 1. Growth Engine (Customer Acquisition)
**Purpose:** How new customers are acquired — awareness through conversion.
**Artefact Pillars:** Revenue Intelligence + Customer Intelligence

**Stages:**
1. **Create Demand** — Generate awareness in ungated channels (content, thought leadership, events, dark social)
2. **Capture Demand** — Buyer intent becomes visible (form fills, demo requests, hand-raisers)
3. **Convert** — First transaction occurs (signed engagement, initial purchase)

**Key Metrics:** CR1 (Visit → Lead), CR2 (Lead → Qualified), Win Rate, Cycle Time, Pipeline Coverage

**Demand Creation vs. Capture:**
- Demand Creation: Build future pipeline (95% of market not buying now). Channels: LinkedIn, podcasts, events.
- Demand Capture: Convert the 5% actively looking. Channels: Google Ads, G2, referrals.
- Healthy split: 40-60% Demand Creation. Below 30% = brittle, dependent on competitive channels.

## 2. Fulfillment Engine (Value Delivery)
**Purpose:** How customers receive promised value — post-sale through expansion.
**Artefact Pillars:** Execution Intelligence + Customer Intelligence

**Stages:**
1. **Onboard** — Client setup, data connections, kickoff
2. **Deliver** — Core service execution against SOW
3. **Activate** — Client achieves first meaningful outcome (time to value)
4. **Review** — QBR, performance tracking, satisfaction
5. **Renew** — Contract renewal conversation
6. **Expand** — Upsell, cross-sell, deeper implementation

**Key Metrics:** NRR, Gross Retention, Time to First Value, CSAT, Expansion Revenue %

## 3. Innovation Engine (Product/Service Improvement)
**Purpose:** How products and services improve over time.
**Artefact Pillar:** Performance Intelligence

**Stages:**
1. **Gather** — Collect insights from clients, market, team
2. **Prioritize** — Evaluate against strategic goals
3. **Build/Test** — Develop and validate
4. **Launch** — Roll out to clients and market

**Key Metrics:** Feedback Items, Features Shipped/Quarter, Adoption Rate, Innovation ROI
"""

EXIT_CRITERIA = """# Pipeline Exit Criteria Framework

A pipeline stage is not a label — it is a **contract**. Exit criteria are the tests that must pass before a deal advances.

## Exit Test Schema

Each criterion has:
- **test_name** — What must be true
- **test_category** — qualification | discovery | commercial | technical | legal
- **required_proof** — Evidence needed to pass
- **validation_method** — checkbox | select_field | evidence_url | api_check | manual_review
- **approver_role** — Who signs off
- **is_blocking** — true = deal cannot advance; false = advisory only

## Standard Transitions

### Lead → MQL (Does this lead match our ICP and show intent?)
1. Firmographic fit score meets threshold (blocking)
2. Company size within ICP range (blocking)
3. Industry matches ICP vertical (blocking)
4. Engagement threshold reached (blocking)
5. Valid contact information (blocking)

### MQL → SQL (Has sales confirmed this lead is worth pursuing?)
1. BANT budget confirmed (blocking)
2. Authority identified (blocking)
3. Need mapped to ICP pain taxonomy (blocking)
4. Timeline is actionable (blocking)
5. Sales accepted lead (blocking)

### SQL → Discovery Qualified (Do we deeply understand the buyer?)
1. SPICED framework complete (blocking)
2. Champion identified (blocking)
3. Decision process mapped (blocking)
4. Timeline confirmed with critical event (blocking)
5. Impact quantified (advisory)
6. Competitive landscape documented (advisory)

### Discovery → Proposal (Can we propose with confidence?)
1. Budget confirmed and aligned to scope (blocking)
2. Success metrics agreed (blocking)
3. Technical requirements documented (blocking)
4. Stakeholder map complete (blocking)
5. Proposal format agreed (advisory)

### Proposal → Negotiation (Is the proposal being actively evaluated?)
1. Proposal delivered and reviewed (blocking)
2. Pricing approved by champion (blocking)
3. Legal requirements identified (blocking)
4. Go-live timeline agreed (blocking)

### Negotiation → Closed Won (Is everything signed and ready?)
1. Contract signed (blocking)
2. Payment terms agreed (blocking)
3. Onboarding kickoff scheduled (blocking)
4. Internal handoff complete (blocking)
5. CRM deal record complete (blocking)

## Maturity Scale (0-5)
0 = None | 1 = Informal | 2 = Partial | 3 = Structured | 4 = Enforced | 5 = Data-Validated
"""

CONSTRAINTS = """# Revenue Scaling Constraints

Every business faces one **dominant constraint** — the single bottleneck that, if removed, would unlock the most growth.

## The 4 Constraints

### 1. Lead Generation
**Symptom:** Not enough prospects entering the pipeline.
**Diagnostic:** Pipeline below 3x coverage? Sales team idle? Channels producing fewer leads?
**Causes:** Insufficient marketing investment, wrong channels, weak brand, no referral engine.
**Focus:** Growth Engine (early stages) — Stages 1-3 of Customer Value Journey.
**Revenue Formula Lever:** Traffic (VM1) + CR1 (Visit → Lead)

### 2. Conversion
**Symptom:** Prospects enter but don't buy.
**Diagnostic:** Win rate below 20%? Deals stall at specific stages? Long sales cycles?
**Causes:** Weak discovery, poor solution-problem fit, pricing misalignment, no urgency, wrong ICP.
**Focus:** Growth Engine (late stages) — Pipeline architecture, SPICED execution.
**Revenue Formula Lever:** CR2-CR5 (Lead → Won)

### 3. Delivery
**Symptom:** Can't fulfill at scale — quality drops with growth.
**Diagnostic:** Turning away business? Satisfaction declining? Timelines slipping? Key-person dependency?
**Causes:** No standardized process, founder dependency, no playbooks, hiring can't keep up.
**Focus:** Fulfillment Engine — Standardization (70/30 rule), playbooks, hiring.
**Revenue Formula Lever:** NRR (Retention Formula)

### 4. Profitability
**Symptom:** Revenue grows but profit doesn't.
**Diagnostic:** Gross margin below 50%? Revenue requires proportional team growth? Discounting to close?
**Causes:** Underpricing, scope creep, inefficient delivery, wrong service mix, overhead growth.
**Focus:** All engines (efficiency focus) — Pricing, productization, Innovation Engine.
**Revenue Formula Lever:** ACV + NRR

## Constraint → Revenue Formula Bridge

| Constraint | Revenue Formula Lever(s) |
|---|---|
| Lead Generation | VM1 (Visitors) + CR1 |
| Conversion | CR2-CR5 |
| Delivery | NRR |
| Profitability | ACV + NRR |

## Quick Diagnostic: Hormozi's 4 Levers
Revenue = Traffic × Conversion × Price × (1/Churn)
The lever with the biggest gap to benchmark has the most upside.
"""

SIGNAL_TAXONOMY = """# Signal Taxonomy (6 Types)

Every GTM change must be backed by a signal — no change without evidence.

## The 6 Signal Types

| Signal Type | What It Detects | Recommended Actions |
|---|---|---|
| **win_loss_pattern** | Win rates, loss reasons, deal outcomes by segment/persona/channel | ICP refinement, persona update, qualification rule change |
| **conversion_drop_off** | Stage-to-stage conversion rates below benchmark or declining | Pipeline stage exit criteria update, SLA adjustment |
| **velocity_anomaly** | Time-in-stage significantly above or below benchmark | Stage SLA change, process bottleneck investigation |
| **spiced_frequency** | Recurring pain points, impacts, or critical events across deals | Messaging update, positioning refinement |
| **attribution_shift** | Channel performance changes, pipeline source trends | Channel strategy change, campaign targeting update, budget reallocation |
| **data_quality** | Missing fields, incomplete records, data gaps | HubSpot field enforcement, data hygiene campaign |

## Evidence-First Workflow

1. **Detect** — Run analysis tools to identify signals
2. **Classify** — Map finding to one of 6 signal types
3. **Propose** — Draft a GTM commit with signal_type, signal_source, signal_data
4. **Review** — Human reviews the commit proposal
5. **Deploy** — Apply the change to the GTM system
6. **Measure** — Track impact against measurement plan

## Signal Structure

Each signal returns:
- signal_type — One of the 6 types
- signal_name — Human-readable description
- signal_strength — 0.0 to 1.0 (higher = stronger evidence)
- evidence — Structured data supporting the finding
- recommended_action — What to do about it
"""

REVENUE_FORMULA = """# Revenue Formula

## Winning by Design Acquisition Formula

```
ARR = Visitors × CR1 × CR2 × CR3 × CR4 × CR5 × ACV × Frequency
```

| Stage | Metric | Benchmark |
|---|---|---|
| VM1 → VM2 | CR1 (Visit → Lead) | 18-20% |
| VM2 → VM3 | CR2 (Lead → Qualified) | 15-18% |
| VM3 → VM4 | CR3 (Qualified → Opp) | 80-85% |
| VM4 → VM5 | CR4 (Opp Progression) | 25-30% |
| VM5 → Won | CR5 (Win Rate) | 30-80% |

**Key Insight:** Because the formula is multiplicative, improving any single conversion rate has a cascading effect. A 10% improvement at the weakest link often yields more revenue than doubling traffic.

## Weakest Link Analysis

The conversion rate with the biggest gap to benchmark is the highest-leverage improvement point.

## Compound Improvement Model

The formula is multiplicative, not additive:
```
Current:  1,000 leads × 5% × $50K = $2.5M
Improved: 1,100 leads × 5.5% × $55K = $3.3M (+33%)
```
A 10% improvement at each of 3 points produces a 33% compound effect.

## Retention Formula (NRR Compounding)

```
LTV = Σ(t=1 to lifetime) [Base ARR × NRR^t]
```

| NRR | Year 1 | Year 3 | Year 5 | 5-Year LTV (per $100K) |
|---|---|---|---|---|
| 90% | $100K | $73K | $59K | $410K |
| 100% | $100K | $100K | $100K | $500K |
| 110% | $100K | $121K | $161K | $611K |
| 120% | $100K | $144K | $249K | $744K |

At 110% NRR, a customer's value grows 61% over 5 years without new sales effort.
"""

GTM_COMMIT_ANATOMY = """# GTM Commit Anatomy

Every GTM change follows a structured commit format — just like code commits, but for your revenue strategy.

## The 6 Components

### 1. Intent (Why)
What is the purpose of this change? Why now? What signal triggered it?
- Clear, concise description of the change
- Links to the signal type that prompted it

### 2. Diff (What Changes)
Structured before/after comparison:
- **Before:** Current state of the GTM element
- **After:** Proposed new state
- Must be specific enough to implement

### 3. Impact Surface (What's Affected)
Downstream systems that will be affected by this change:
- CRM automation, reporting, forecasting
- Sales process, marketing campaigns
- Content, messaging, positioning

### 4. Risk Level (How Risky)
Based on entity type and change magnitude:
- **Low:** Playbook updates, minor messaging tweaks
- **Medium:** Scoring model changes, exit criteria updates, persona refinements
- **High:** ICP redefinition, pipeline restructure, GTM motion changes

### 5. Evidence (Proof)
The signal data that justifies the change:
- Signal type (from 6-type taxonomy)
- Signal strength (0.0-1.0)
- Structured evidence data

### 6. Measurement Plan (How We'll Know)
What metric should move, and by when:
- Metrics to watch (2-3 specific KPIs)
- Measurement window (30-90 days)
- Success criteria (what "better" looks like)
- Review date (calendar reminder)

## Entity Types

| Entity | Risk | Blast Radius | Reviewers |
|---|---|---|---|
| ICP Definition | Medium | High | Marketing Lead, CEO |
| Buyer Persona | Low | Medium | Marketing Lead |
| Positioning | Medium | High | Marketing Lead, CEO |
| Pipeline Stage | High | High | RevOps Lead, CEO |
| Exit Criteria | Medium | Medium | RevOps Lead |
| GTM Motion | High | High | RevOps Lead, CEO |
| Scoring Model | Medium | Medium | Sales Lead |
| Playbook | Low | Low | Sales Lead |
"""


def get_resource(name: str) -> str:
    """Get a methodology resource by name."""
    resources = {
        "scoring-model": SCORING_MODEL,
        "tier-definitions": TIER_DEFINITIONS,
        "rfm-segments": RFM_SEGMENTS,
        "spiced-framework": SPICED_FRAMEWORK,
        "value-engines": VALUE_ENGINES,
        "exit-criteria": EXIT_CRITERIA,
        "constraints": CONSTRAINTS,
        "signal-taxonomy": SIGNAL_TAXONOMY,
        "revenue-formula": REVENUE_FORMULA,
        "gtm-commit-anatomy": GTM_COMMIT_ANATOMY,
    }
    return resources.get(name, f"Unknown resource: {name}")


def list_resources() -> list[dict]:
    """List all available methodology resources."""
    return [
        {"uri": "methodology://scoring-model", "name": "ICP Scoring Model", "description": "14.5-point ICP scoring model reference"},
        {"uri": "methodology://tier-definitions", "name": "Tier Definitions", "description": "4-tier classification system"},
        {"uri": "methodology://rfm-segments", "name": "RFM Segments", "description": "11 RFM segment definitions"},
        {"uri": "methodology://spiced-framework", "name": "SPICED Framework", "description": "SPICED discovery extraction reference"},
        {"uri": "methodology://value-engines", "name": "Value Engines", "description": "3 Value Engines: Growth, Fulfillment, Innovation"},
        {"uri": "methodology://exit-criteria", "name": "Exit Criteria", "description": "Pipeline stage exit criteria framework"},
        {"uri": "methodology://constraints", "name": "Scaling Constraints", "description": "4 scaling constraints with diagnostic criteria"},
        {"uri": "methodology://signal-taxonomy", "name": "Signal Taxonomy", "description": "6 signal types for evidence-backed GTM intelligence"},
        {"uri": "methodology://revenue-formula", "name": "Revenue Formula", "description": "WbD multiplicative pipeline model + NRR compounding"},
        {"uri": "methodology://gtm-commit-anatomy", "name": "GTM Commit Anatomy", "description": "5-component structure for version-controlled GTM changes"},
    ]
