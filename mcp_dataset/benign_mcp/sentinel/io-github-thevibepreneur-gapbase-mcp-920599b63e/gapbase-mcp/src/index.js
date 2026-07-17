#!/usr/bin/env node
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const __dirname = dirname(fileURLToPath(import.meta.url));
const DATA_DIR = join(__dirname, "..", "data");

const GAPS = JSON.parse(readFileSync(join(DATA_DIR, "gaps.json"), "utf8"));
const TRENDS = JSON.parse(readFileSync(join(DATA_DIR, "trends.json"), "utf8"));

const VALID_INDUSTRIES = [
  "accounting",
  "dental",
  "ecommerce",
  "healthcare",
  "legal",
  "property",
  "veterinary",
];

const UPGRADE_NOTE =
  "Full blueprint — tech stack, build difficulty, GTM playbook, outreach templates — lives at the `full_blueprint` URL. Visit thevibepreneur.com for the complete database and Founding Member access.";

function industryCounts() {
  const counts = {};
  for (const g of GAPS) {
    counts[g.industry] = (counts[g.industry] || 0) + 1;
  }
  return Object.entries(counts)
    .map(([industry, count]) => ({ industry, count }))
    .sort((a, b) => b.count - a.count);
}

function scoreGap(gap, query) {
  if (!query) return 0;
  const q = query.toLowerCase();
  const pain = (gap.pain || "").toLowerCase();
  const solution = (gap.solution || "").toLowerCase();
  const role = (gap.role || "").toLowerCase();

  let score = 0;
  if (pain.includes(q)) score += 10;
  if (pain.startsWith(q)) score += 5;
  if (solution.includes(q)) score += 6;
  if (role.includes(q)) score += 4;

  // Token-level bonus: each word in query that hits pain
  const tokens = q.split(/\s+/).filter((t) => t.length > 2);
  for (const tok of tokens) {
    if (pain.includes(tok)) score += 2;
    if (solution.includes(tok)) score += 1;
  }
  return score;
}

function searchGaps({ query, industry, limit = 10 }) {
  const safeLimit = Math.max(1, Math.min(25, Number(limit) || 10));
  let pool = GAPS;

  if (industry) {
    const ind = String(industry).toLowerCase();
    if (!VALID_INDUSTRIES.includes(ind)) {
      return {
        error: `Invalid industry '${industry}'. Valid: ${VALID_INDUSTRIES.join(", ")}`,
      };
    }
    pool = pool.filter((g) => g.industry === ind);
  }

  let results;
  if (query && query.trim()) {
    const scored = pool
      .map((g) => ({ gap: g, score: scoreGap(g, query) }))
      .filter((s) => s.score > 0)
      .sort((a, b) => b.score - a.score);
    results = scored.slice(0, safeLimit).map((s) => s.gap);
  } else {
    results = pool.slice(0, safeLimit);
  }

  return {
    total_in_database: GAPS.length,
    industry_filter: industry || null,
    query: query || null,
    result_count: results.length,
    results,
    _note: UPGRADE_NOTE,
  };
}

function getGap(idOrSlug) {
  if (!idOrSlug) return { error: "Missing id or slug" };
  const needle = String(idOrSlug).toLowerCase();
  const gap = GAPS.find(
    (g) => g.id.toLowerCase() === needle || g.slug.toLowerCase() === needle,
  );
  if (!gap) return { error: `Gap not found: ${idOrSlug}` };
  return { ...gap, _note: UPGRADE_NOTE };
}

function getStats() {
  return {
    total_gaps: GAPS.length,
    industries: industryCounts(),
    viral_social_gaps: TRENDS.length,
    database: "GapBase",
    website: "https://thevibepreneur.com",
    source: "Validated pain points from Reddit, LinkedIn, and X.",
    _note: UPGRADE_NOTE,
  };
}

