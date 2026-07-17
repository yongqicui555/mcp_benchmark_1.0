/**
 * calculate-greeks.ts — MCP tool handler for `calculate_greeks`.
 *
 * Fetches current underlying prices, computes time-to-expiry in years,
 * selects the correct pricing model (Black-Scholes for European, binomial
 * tree for American), resolves implied volatility via Newton-Raphson when
 * not supplied, then computes all Greeks (delta, gamma, theta, vega, rho).
 * Aggregates portfolio-level Greeks across all positions.
 *
 * PAID tier only. Free users receive a TierError before this handler runs,
 * but we also guard at the top of the function as defense-in-depth.
 */

import { YahooFinanceService } from "../services/yahoo-finance.js";
import {
  blackScholesPrice,
  blackScholesDelta,
  blackScholesGamma,
  blackScholesTheta,
  blackScholesVega,
  blackScholesRho,
  impliedVolatility,
  binomialTreePrice,
} from "../engine/greeks.js";
import type { BSParams } from "../engine/greeks.js";
import {
  TierError,
  ComputationError,
  InvalidInputError,
  toMcpError,
} from "../utils/errors.js";
import {
  formatNumber,
  formatPercent,
  formatCurrency,
  formatRatio,
} from "../utils/format.js";
import type { CalculateGreeksInput } from "../schemas/calculate-greeks.js";
import type { AuthContext } from "../middleware/auth.js";
import type {
  CalculateGreeksResult,
  GreekResult,
  PortfolioGreeks,
} from "../types/risk.js";

// ---------------------------------------------------------------------------
// Env / ToolResult
// ---------------------------------------------------------------------------

export interface Env {
  PRICE_CACHE: KVNamespace;
  USER_STATE: DurableObjectNamespace;
}

