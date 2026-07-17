# Architecture

## Overview

Artefact MCP Server is a STDIO-based MCP server built with FastMCP 2.x. It exposes 3 tools and 4 resources through the Model Context Protocol.

```
┌─────────────────────────────────────────────────┐
│                  MCP Client                      │
│         (Claude, Cursor, Windsurf)               │
└──────────────────┬──────────────────────────────┘
                   │ STDIO (JSON-RPC)
┌──────────────────▼──────────────────────────────┐
│              FastMCP Server                       │
│         server.py (entry point)                  │
│                                                  │
│  ┌─────────┐  ┌─────────┐  ┌──────────────┐    │
│  │ run_rfm │  │ qualify │  │ score_pipeline│    │
│  └────┬────┘  └────┬────┘  └──────┬───────┘    │
│       │            │               │             │
│  ┌────▼────────────▼───────────────▼───────┐    │
│  │              Core Engines                │    │
│  │  rfm_scorer.py  icp_scorer.py           │    │
│  │  segmenter.py   hubspot_client.py       │    │
│  └─────────────────┬───────────────────────┘    │
│                    │                             │
│  ┌─────────────────▼───────────────────────┐    │
│  │           License Gate                   │    │
│  │  Free: sample data only                  │    │
│  │  Pro/Enterprise: HubSpot live data       │    │
│  └─────────────────┬───────────────────────┘    │
└────────────────────┼────────────────────────────┘
                     │ HTTPS
          ┌──────────▼──────────┐
          │   HubSpot API v3    │
          │  (deals, companies, │
          │   contacts, etc.)   │
          └─────────────────────┘
```

## Directory Structure

```
src/artefact_mcp/
├── __init__.py              # Version metadata
├── server.py                # FastMCP server, tool registration, license check
├── tools/
│   ├── rfm.py              # RFM analysis tool (sample data + HubSpot)
│   ├── icp.py              # ICP qualification tool
│   └── pipeline.py         # Pipeline health scoring tool
├── core/
│   ├── rfm_scorer.py       # RFM scoring engine (4 presets)
│   ├── segmenter.py        # 11-segment classifier + ICP pattern extractor
│   ├── icp_scorer.py       # 14.5-point ICP scoring model
│   ├── hubspot_client.py   # HubSpot API v3 client (httpx)
│   └── license.py          # LemonSqueezy license validation + cache
└── resources/
    └── methodology.py      # Static methodology resources (4 URIs)
```

## Data Flow

### RFM Analysis (`run_rfm`)

```
Input: source, industry_preset
  ↓
License Check → blocks HubSpot for free tier
  ↓
Data Source: HubSpot API or sample data
  ↓
RFM Scorer → scores Recency (1-5), Frequency (1-5), Monetary (1-5)
  ↓
Segmenter → classifies into 11 segments (Champions, Loyal, etc.)
  ↓
ICP Analyzer → extracts patterns from top performers
  ↓
Output: scored clients, segment distribution, ICP patterns, tier recommendations
```

### ICP Qualification (`qualify`)

```
Input: company_id (HubSpot) OR company_data (manual JSON)
  ↓
License Check → blocks HubSpot ID lookup for free tier
  ↓
Data Source: HubSpot company fetch or direct data
  ↓
ICP Scorer → 3 dimensions:
  - Firmographic Fit (5 pts): industry, revenue, employees, geography
  - Behavioral Fit (5 pts): tech stack, growth signals, engagement, purchase history
  - Strategic Fit (4.5 pts): decision-maker access, budget authority, alignment
  ↓
Exclusion Check → hard disqualifiers (non-B2B, too small, etc.)
  ↓
Tier Classification → Ideal (11.5+) / Strong (8.5+) / Moderate (5.5+) / Poor (<5.5)
  ↓
Output: score breakdown, tier, recommended action, engagement strategy
```

### Pipeline Health (`score_pipeline_health`)

```
Input: pipeline_id (optional), source
  ↓
License Check → blocks HubSpot for free tier
  ↓
Data Source: HubSpot open deals or sample deals
  ↓
Velocity Calculator → avg days per stage, bottleneck identification
  ↓
Conversion Analyzer → stage-to-stage conversion rates
  ↓
Risk Detector → stalled deals, past-due deals, long-running deals
  ↓
Health Scorer → composite 0-100 score with penalties/bonuses
  ↓
Output: health score, velocity metrics, conversion rates, at-risk deals, stage distribution
```

## Scoring Engines

### RFM Scorer

Four preset configurations with different thresholds:

| Preset | Recency Thresholds | Frequency Scale | Use Case |
|--------|--------------------|-----------------|----------|
| Default | 30/90/180/365 days | 1/3/5/10 txns | General B2B |
| B2B Service | 60/120/240/450 days | 1/2/4/8 txns | Consulting, agencies |
| SaaS | 30/60/120/240 days | 2/5/10/20 txns | Software subscriptions |
| Manufacturing | 90/180/365/540 days | 1/2/3/6 txns | Industrial, long cycles |

Each dimension scored 1-5. Total RFM score: 3-15.

### 11-Segment Classification

| Segment | R | F | M | Description |
|---------|---|---|---|-------------|
| Champions | 5 | 5 | 4-5 | Best customers |
| Loyal Customers | 4-5 | 4-5 | 3-5 | Consistent high performers |
| Potential Loyalists | 4-5 | 2-3 | 2-3 | Recent, growing |
| New Customers | 5 | 1 | any | Just acquired |
| Promising | 4 | 1 | 1-2 | Recent first-timers |
| Need Attention | 3 | 3 | 3 | Average, declining |
| About to Sleep | 2-3 | 1-2 | 1-2 | Cooling off |
| At Risk | 2 | 3-5 | 3-5 | Used to be active |
| Can't Lose Them | 1-2 | 4-5 | 4-5 | High value, gone quiet |
| Hibernating | 1-2 | 1-2 | 1-2 | Long inactive |
| Lost | 1 | 1 | 1 | Gone |

## Dependencies

- **fastmcp>=2.0** — MCP protocol server framework
- **httpx>=0.25.0** — Async-capable HTTP client for HubSpot API

No pandas, numpy, or heavy data libraries. All scoring is pure Python.

## License Gating

```
No ARTEFACT_LICENSE_KEY → Free tier → sample data only
Valid key + Pro variant → Pro tier → HubSpot live data
Valid key + Enterprise variant → Enterprise tier → Pro + custom presets
```

License validated against LemonSqueezy API at startup, cached locally for 24 hours (7-day offline grace period). Keys are hashed (SHA256) before local storage.
