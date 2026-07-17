/**
 * correlation-matrix.ts — MCP tool handler for `correlation_matrix`.
 *
 * Fetches prices for all requested tickers, computes a pairwise correlation
 * matrix using the specified method (pearson / spearman / kendall), identifies
 * the highest- and lowest-correlated pairs, and computes eigenvalues of the
 * matrix for PCA-style risk decomposition.
 *
 * Tier gates (enforced by middleware BEFORE this handler is called):
 *   FREE  — max 10 tickers
 *   PAID  — up to 50 tickers
 *
 * Handler signature matches the rest of the tool layer:
 *   handleCorrelationMatrix(input, env, authContext) -> ToolResult
 */

import type { CorrelationMatrixInput } from "../schemas/correlation-matrix.js";
import type { AuthContext } from "../middleware/auth.js";
import type { CorrelationMatrixResult } from "../types/risk.js";

import { YahooFinanceService } from "../services/yahoo-finance.js";
import {
  buildCorrelationMatrix,
  computeEigenvalues,
} from "../engine/correlation.js";
import { calculateLogReturns } from "../engine/returns.js";
import { toMcpError } from "../utils/errors.js";
import { formatNumber, formatPercent } from "../utils/format.js";

// ---------------------------------------------------------------------------
// Env shape required by this tool
// ---------------------------------------------------------------------------

export interface Env {
  PRICE_CACHE: KVNamespace;
  USER_STATE: DurableObjectNamespace;
}

// ---------------------------------------------------------------------------
// ToolResult type (matches MCP SDK expectations)
// ---------------------------------------------------------------------------

export interface ToolResult {
  content: [{ type: "text"; text: string }];
  isError?: boolean;
}

// ---------------------------------------------------------------------------
// Handler
// ---------------------------------------------------------------------------

/**
 * Handle the `correlation_matrix` MCP tool.
 *
 * @param input        Validated input (parsed by Zod schema upstream).
 * @param env          Cloudflare Worker environment bindings.
 * @param authContext  Resolved auth/tier context from middleware.
 * @returns            ToolResult with JSON-serialised CorrelationMatrixResult.
 */
export async function handleCorrelationMatrix(
  input: CorrelationMatrixInput,
  env: Env,
  authContext: AuthContext
): Promise<ToolResult> {
  try {
    const { tickers, lookback_days, method } = input;

    // ------------------------------------------------------------------
    // 1. Fetch price data for all tickers in parallel
    // ------------------------------------------------------------------
    const svc = new YahooFinanceService({
      PRICE_CACHE: env.PRICE_CACHE,
    });

    // Fetch one extra day so we have at least lookback_days returns after
    // differencing (log returns reduce length by 1).
    const priceMap = await svc.fetchMultiplePrices(tickers, lookback_days + 1);

    // ------------------------------------------------------------------
    // 2. Align series — trim all to the same length (shortest available)
    // ------------------------------------------------------------------
    const rawSeries = tickers.map((t) => priceMap[t] ?? []);

    // Ensure every ticker returned data
    for (let i = 0; i < tickers.length; i++) {
      if (rawSeries[i].length < 2) {
        throw new Error(
          `Insufficient price data for ${tickers[i]}: need at least 2 days, got ${rawSeries[i].length}`
        );
      }
    }

    // Align by taking the tail of each series to the shortest length
    const minLen = Math.min(...rawSeries.map((s) => s.length));
    const closePrices = rawSeries.map((series) =>
      series.slice(-minLen).map((p) => p.close)
    );

    // ------------------------------------------------------------------
    // 3. Compute log returns for each ticker
    // ------------------------------------------------------------------
    const returnSeries = closePrices.map((prices) =>
      calculateLogReturns(prices)
    );

    // ------------------------------------------------------------------
    // 4. Build the correlation matrix
    // ------------------------------------------------------------------
    const matrix2d = buildCorrelationMatrix(returnSeries, method);

    // Convert from 2D array to nested Record<string, Record<string, number>>
    // Round to 6 decimal places for clean JSON output
    const matrixRecord: Record<string, Record<string, number>> = {};
    for (let i = 0; i < tickers.length; i++) {
      matrixRecord[tickers[i]] = {};
      for (let j = 0; j < tickers.length; j++) {
        matrixRecord[tickers[i]][tickers[j]] = round6(matrix2d[i][j]);
      }
    }

    // ------------------------------------------------------------------
    // 5. Find highest and lowest correlated pairs (off-diagonal only)
    // ------------------------------------------------------------------
    let highestPair: [string, string] = [tickers[0], tickers[1]];
    let lowestPair: [string, string] = [tickers[0], tickers[1]];
    let highestValue = -Infinity;
    let lowestValue = Infinity;

    for (let i = 0; i < tickers.length; i++) {
      for (let j = i + 1; j < tickers.length; j++) {
        const corr = matrix2d[i][j];
        if (corr > highestValue) {
          highestValue = corr;
          highestPair = [tickers[i], tickers[j]];
        }
        if (corr < lowestValue) {
          lowestValue = corr;
          lowestPair = [tickers[i], tickers[j]];
        }
      }
    }

    // ------------------------------------------------------------------
    // 6. Compute eigenvalues of the correlation matrix
    // ------------------------------------------------------------------
    const eigenvalues = computeEigenvalues(matrix2d).map(round6);

    // ------------------------------------------------------------------
    // 7. Build human-readable summary
    // ------------------------------------------------------------------
    const n = tickers.length;
    const totalVariance = eigenvalues.reduce((s, e) => s + e, 0);
    const firstEigenShare =
      totalVariance > 0 ? eigenvalues[0] / totalVariance : 0;

    const methodLabel =
      method === "pearson"
        ? "Pearson (linear)"
        : method === "spearman"
          ? "Spearman (rank)"
          : "Kendall (concordance)";

    const diversificationComment =
      firstEigenShare > 0.8
        ? "The dominant first eigenvalue suggests the portfolio is highly undiversified — most variance is explained by a single common factor."
        : firstEigenShare > 0.5
          ? "The first eigenvalue explains more than half the total variance, indicating moderate concentration risk."
          : "Eigenvalue distribution is relatively spread, suggesting reasonable diversification across assets.";

    const summary =
      `Correlation matrix (${methodLabel}) computed for ${n} assets ` +
      `over ${returnSeries[0].length} trading days.\n` +
      `Most correlated pair: ${highestPair[0]} / ${highestPair[1]} ` +
      `(r = ${formatNumber(highestValue, 4)}).\n` +
      `Least correlated pair: ${lowestPair[0]} / ${lowestPair[1]} ` +
      `(r = ${formatNumber(lowestValue, 4)}).\n` +
      `First eigenvalue explains ${formatPercent(firstEigenShare)} of total variance. ` +
      diversificationComment;

    // ------------------------------------------------------------------
    // 8. Assemble result and return
    // ------------------------------------------------------------------
    const result: CorrelationMatrixResult = {
      matrix: matrixRecord,
      highest_correlation: {
        pair: highestPair,
        value: round6(highestValue),
      },
      lowest_correlation: {
        pair: lowestPair,
        value: round6(lowestValue),
      },
      eigenvalues,
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
// Private helpers
// ---------------------------------------------------------------------------

function round6(n: number): number {
  return Math.round(n * 1_000_000) / 1_000_000;
}