export interface ToolResult {
  content: [{ type: "text"; text: string }];
  isError?: boolean;
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

/** Calendar days per year (used for time-to-expiry calculation). */
const CALENDAR_DAYS_PER_YEAR = 365;

// ---------------------------------------------------------------------------
// Handler
// ---------------------------------------------------------------------------

/**
 * Handle a `calculate_greeks` tool call.
 *
 * @param input       Validated input from the Zod schema
 * @param env         Cloudflare Worker environment bindings
 * @param authContext Resolved user auth context
 */
export async function handleCalculateGreeks(
  input: CalculateGreeksInput,
  env: Env,
  authContext: AuthContext
): Promise<ToolResult> {
  // Defense-in-depth tier check.
  if (authContext.tier === "free") {
    throw new TierError("calculate_greeks");
  }

  try {
    const { options, risk_free_rate } = input;

    // --- 1. Collect unique underlying tickers ---
    const underlyings = [...new Set(options.map((o) => o.underlying))];

    // --- 2. Fetch current prices for all underlyings ---
    const av = new YahooFinanceService(env);
    const priceMap = await av.fetchMultiplePrices(underlyings, 2);

    const spotPrices: Record<string, number> = {};
    for (const ticker of underlyings) {
      const prices = priceMap[ticker];
      if (!prices || prices.length === 0) {
        throw new ComputationError(
          `Could not fetch current price for ${ticker}.`,
          "No price data returned"
        );
      }
      spotPrices[ticker] = prices[prices.length - 1].close;
    }

    // --- 3. Compute Greeks for each option position ---
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const positionResults: GreekResult[] = [];

    for (const option of options) {
      const {
        underlying,
        strike,
        expiry,
        option_type,
        style,
        quantity,
        implied_volatility: givenIV,
        market_price,
      } = option;

      const spot = spotPrices[underlying];
      if (!spot || spot <= 0) {
        throw new ComputationError(
          `Invalid spot price for ${underlying}: ${spot}`
        );
      }

      // Validate expiry is in the future
      const expiryDate = new Date(expiry);
      expiryDate.setHours(0, 0, 0, 0);
      if (expiryDate <= today) {
        throw new InvalidInputError(
          "expiry",
          expiry,
          `Expiry date ${expiry} must be in the future`
        );
      }

      // Compute time to expiry in years (calendar days)
      const msPerDay = 1000 * 60 * 60 * 24;
      const daysToExpiry =
        (expiryDate.getTime() - today.getTime()) / msPerDay;
      const timeToExpiry = daysToExpiry / CALENDAR_DAYS_PER_YEAR;

      // Resolve implied volatility
      let iv: number;
      if (givenIV != null) {
        iv = givenIV;
      } else {
        // market_price is guaranteed by the schema refine when iv is null
        if (!market_price || market_price <= 0) {
          throw new InvalidInputError(
            "market_price",
            market_price,
            "market_price must be positive when implied_volatility is not provided"
          );
        }
        try {
          iv = impliedVolatility(
            market_price,
            spot,
            strike,
            timeToExpiry,
            risk_free_rate,
            option_type
          );
        } catch (err) {
          throw new ComputationError(
            `Could not compute implied volatility for ${underlying} ${strike} ${expiry} ${option_type}: ` +
              (err instanceof Error ? err.message : String(err))
          );
        }
      }

      const bsParams: BSParams = {
        spot,
        strike,
        timeToExpiry,
        riskFreeRate: risk_free_rate,
        volatility: iv,
        optionType: option_type,
      };

      // Theoretical price: use binomial for American, Black-Scholes for European
      let theoreticalPrice: number;
      if (style === "american") {
        theoreticalPrice = binomialTreePrice(
          {
            spot,
            strike,
            timeToExpiry,
            riskFreeRate: risk_free_rate,
            volatility: iv,
            optionType: option_type,
            steps: 100,
          },
          true /* american */
        );
      } else {
        theoreticalPrice = blackScholesPrice(bsParams);
      }

      // Greeks are always computed via Black-Scholes closed-form (standard market practice
      // even for American options approximated via binomial price).
      const delta = blackScholesDelta(bsParams);
      const gamma = blackScholesGamma(bsParams);
      const theta = blackScholesTheta(bsParams);
      const vega = blackScholesVega(bsParams);
      const rho = blackScholesRho(bsParams);

      positionResults.push({
        underlying,
        strike,
        expiry,
        option_type,
        delta,
        gamma,
        theta,
        vega,
        rho,
        implied_volatility: iv,
        theoretical_price: theoreticalPrice,
      });
    }

    // --- 4. Aggregate portfolio-level Greeks (quantity-weighted) ---
    const portfolioGreeks: PortfolioGreeks = {
      delta: 0,
      gamma: 0,
      theta: 0,
      vega: 0,
      rho: 0,
    };

    for (let i = 0; i < options.length; i++) {
      const qty = options[i].quantity;
      const g = positionResults[i];
      portfolioGreeks.delta += g.delta * qty;
      portfolioGreeks.gamma += g.gamma * qty;
      portfolioGreeks.theta += g.theta * qty;
      portfolioGreeks.vega += g.vega * qty;
      portfolioGreeks.rho += g.rho * qty;
    }

    // --- 5. Build result ---
    const result: CalculateGreeksResult = {
      positions: positionResults,
      portfolio_greeks: portfolioGreeks,
      summary: buildGreeksSummary(
        options.map((o, i) => ({ ...o, ...positionResults[i] })),
        portfolioGreeks,
        spotPrices,
        risk_free_rate
      ),
    };

    return {
      content: [{ type: "text", text: JSON.stringify(result) }],
    };
  } catch (err) {
    return toMcpError(err);
  }
}

// ---------------------------------------------------------------------------
// Summary builder
// ---------------------------------------------------------------------------

interface EnrichedOption {
  underlying: string;
  strike: number;
  expiry: string;
  option_type: string;
  style: string;
  quantity: number;
  delta: number;
  gamma: number;
  theta: number;
  vega: number;
  rho: number;
  implied_volatility: number;
  theoretical_price: number;
}

function buildGreeksSummary(
  positions: EnrichedOption[],
  portfolio: PortfolioGreeks,
  spotPrices: Record<string, number>,
  riskFreeRate: number
): string {
  const lines: string[] = [];

  // Per-position section
  lines.push(`Option Greeks — ${positions.length} position${positions.length === 1 ? "" : "s"}`);
  lines.push("");

  const colW = 10;
  const header = [
    "Position".padEnd(30),
    "IV".padStart(colW),
    "Price".padStart(colW),
    "Delta".padStart(colW),
    "Gamma".padStart(colW),
    "Theta/day".padStart(colW),
    "Vega/1%".padStart(colW),
    "Rho/1%".padStart(colW),
  ].join("  ");
  lines.push(header);
  lines.push("-".repeat(header.length));

  for (const pos of positions) {
    const label = `${pos.underlying} ${pos.strike} ${pos.expiry} ${pos.option_type.toUpperCase()} x${pos.quantity}`;
    const row = [
      label.padEnd(30),
      formatPercent(pos.implied_volatility, 1).padStart(colW),
      formatCurrency(pos.theoretical_price).padStart(colW),
      formatNumber(pos.delta, 4).padStart(colW),
      formatNumber(pos.gamma, 4).padStart(colW),
      formatNumber(pos.theta, 4).padStart(colW),
      formatNumber(pos.vega, 4).padStart(colW),
      formatNumber(pos.rho, 4).padStart(colW),
    ].join("  ");
    lines.push(row);
  }

  lines.push("-".repeat(header.length));
  lines.push("");

  // Portfolio-level Greeks
  lines.push("Portfolio Greeks (quantity-weighted sum):");
  lines.push(`  Delta: ${formatNumber(portfolio.delta, 4)}  — $${formatNumber(portfolio.delta, 2)} P&L per $1 move in underlying`);
  lines.push(`  Gamma: ${formatNumber(portfolio.gamma, 4)}  — rate of delta change per $1 underlying move`);
  lines.push(`  Theta: ${formatNumber(portfolio.theta, 4)}  — daily time decay (negative = you pay theta)`);
  lines.push(`  Vega:  ${formatNumber(portfolio.vega, 4)}  — P&L per 1% change in implied volatility`);
  lines.push(`  Rho:   ${formatNumber(portfolio.rho, 4)}  — P&L per 1% change in risk-free rate (${formatPercent(riskFreeRate)})`);
  lines.push("");

  // Interpretation hints
  const absDelta = Math.abs(portfolio.delta);
  if (absDelta > 50) {
    lines.push(
      `Note: Portfolio delta of ${formatNumber(portfolio.delta, 2)} indicates significant directional exposure.`
    );
  }
  if (portfolio.theta < -10) {
    lines.push(
      `Note: Portfolio theta of ${formatNumber(portfolio.theta, 2)}/day means you are paying time decay.`
    );
  } else if (portfolio.theta > 10) {
    lines.push(
      `Note: Portfolio theta of +${formatNumber(portfolio.theta, 2)}/day means you are collecting time decay.`
    );
  }

  return lines.join("\n");
}
