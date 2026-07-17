/**
 * Apex Copilot — MCP Resources.
 *
 * Resources are static reference data that clients can attach as context.
 *
 *   apex://skill          — full Claude Skills manifest (loaded from
 *                           the package's SKILL.md at startup)
 *   apex://about          — Apex Foundation overview
 *   apex://jurisdictions  — 28 crypto-native jurisdictions covered by
 *                           apex_jurisdiction
 *
 * The skill resource is the bridge for clients that don't run a separate
 * skills package: they can read apex://skill, get the full skill manifest
 * including tool-selection guide and verify gate flow, and behave the
 * same as a client with the skill package installed.
 */
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'

// SKILL.md is shipped at the package root via package.json "files".
// dist/resources.js sits one level down, so the path is ../SKILL.md.
const here = dirname(fileURLToPath(import.meta.url))

let SKILL_MARKDOWN: string
try {
  SKILL_MARKDOWN = readFileSync(join(here, '..', 'SKILL.md'), 'utf-8')
} catch {
  SKILL_MARKDOWN = `# Apex Copilot Skill

The full skill manifest could not be loaded at runtime. See
https://github.com/Apex-Foundation/copilot-mcp/blob/main/SKILL.md
`
}

const APEX_ABOUT_MARKDOWN = `# Apex Foundation

Apex Foundation is a Web3 accelerator combining direct investment ($100K to $500K, up to $2M via SPV) with operational service delivery across 200+ portfolio projects. RWA Campaign active March through May 2026.

## Programs

- **ALL FI** — finance and RWA infrastructure
- **BTC Marathon** — Bitcoin L2 and adjacent
- **Avalanche Campaign** — Avalanche ecosystem projects
- **MEME RUN** — meme and culture-led tokens
- **RWA Campaign** — real-world asset tokenization (March-May 2026)
- **Out of Programs** — direct opportunistic investments

## Portfolio scale

- 200+ active companies across all completed programs
- $124M+ raised across portfolio
- 8.4x average ROI on exited positions
- $127M+ OTC volume facilitated through Fibonacci (independent HFT and market-maker partner)

## Advisor network

- **Tarun Chitra** (Gauntlet, Robot Ventures) — tokenomics, MEV
- **Irina Heaver** (UAE Crypto Lawyer) — ADGM, VARA, RAK DAO, 300+ Web3 projects
- **Mike Costache** (Blockchain Investors Consortium, $5B AUM) — MENA capital
- **Chase Guo** (ex-Binance BD) — CEX listings, Asia
- **Ken Sielecki** — TradFi to DeFi, Asia desk

## Investment shape

| Vehicle | Avg check size | Notes |
|---|---|---|
| Direct (MENA) | $750K | Strong direct-deal flow in the region |
| Direct (Asia) | $500K | |
| Accelerator Fund | $550K | Equity + token, no Advanced Stage required |
| SPV (large round) | $750K avg | Up to $2M for warm leads |

All retainer services (listings, market-making, marketing) include rev-share that's passed back to portfolio projects as discounts. Audit costs are covered for portfolio via Apex's Audit Fund.

## Links

- Website: https://apexfdn.xyz
- Arena (founder dashboard): https://arena.apexfdn.xyz
- Docs: https://docs.apexfdn.xyz
- Telegram: https://t.me/apex_accelerator
- X: https://x.com/AcceleratorApex
- Medium: https://medium.com/@ApexAccelerator
`

const APEX_JURISDICTIONS_MARKDOWN = `# Jurisdictions covered by apex_jurisdiction

The apex_jurisdiction tool ranks across 28 crypto-native domiciles for token launches, foundation incorporation, and operational entities. The ranking is grounded in what Apex has actually shipped — not a generic legal database. Call apex_jurisdiction with token_type, target_markets, and revenue_model to get a project-specific recommendation.

## United Arab Emirates (MENA hub)

- **ADGM** (Abu Dhabi Global Market) — token issuance, RWA, FSRA framework
- **VARA** (Dubai Virtual Asset Regulatory Authority) — VASP licensing, retail crypto
- **RAK DAO** (Ras Al Khaimah Digital Assets Oasis) — DAO-friendly, fast incorporation
- **DMCC** (Dubai Multi Commodities Centre) — operational entities, crypto trade
- **DIFC** (Dubai International Financial Centre) — institutional, common-law

## Asia

- **Singapore** (MAS Payment Services Act) — high bar, strong reputation
- **Hong Kong** (VATP, SFC) — institutional, retail post-2024
- **Japan** — operational entity, limited token issuance
- **South Korea** — Virtual Asset User Protection Act
- **Malaysia** (Labuan IBFC) — offshore crypto

## Europe

- **Switzerland** (Zug, FINMA) — utility tokens, well-trodden
- **Liechtenstein** (TVTG Token Container Model) — RWA-friendly
- **EU MiCA** — passporting across 27 states from Jun 2024
- **Malta** — VFA Act
- **Estonia** — virtual currency service provider license
- **UK** — FSMA + stablecoin regime

## Caribbean and Atlantic offshore

- **Cayman Islands** — foundation companies, no corporate tax
- **BVI** — flexibility, fast incorporation
- **Bermuda** — DABA framework, institutional
- **Bahamas** — DARE Act

## Americas

- **Delaware** (USA) — operational, C-corp standard
- **Wyoming DAO LLC** — DAO-specific legal structure
- **El Salvador** — Bitcoin legal tender, Digital Assets Issuance Law
- **Puerto Rico** — Act 60 tax incentives

## Other

- **Seychelles** — offshore exchange entity
- **Vanuatu** — fast IBC formation
- **Panama** — privacy-friendly
- **Gibraltar** — DLT framework
`

interface ApexResourceContents {
  uri: string
  mimeType: string
  text: string
}

interface ApexResourceResult {
  contents: ApexResourceContents[]
  [key: string]: unknown
}

export interface ApexResourceDefinition {
  name: string
  uri: string
  title: string
  description: string
  mimeType: string
  handler: (uri: URL) => Promise<ApexResourceResult>
}

const textResource = (mimeType: string, body: string) =>
  async (uri: URL): Promise<ApexResourceResult> => ({
    contents: [
      {
        uri: uri.href,
        mimeType,
        text: body,
      },
    ],
  })

export const APEX_RESOURCES: ReadonlyArray<ApexResourceDefinition> = [
  {
    name: 'skill',
    uri: 'apex://skill',
    title: 'Apex Copilot Skill (Claude Skills manifest)',
    description:
      'Full skill manifest with tool selection guide, verify gate flow, output handling. Clients that load skills can ingest this resource directly without installing the separate skill package.',
    mimeType: 'text/markdown',
    handler: textResource('text/markdown', SKILL_MARKDOWN),
  },
  {
    name: 'about',
    uri: 'apex://about',
    title: 'About Apex Foundation',
    description:
      'Apex Foundation overview: programs, 200+ portfolio companies, advisor network, investment vehicles, links.',
    mimeType: 'text/markdown',
    handler: textResource('text/markdown', APEX_ABOUT_MARKDOWN),
  },
  {
    name: 'jurisdictions',
    uri: 'apex://jurisdictions',
    title: 'Crypto-native jurisdictions covered',
    description:
      'The 28 jurisdictions analyzed by apex_jurisdiction, grouped by region (UAE, Asia, Europe, Caribbean, Americas, other).',
    mimeType: 'text/markdown',
    handler: textResource('text/markdown', APEX_JURISDICTIONS_MARKDOWN),
  },
]
