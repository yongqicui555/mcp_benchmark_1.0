/**
 * Apex Copilot — MCP Prompts.
 *
 * Prompts are invokable workflows the user can trigger from their MCP
 * client (e.g. Claude Desktop's prompt picker, Cursor's command palette).
 * Each prompt collects structured arguments and returns a primed user
 * message that points the assistant at the right Apex tool with the
 * right framing.
 *
 * These complement the SKILL.md / instructions guidance — the skill
 * teaches the assistant *when* to reach for a tool. Prompts give the
 * user a *one-click handle* to invoke the same workflow without typing
 * out the framing themselves.
 */
import { z } from 'zod'

export interface ApexPromptMessage {
  role: 'user' | 'assistant'
  content: { type: 'text'; text: string }
}

export interface ApexPromptResult {
  messages: ApexPromptMessage[]
  [key: string]: unknown
}

export interface ApexPromptDefinition {
  name: string
  title: string
  description: string
  argsSchema: z.ZodRawShape
  handler: (args: Record<string, unknown>) => ApexPromptResult
}

const userText = (text: string): ApexPromptResult => ({
  messages: [
    {
      role: 'user' as const,
      content: { type: 'text' as const, text },
    },
  ],
})

const str = (args: Record<string, unknown>, key: string, fallback = '(not provided)'): string => {
  const v = args[key]
  return typeof v === 'string' && v.trim().length > 0 ? v : fallback
}

const opt = (args: Record<string, unknown>, key: string): string | undefined => {
  const v = args[key]
  return typeof v === 'string' && v.trim().length > 0 ? v : undefined
}

