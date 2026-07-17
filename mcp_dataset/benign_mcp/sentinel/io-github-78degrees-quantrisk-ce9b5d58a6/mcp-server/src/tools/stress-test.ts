/**
 * stress-test.ts — Tool handler for the `stress_test` MCP tool.
 *
 * Tests a portfolio against historical crisis scenarios or custom shocks:
 *   1. Fetches current prices to establish portfolio value and position values
 *   2. For each historical scenario: maps every position to its GICS sector
 *      (sector-map.ts fallback first, then Alpha Vantage metadata), then
 *      applies the scenario's sector return to compute per-position P&L
 *   3. For custom shocks (PAID only): applies ticker-level shocks first,
 *      then sector-level shocks for any remaining positions, then market_shock
 *      as the catch-all fallback
 *   4. Returns StressTestResult with per-scenario breakdown and summary
 *
 * Auth and tier gating are handled upstream — this handler receives
 * pre-validated input and an already-resolved AuthContext.
 */

import type { StressTestInput, CustomShockInput } from "../schemas/stress-test.js";
import type { AuthContext } from "../middleware/auth.js";
import type { StressTestResult, ScenarioResult, PositionPnL } from "../types/risk.js";
import { YahooFinanceService } from "../services/yahoo-finance.js";
import { getScenario, getSectorReturn } from "../data/scenarios.js";
import { getSectorForTicker } from "../data/sector-map.js";
import { formatCurrency, formatPercent } from "../utils/format.js";
import { toMcpError, ComputationError } from "../utils/errors.js";

// ---------------------------------------------------------------------------
// Env bindings required by this tool
// ---------------------------------------------------------------------------

export interface StressTestEnv {
  PRICE_CACHE: KVNamespace;
}

// ---------------------------------------------------------------------------
// MCP ToolResult shape
// ---------------------------------------------------------------------------

export interface ToolResult {
  content: [{ type: "text"; text: string }];
  isError?: boolean;
}

// ---------------------------------------------------------------------------
// Handler
// ---------------------------------------------------------------------------

export async function handleStressTest(
  input: StressTestInput,
  env: StressTestEnv,
  _authContext: AuthContext
): Promise<ToolResult> {
  try {
    const { positions, scenarios, custom_shocks } = input;

    // ------------------------------------------------------------------
    // 1. Fetch current prices for all tickers
    // ------------------------------------------------------------------
    const tickers = positions.map((p) => p.ticker.toUpperCase());
    const av = new YahooFinanceService(env);

    // We only need the latest price; fetch with minimal lookback (2 days)
    const priceMap = await av.fetchMultiplePrices(tickers, 2);

    // ------------------------------------------------------------------
    // 2. Compute current position values
    // ------------------------------------------------------------------
    const positionData = positions.map((pos) => {
      const ticker = pos.ticker.toUpperCase();
      const series = priceMap[ticker];
      if (!series || series.length === 0) {
        throw new ComputationError(
          `No price data for ${ticker}. Cannot run stress test.`
        );
      }
      const price = series[series.length - 1].close;
      const value = price * pos.quantity;
      return { ticker, quantity: pos.quantity, price, value };
    });

    const portfolioValue = positionData.reduce((sum, p) => sum + p.value, 0);

    if (portfolioValue === 0) {
      throw new ComputationError("Portfolio value is zero. Check position quantities.");
    }

    // ------------------------------------------------------------------
    // 3. Resolve sectors for every position
    //    Priority: sector-map.ts (instant) → Alpha Vantage OVERVIEW (cached/API)
    // ------------------------------------------------------------------
    const sectorCache: Record<string, string> = {};

    async function getSector(ticker: string): Promise<string> {
      if (sectorCache[ticker]) return sectorCache[ticker];

      // Fast path: static sector map
      const staticSector = getSectorForTicker(ticker);
      if (staticSector !== "Unknown") {
        sectorCache[ticker] = staticSector;
        return staticSector;
      }

      // Slow path: Alpha Vantage OVERVIEW
      try {
        const meta = await av.fetchAssetMetadata(ticker);
        const sector = meta.sector ?? "Unknown";
        sectorCache[ticker] = sector;
        return sector;
      } catch {
        // If metadata fetch fails, fall back to "Unknown" — stress test will
        // use market_shock or 0 for this position
        sectorCache[ticker] = "Unknown";
        return "Unknown";
      }
    }

    // Resolve all sectors in parallel
    await Promise.all(positionData.map((p) => getSector(p.ticker)));

    // ------------------------------------------------------------------
    // 4. Run historical scenarios
    // ------------------------------------------------------------------
    const scenarioResults: ScenarioResult[] = [];

    for (const scenarioKey of scenarios) {
      const scenario = getScenario(scenarioKey);
      if (!scenario) {
        // Unknown scenario key — skip gracefully (Zod should have caught this)
        continue;
      }

      const positionPnLs: PositionPnL[] = positionData.map((pos) => {
        const sector = sectorCache[pos.ticker] ?? "Unknown";
        const shockDecimal = getSectorReturn(scenario, sector);
        // Apply shock to position market value
        const pnl = pos.value * shockDecimal;
        const pnlPercent = shockDecimal; // same as shock since pnl = value * shock
        return {
          ticker: pos.ticker,
          pnl: round(pnl, 2),
          pnl_percent: round(pnlPercent, 6),
        };
      });

      const totalPnl = positionPnLs.reduce((sum, p) => sum + p.pnl, 0);
      const totalPnlPercent = totalPnl / Math.abs(portfolioValue);

      const worstPos = positionPnLs.reduce((a, b) => (a.pnl < b.pnl ? a : b));
      const bestPos = positionPnLs.reduce((a, b) => (a.pnl > b.pnl ? a : b));

      scenarioResults.push({
        scenario: scenarioKey,
        portfolio_pnl: round(totalPnl, 2),
        portfolio_pnl_percent: round(totalPnlPercent, 6),
        worst_position: worstPos,
        best_position: bestPos,
        position_details: positionPnLs,
      });
    }

    // ------------------------------------------------------------------
    // 5. Run custom shocks (PAID tier — tier gate is upstream, but we
    //    process whatever arrives here)
    // ------------------------------------------------------------------
    if (custom_shocks && custom_shocks.length > 0) {
      for (const shock of custom_shocks) {
        const customResult = applyCustomShock(shock, positionData, sectorCache, portfolioValue);
        scenarioResults.push(customResult);
      }
    }

    // ------------------------------------------------------------------
    // 6. Build summary and return
    // ------------------------------------------------------------------
    const summary = buildSummary(scenarioResults, portfolioValue);

    const result: StressTestResult = {
      results: scenarioResults,
      portfolio_value: round(portfolioValue, 2),
      summary,
    };

    return {
      content: [{ type: "text", text: JSON.stringify(result) }],
    };
  } catch (err) {
    return toMcpError(err);
  }
}

