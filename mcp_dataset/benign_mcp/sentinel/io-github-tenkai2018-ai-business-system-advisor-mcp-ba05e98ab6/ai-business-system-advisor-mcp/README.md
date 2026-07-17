# AI Business System Advisor MCP

[![smithery badge](https://smithery.ai/badge/prodxsolution/ai-business-system-advisor-mcp)](https://smithery.ai/servers/prodxsolution/ai-business-system-advisor-mcp)

Find the safest first AI workflow for your business.

AI Business System Advisor MCP helps founders, operators, consultants, and small teams review business workflows, AI opportunities, trust/control risks, and implementation readiness before building AI agents or automation.

It produces a public-safe mini review, recommends a practical first AI-human workflow, and exports a structured intake packet for deeper review or implementation planning.

This MCP is designed for business-system thinking, not generic chatbot recommendations or tool-first automation.

## What It Does

- Reviews business context, target customers, offers, workflows, and goals.
- Identifies operational bottlenecks and customer journey friction.
- Evaluates AI workflow ideas for value, readiness, and trust/control risk.
- Recommends a narrow first AI-human workflow with review and escalation rules.
- Generates mini reports and structured intake packets.

## Who It Is For

- Solo founders
- Service businesses
- B2B consultants
- Agency owners
- Operators
- Small teams exploring AI agents or automation

## Problems It Helps Solve

- Which workflow should I automate first?
- Is this AI agent idea safe for my customer experience?
- Where should humans stay in control?
- What trust/control risks exist in this workflow?
- What information is missing before implementation?
- How should I prepare this business for AI automation?

## Use With MCP Clients

For Claude Desktop, Cursor, Windsurf, Codex, or another stdio MCP client:

```json
{
  "mcpServers": {
    "ai-business-system-advisor": {
      "command": "npx",
      "args": ["-y", "ai-business-system-advisor-mcp"]
    }
  }
}
```

You can also run the package directly:

```bash
npx -y ai-business-system-advisor-mcp
```

For remote MCP clients, use:

```text
https://mcp.prodxsolution.com/ai-business-system-advisor/mcp
```

Smithery listing:

```text
https://smithery.ai/servers/prodxsolution/ai-business-system-advisor-mcp
```

## Available Tools

- `analyze_business_context`
- `map_customer_touchpoints`
- `identify_bottlenecks`
- `evaluate_ai_opportunities`
- `assess_trust_control_risks`
- `recommend_first_workflow`
- `generate_mini_report`
- `recommend_next_step`
- `export_intake_packet`

## Available Prompts

- `run_mini_business_system_review`
- `evaluate_ai_workflow_idea`
- `prepare_diagnostic_intake`
- `governance_gap_snapshot`

## Available Resources

- Overview
- How it works
- Readiness guide
- Sample mini report
- Sample intake packet
- Privacy note

## Example Questions

Ask your AI assistant:

- Review my business and identify the safest first AI workflow to improve.
- Is this AI agent idea safe for customer support, refunds, and complaints?
- Where should humans stay in control in this workflow?
- What trust/control risks should I consider before automating this process?
- Generate a mini business system review and tell me what information is missing.
- Export an intake packet for deeper workflow review.

## Example Output

```text
Mini Business System Review

Business Snapshot:
A service agency sells conversion and landing page work to ecommerce brands. Sales capacity is constrained by manual lead research, inconsistent qualification, and proposal drafting.

Likely Bottlenecks:
- Lead research takes too long before a sales call.
- Proposal quality depends on expert availability.
- Customer-facing claims need clearer approval rules.

Recommended First Workflow:
AI prepares a lead research and qualification brief, then drafts proposal sections from approved language. A human reviews lead fit, scope, pricing, claims, and final customer-facing messages.

Trust And Control Risk:
Medium. The workflow can affect revenue, brand trust, and customer expectations, so AI should prepare work but not send promises or pricing without approval.

Success Metrics:
- qualified calls booked
- proposal cycle time
- human edit rate
- lead-to-call conversion

Missing Information:
ideal customer criteria, approved claims, disallowed claims, proposal rules, escalation triggers, and success metrics
```

## Privacy And Security

The server is read-mostly and does not intentionally persist submitted business context. Do not send passwords, API keys, raw private customer records, regulated data, or confidential contracts.

Outputs are first-pass reviews based on the information provided. They are not legal, financial, medical, HR, or compliance advice.

## Public Safety Boundary

The server uses business-facing language and refuses requests for private implementation details. Public outputs focus on business context, workflow fit, risk controls, recommended next steps, and missing information.

It does not expose protected implementation details, exact formulas, confidential designs, or client-specific confidential data.

## Roadmap

- More fictional sample reviews for common business types.
- Guided public workflow for mini reviews and intake packets.
- Additional public resources for AI workflow readiness and human review design.