export const APEX_PROMPTS: ReadonlyArray<ApexPromptDefinition> = [
  {
    name: 'score-my-project',
    title: 'Score my Web3 project',
    description:
      'Run Apex Score — 0-100 composite across team, product, traction, defensibility, capital efficiency, tokenomics, compliance, narrative. 85+ clears the bar for skipping standard Apex due diligence.',
    argsSchema: {
      projectName: z.string().describe('Project name'),
      description: z
        .string()
        .describe('Project description: problem, solution, target user, current stage'),
      projectUrl: z
        .string()
        .optional()
        .describe('Optional URL: website, GitHub, whitepaper, or X account'),
    },
    handler: (args) => {
      const url = opt(args, 'projectUrl')
      return userText(
        `Please run apex_score on my project and walk me through the results.

Project: ${str(args, 'projectName')}
${url ? `URL: ${url}\n` : ''}
Description:
${str(args, 'description')}

After running apex_score:
- Lead with the composite score and the per-dimension breakdown.
- Surface the weakest dimensions and the most concrete fixes.
- If composite is 85 or higher, note that Apex's bar for skipping standard due diligence has been cleared.`,
      )
    },
  },

  {
    name: 'find-jurisdiction',
    title: 'Find the best jurisdiction for my token',
    description:
      'Get jurisdictional analysis across 28 crypto-native domiciles (UAE, Singapore, Cayman, BVI, Switzerland, Liechtenstein, EU MiCA, Wyoming DAO LLC, and more).',
    argsSchema: {
      tokenType: z
        .string()
        .describe('Token type: utility, governance, RWA, stablecoin, security, gaming, etc.'),
      targetMarkets: z
        .string()
        .describe('Target markets (countries or regions where the token will be available to users)'),
      revenueModel: z
        .string()
        .describe('Revenue model: fees, subscription, treasury yield, ad-share, etc.'),
    },
    handler: (args) =>
      userText(
        `Please run apex_jurisdiction for my token launch.

Token type: ${str(args, 'tokenType')}
Target markets: ${str(args, 'targetMarkets')}
Revenue model: ${str(args, 'revenueModel')}

After the analysis:
- Lead with the top 1-2 jurisdictions that actually fit, with risk level and expected timeline for each.
- Explain why each fits and what Apex's experience with that jurisdiction looks like.
- Flag any high-risk patterns (securities exposure, gambling regs, KYC tier mismatches).`,
      ),
  },

  {
    name: 'find-investors',
    title: 'Find investors for my project',
    description:
      'Match a project against Web3 VCs, angels, and CEX venture arms. Apex direct-relationship funds surface above the cold list.',
    argsSchema: {
      projectName: z.string().describe('Project name'),
      description: z.string().describe('Project description'),
      roundSize: z.string().describe('Round size, e.g. "$2M"'),
      roundType: z.string().describe('Round type: pre-seed, seed, series A, etc.'),
    },
    handler: (args) =>
      userText(
        `Please run apex_fund_match for my fundraise.

Project: ${str(args, 'projectName')}
Description:
${str(args, 'description')}

Round: ${str(args, 'roundType')} of ${str(args, 'roundSize')}

After matching:
- Lead with the top 3-5 funds ranked by fit.
- For each, surface the thesis fit and the warm-intro probability through the Apex network.
- Flag any funds where the check size mismatches our round, so I don't waste time on misfits.`,
      ),
  },

  {
    name: 'match-portfolio',
    title: 'Compare against the Apex portfolio',
    description:
      'Find the most similar projects in the Apex portfolio (200+ projects across all programs).',
    argsSchema: {
      projectName: z.string().describe('Project name'),
      description: z
        .string()
        .describe('Project description: vertical, stage, what makes it different'),
    },
    handler: (args) =>
      userText(
        `Please run apex_portfolio_match on my project to see who in the Apex portfolio is closest.

Project: ${str(args, 'projectName')}
Description:
${str(args, 'description')}

After matching:
- List the top 3-5 closest portfolio projects with similarity scores.
- For each match, surface the founder-applicable lesson: what worked, what to avoid, what they would do differently.`,
      ),
  },

  {
    name: 'audit-contract',
    title: 'Pre-audit security review of a smart contract',
    description:
      'Static analysis plus LLM review for Solidity (Slither + Claude) or Rust/Solana (LLM checklist). Pre-audit triage — not a replacement for a paid audit at TGE.',
    argsSchema: {
      repoOrSource: z
        .string()
        .describe('GitHub repo URL (e.g. github.com/Uniswap/v4-core) or pasted Solidity / Rust source'),
      language: z.string().describe('Language: solidity or rust'),
    },
    handler: (args) =>
      userText(
        `Please run apex_code_review on this contract.

Source: ${str(args, 'repoOrSource')}
Language: ${str(args, 'language')}

After the analysis:
- Show the composite 0-100 score with the per-dimension breakdown.
- Show every high-severity finding in full: file, line, description, recommended remediation.
- Collapse medium / low / info findings to counts unless I ask for detail.
- Remind me this is pre-audit triage and that a paid audit at TGE is still required.`,
      ),
  },

  {
    name: 'find-hackathons',
    title: 'Find Web3 hackathons relevant to my project',
    description:
      'Surface upcoming Web3 hackathons matching the project — chain, topic, prize pool, deadline. Also surfaces past winners as design references.',
    argsSchema: {
      topics: z
        .string()
        .describe('Topics: DeFi, infra, RWA, AI, gaming, meme, social, etc. (comma-separated is fine)'),
      chains: z
        .string()
        .optional()
        .describe('Optional chain filter: Ethereum, Solana, Base, Avalanche, Bitcoin, etc.'),
    },
    handler: (args) => {
      const chains = opt(args, 'chains')
      return userText(
        `Please run apex_hackathons for me.

Topics: ${str(args, 'topics')}
${chains ? `Chains: ${chains}\n` : ''}
After the results:
- Lead with the hackathons that fit best by prize pool and deadline.
- Flag any with downstream funding tracks (winners often get cheques from sponsoring funds — note which).
- Surface 1-2 past-winner projects if their build is close to what I'm doing, so I can study what worked.`,
      )
    },
  },

  {
    name: 'check-twitter',
    title: 'Check a Twitter / X account for Web3 credibility',
    description:
      'Audience quality scan: real followers vs farmed, engagement authenticity, KOL tier, mentions, overlap with Apex-network funds.',
    argsSchema: {
      handle: z.string().describe('Twitter / X handle, without the @'),
    },
    handler: (args) =>
      userText(
        `Please run apex_twitter on @${str(args, 'handle')}.

After the scan:
- Lead with the credibility signal: real KOL tier vs purchased followers vs mixed.
- Surface the engagement rate, account age, and overlap with Apex-network funds.
- Flag any red patterns (sudden follower spikes, shill loops, low original-content ratio).
- Treat the output as a signal, not a verdict.`,
      ),
  },

  {
    name: 'full-diligence',
    title: 'Full Apex diligence package',
    description:
      'Run a full Apex pass: score → portfolio match → jurisdiction (if token type given) → fund match (if round size given). Burns through the verify gate — use deliberately.',
    argsSchema: {
      projectName: z.string().describe('Project name'),
      description: z.string().describe('Detailed project description'),
      projectUrl: z.string().optional().describe('Optional project URL'),
      tokenType: z.string().optional().describe('Token type, if there is a token component'),
      roundSize: z.string().optional().describe('Round size, if fundraising'),
    },
    handler: (args) => {
      const url = opt(args, 'projectUrl')
      const tokenType = opt(args, 'tokenType')
      const roundSize = opt(args, 'roundSize')
      const steps = [
        '1. apex_score — get the composite score',
        '2. apex_portfolio_match — find similar Apex portfolio projects',
        tokenType
          ? '3. apex_jurisdiction — recommend a domicile'
          : '3. Skip apex_jurisdiction (no token type provided)',
        roundSize
          ? '4. apex_fund_match — surface investors and warm-intro probability'
          : '4. Skip apex_fund_match (no round size provided)',
      ].join('\n')

      return userText(
        `Run the full Apex diligence package on my project.

Project: ${str(args, 'projectName')}
${url ? `URL: ${url}\n` : ''}${tokenType ? `Token type: ${tokenType}\n` : ''}${roundSize ? `Round size: ${roundSize}\n` : ''}
Description:
${str(args, 'description')}

Run in this order:
${steps}

Synthesize at the end:
- What is the strongest angle right now.
- What is the biggest gap I should close before fundraising or launching.
- What I should do in the next two weeks.

The verify gate may fire between calls. Walk me through verification if it does — show the shell command, ask permission, run it, capture the code, call apex_verify, then continue.`,
      )
    },
  },
]