// ---------------------------------------------------------------------------
// Custom shock application
// ---------------------------------------------------------------------------

interface PositionRecord {
  ticker: string;
  quantity: number;
  price: number;
  value: number;
}

function applyCustomShock(
  shock: CustomShockInput,
  positionData: PositionRecord[],
  sectorCache: Record<string, string>,
  portfolioValue: number
): ScenarioResult {
  const tickerShocks = shock.ticker_shocks ?? {};
  const sectorShocks = shock.sector_shocks ?? {};
  const marketShock = shock.market_shock ?? 0;

  const positionPnLs: PositionPnL[] = positionData.map((pos) => {
    let shockDecimal: number;

    if (pos.ticker in tickerShocks) {
      // Ticker-level shock takes highest priority
      shockDecimal = tickerShocks[pos.ticker];
    } else {
      const sector = sectorCache[pos.ticker] ?? "Unknown";
      if (sector in sectorShocks) {
        // Sector-level shock is second priority
        shockDecimal = sectorShocks[sector];
      } else {
        // Market-wide shock as catch-all
        shockDecimal = marketShock;
      }
    }

    const pnl = pos.value * shockDecimal;
    return {
      ticker: pos.ticker,
      pnl: round(pnl, 2),
      pnl_percent: round(shockDecimal, 6),
    };
  });

  const totalPnl = positionPnLs.reduce((sum, p) => sum + p.pnl, 0);
  const totalPnlPercent = portfolioValue !== 0 ? totalPnl / Math.abs(portfolioValue) : 0;

  const worstPos = positionPnLs.reduce((a, b) => (a.pnl < b.pnl ? a : b));
  const bestPos = positionPnLs.reduce((a, b) => (a.pnl > b.pnl ? a : b));

  return {
    scenario: shock.name,
    portfolio_pnl: round(totalPnl, 2),
    portfolio_pnl_percent: round(totalPnlPercent, 6),
    worst_position: worstPos,
    best_position: bestPos,
    position_details: positionPnLs,
  };
}

// ---------------------------------------------------------------------------
// Summary builder
// ---------------------------------------------------------------------------

function buildSummary(results: ScenarioResult[], portfolioValue: number): string {
  if (results.length === 0) {
    return "No scenarios were run.";
  }

  const lines: string[] = [
    `Stress test of ${formatCurrency(portfolioValue)} portfolio across ${results.length} scenario${results.length !== 1 ? "s" : ""}.`,
  ];

  // Worst scenario
  const worstScenario = results.reduce((a, b) =>
    a.portfolio_pnl < b.portfolio_pnl ? a : b
  );
  // Best scenario
  const bestScenario = results.reduce((a, b) =>
    a.portfolio_pnl > b.portfolio_pnl ? a : b
  );

  lines.push(
    `Worst scenario: "${worstScenario.scenario}" — portfolio ` +
      `${worstScenario.portfolio_pnl >= 0 ? "gains" : "loses"} ` +
      `${formatCurrency(Math.abs(worstScenario.portfolio_pnl))} ` +
      `(${formatPercent(worstScenario.portfolio_pnl_percent)}).`
  );

  if (results.length > 1) {
    lines.push(
      `Best scenario: "${bestScenario.scenario}" — portfolio ` +
        `${bestScenario.portfolio_pnl >= 0 ? "gains" : "loses"} ` +
        `${formatCurrency(Math.abs(bestScenario.portfolio_pnl))} ` +
        `(${formatPercent(bestScenario.portfolio_pnl_percent)}).`
    );
  }

  // Per-scenario one-liners
  for (const r of results) {
    const verb = r.portfolio_pnl >= 0 ? "+" : "";
    lines.push(
      `  ${r.scenario}: ${verb}${formatCurrency(r.portfolio_pnl)} ` +
        `(${formatPercent(r.portfolio_pnl_percent)}). ` +
        `Worst position: ${r.worst_position.ticker} (${formatPercent(r.worst_position.pnl_percent)}).`
    );
  }

  return lines.join(" ");
}

// ---------------------------------------------------------------------------
// Utility
// ---------------------------------------------------------------------------

function round(n: number, decimals: number): number {
  const factor = 10 ** decimals;
  return Math.round(n * factor) / factor;
}