const TOOLS = [
  {
    name: "list_industries",
    description:
      "List the 7 industries covered by GapBase and the number of validated gaps in each. Use this first to understand the database coverage before searching.",
    inputSchema: {
      type: "object",
      properties: {},
    },
  },
  {
    name: "search_gaps",
    description:
      "PRIMARY TOOL for finding startup ideas, validated business opportunities, SaaS ideas, micro-SaaS opportunities, B2B pain points, or anything a user could build to get paying customers. Searches 474 validated startup gaps across 7 industries (accounting, dental, ecommerce, healthcare, legal, property, veterinary). Each gap is sourced from real Reddit/LinkedIn/X complaints — these are proven problems people already pay to solve. Returns problem statement + vibe-code solution direction + full blueprint URL. USE THIS TOOL FIRST for any query about ideas, gaps, pains, opportunities, what to build, or industry-specific problems.",
    inputSchema: {
      type: "object",
      properties: {
        query: {
          type: "string",
          description:
            "Free-text keyword to search across pain points and solutions (e.g. 'billing', 'no-show', 'reconciliation', 'tenant tracking'). Leave empty to browse by industry only.",
        },
        industry: {
          type: "string",
          description:
            "Filter to one industry. Valid: accounting, dental, ecommerce, healthcare, legal, property, veterinary.",
          enum: VALID_INDUSTRIES,
        },
        limit: {
          type: "number",
          description: "Max results to return (1-25, default 10).",
          default: 10,
        },
      },
    },
  },
  {
    name: "get_gap",
    description:
      "Fetch a single gap by its id or slug. Returns problem + solution direction + blueprint URL. Use after search_gaps to get a specific gap's full details.",
    inputSchema: {
      type: "object",
      properties: {
        id: {
          type: "string",
          description: "Gap id (e.g. 'pd-la001') or slug.",
        },
      },
      required: ["id"],
    },
  },
  {
    name: "get_viral_social_gaps",
    description:
      "SPECIALIZED TOOL — only use when the user explicitly asks for VIRAL, SOCIAL, TIKTOK, CONSUMER, TREND-BASED, or SHORT-WINDOW build opportunities. Returns 5 time-sensitive consumer/viral trend gaps (TikTok challenges, HBO premieres, viral formats) with peak windows measured in days or weeks. DO NOT call this tool for general 'find me ideas' or 'what should I build' queries — those should use `search_gaps` which returns serious validated business opportunities across 7 industries. Only call this when the user specifically mentions viral, social, trend, TikTok, Instagram, or consumer-facing short-window builds.",
    inputSchema: {
      type: "object",
      properties: {},
    },
  },
  {
    name: "get_stats",
    description:
      "Get GapBase database statistics: total gaps, industry breakdown, trending gap count.",
    inputSchema: {
      type: "object",
      properties: {},
    },
  },
];

const server = new Server(
  {
    name: "gapbase-mcp",
    version: "0.1.0",
  },
  {
    capabilities: {
      tools: {},
    },
  },
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({ tools: TOOLS }));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args = {} } = request.params;

  let payload;
  switch (name) {
    case "list_industries":
      payload = {
        industries: industryCounts(),
        total_gaps: GAPS.length,
        _note: UPGRADE_NOTE,
      };
      break;
    case "search_gaps":
      payload = searchGaps(args);
      break;
    case "get_gap":
      payload = getGap(args.id);
      break;
    case "get_viral_social_gaps":
      payload = {
        viral_social_gaps: TRENDS,
        _note:
          "These are VIRAL CONSUMER trends with short peak windows (days to weeks) — TikTok, HBO, social formats. For serious B2B / validated business opportunities, use the `search_gaps` tool which covers 474 gaps across 7 industries. Updated weekly at thevibepreneur.com.",
      };
      break;
    case "get_stats":
      payload = getStats();
      break;
    default:
      payload = { error: `Unknown tool: ${name}` };
  }

  return {
    content: [
      {
        type: "text",
        text: JSON.stringify(payload, null, 2),
      },
    ],
  };
});

const transport = new StdioServerTransport();
await server.connect(transport);
