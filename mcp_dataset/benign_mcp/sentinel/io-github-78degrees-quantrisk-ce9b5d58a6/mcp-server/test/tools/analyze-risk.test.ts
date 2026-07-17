/**
 * End-to-end integration test for the analyze_risk tool handler.
 *
 * Mocks the Yahoo Finance service (no real HTTP calls) and validates
 * the full pipeline: price fetch -> returns -> VaR/CVaR -> volatility
 * -> beta -> drawdown -> structured output.
 */

import { describe, it, expect, vi } from "vitest";
import { handleAnalyzeRisk } from "../../src/tools/analyze-risk.js";
import type { AnalyzeRiskEnv } from "../../src/tools/analyze-risk.js";
import type { AnalyzeRiskInput } from "../../src/schemas/analyze-risk.js";
import type { AuthContext } from "../../src/middleware/auth.js";
import type { RiskMetrics } from "../../src/types/risk.js";
import { generateMockPriceMap } from "../fixtures/price-data.js";

// ---------------------------------------------------------------------------
// Mock the Yahoo Finance service so no real HTTP calls are made
// ---------------------------------------------------------------------------

const mockPriceMap = generateMockPriceMap(["AAPL", "MSFT", "NVDA", "SPY"], 253);

vi.mock("../../src/services/yahoo-finance.js", () => {
  return {
    YahooFinanceService: vi.fn().mockImplementation(() => ({
      fetchMultiplePrices: vi.fn().mockImplementation(
        async (tickers: string[], _days: number) => {
          const result: Record<string, typeof mockPriceMap[string]> = {};
          for (const t of tickers) {
            const data = mockPriceMap[t];
            if (!data) throw new Error(`No mock data for ${t}`);
            result[t] = data;
          }
          return result;
        }
      ),
    })),
  };
});

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

const mockEnv: AnalyzeRiskEnv = {
  PRICE_CACHE: {} as KVNamespace,
};

const mockAuth: AuthContext = {
  userId: "test-user-123",
  email: "test@example.com",
  tier: "pro",
  stripeCustomerId: "cus_test",
  isAnonymous: false,
};

function buildInput(overrides?: Partial<AnalyzeRiskInput>): AnalyzeRiskInput {
  return {
    positions: [
      { ticker: "AAPL", quantity: 100 },
      { ticker: "MSFT", quantity: 200 },
      { ticker: "NVDA", quantity: 50 },
    ],
    confidence_level: 0.95,
    horizon_days: 1,
    method: "historical",
    benchmark: "SPY",
    lookback_days: 252,
    ...overrides,
  };
}

// ---------------------------------------------------------------------------
// Helper to parse the tool result
// ---------------------------------------------------------------------------

function parseResult(toolResult: { content: [{ type: string; text: string }]; isError?: boolean }): RiskMetrics {
  expect(toolResult.isError).toBeFalsy();
  expect(toolResult.content).toHaveLength(1);
  expect(toolResult.content[0].type).toBe("text");
  return JSON.parse(toolResult.content[0].text) as RiskMetrics;
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("handleAnalyzeRisk — end-to-end integration", () => {
  it("returns valid RiskMetrics for a 3-position portfolio (historical method)", async () => {
    const input = buildInput();
    const raw = await handleAnalyzeRisk(input, mockEnv, mockAuth);
    const result = parseResult(raw);

    // ── Structure checks ──────────────────────────────────────────────
    expect(result).toHaveProperty("var_absolute");
    expect(result).toHaveProperty("var_percent");
    expect(result).toHaveProperty("cvar_absolute");
    expect(result).toHaveProperty("cvar_percent");
    expect(result).toHaveProperty("annual_volatility");
    expect(result).toHaveProperty("daily_volatility");
    expect(result).toHaveProperty("beta");
    expect(result).toHaveProperty("max_drawdown");
    expect(result).toHaveProperty("portfolio_value");
    expect(result).toHaveProperty("parameters");
    expect(result).toHaveProperty("summary");

    // ── Type checks ───────────────────────────────────────────────────
    expect(typeof result.var_absolute).toBe("number");
    expect(typeof result.var_percent).toBe("number");
    expect(typeof result.cvar_absolute).toBe("number");
    expect(typeof result.cvar_percent).toBe("number");
    expect(typeof result.annual_volatility).toBe("number");
    expect(typeof result.daily_volatility).toBe("number");
    expect(typeof result.beta).toBe("number");
    expect(typeof result.max_drawdown).toBe("number");
    expect(typeof result.portfolio_value).toBe("number");
    expect(typeof result.summary).toBe("string");

    // ── Value sanity checks ───────────────────────────────────────────
    // VaR should be positive (it's a loss metric expressed as a positive number)
    expect(result.var_absolute).toBeGreaterThan(0);
    expect(result.var_percent).toBeGreaterThan(0);

    // CVaR >= VaR (expected shortfall is always at least as large)
    expect(result.cvar_absolute).toBeGreaterThanOrEqual(result.var_absolute);
    expect(result.cvar_percent).toBeGreaterThanOrEqual(result.var_percent);

    // Volatility is positive
    expect(result.annual_volatility).toBeGreaterThan(0);
    expect(result.daily_volatility).toBeGreaterThan(0);
    // Annual vol should be roughly daily vol * sqrt(252)
    const expectedAnnualVol = result.daily_volatility * Math.sqrt(252);
    expect(result.annual_volatility).toBeCloseTo(expectedAnnualVol, 4);

    // Beta should be a reasonable number (not NaN, not wildly extreme)
    expect(Number.isFinite(result.beta)).toBe(true);
    expect(Math.abs(result.beta)).toBeLessThan(10);

    // Max drawdown is between 0 and 1
    expect(result.max_drawdown).toBeGreaterThanOrEqual(0);
    expect(result.max_drawdown).toBeLessThanOrEqual(1);

    // Portfolio value should be positive (100*AAPL + 200*MSFT + 50*NVDA)
    expect(result.portfolio_value).toBeGreaterThan(0);

    // ── Parameters echo ───────────────────────────────────────────────
    expect(result.parameters.confidence_level).toBe(0.95);
    expect(result.parameters.horizon_days).toBe(1);
    expect(result.parameters.method).toBe("historical");
    expect(result.parameters.lookback_days).toBe(252);
  });

  it("summary string is non-empty and contains key financial terms", async () => {
    const input = buildInput();
    const raw = await handleAnalyzeRisk(input, mockEnv, mockAuth);
    const result = parseResult(raw);

    expect(result.summary.length).toBeGreaterThan(50);
    expect(result.summary).toContain("Value at Risk");
    expect(result.summary).toContain("Conditional VaR");
    expect(result.summary).toContain("volatility");
    expect(result.summary).toContain("Beta");
    expect(result.summary).toContain("drawdown");
    // Should mention the portfolio has 3 positions
    expect(result.summary).toContain("3 positions");
  });

  it("works with parametric VaR method", async () => {
    const input = buildInput({ method: "parametric" });
    const raw = await handleAnalyzeRisk(input, mockEnv, mockAuth);
    const result = parseResult(raw);

    expect(result.parameters.method).toBe("parametric");
    expect(result.var_absolute).toBeGreaterThan(0);
    expect(result.cvar_absolute).toBeGreaterThan(0);
    expect(result.annual_volatility).toBeGreaterThan(0);
  });

  it("works with cornish_fisher VaR method", async () => {
    const input = buildInput({ method: "cornish_fisher" });
    const raw = await handleAnalyzeRisk(input, mockEnv, mockAuth);
    const result = parseResult(raw);

    expect(result.parameters.method).toBe("cornish_fisher");
    expect(result.var_absolute).toBeGreaterThan(0);
    expect(result.cvar_absolute).toBeGreaterThan(0);
  });

  it("portfolio value reflects current prices times quantities", async () => {
    const input = buildInput();
    const raw = await handleAnalyzeRisk(input, mockEnv, mockAuth);
    const result = parseResult(raw);

    // Compute expected portfolio value from the last close prices in mock data
    const aaplLast = mockPriceMap["AAPL"][mockPriceMap["AAPL"].length - 1].close;
    const msftLast = mockPriceMap["MSFT"][mockPriceMap["MSFT"].length - 1].close;
    const nvdaLast = mockPriceMap["NVDA"][mockPriceMap["NVDA"].length - 1].close;
    const expectedValue = 100 * aaplLast + 200 * msftLast + 50 * nvdaLast;

    expect(result.portfolio_value).toBeCloseTo(expectedValue, 0);
  });

  it("scales VaR with horizon (multi-day horizon > 1-day)", async () => {
    const input1d = buildInput({ horizon_days: 1 });
    const input10d = buildInput({ horizon_days: 10 });

    const [raw1d, raw10d] = await Promise.all([
      handleAnalyzeRisk(input1d, mockEnv, mockAuth),
      handleAnalyzeRisk(input10d, mockEnv, mockAuth),
    ]);

    const result1d = parseResult(raw1d);
    const result10d = parseResult(raw10d);

    // 10-day VaR should be larger than 1-day VaR (sqrt(10) scaling)
    expect(result10d.var_absolute).toBeGreaterThan(result1d.var_absolute);
    // The ratio should be approximately sqrt(10) ~ 3.16
    const ratio = result10d.var_absolute / result1d.var_absolute;
    expect(ratio).toBeGreaterThan(2);
    expect(ratio).toBeLessThan(5);
  });

  it("higher confidence level produces larger VaR", async () => {
    const input90 = buildInput({ confidence_level: 0.90 });
    const input99 = buildInput({ confidence_level: 0.99 });

    const [raw90, raw99] = await Promise.all([
      handleAnalyzeRisk(input90, mockEnv, mockAuth),
      handleAnalyzeRisk(input99, mockEnv, mockAuth),
    ]);

    const result90 = parseResult(raw90);
    const result99 = parseResult(raw99);

    // 99% VaR should exceed 90% VaR
    expect(result99.var_absolute).toBeGreaterThan(result90.var_absolute);
  });

  it("returns isError: true when given an unknown ticker", async () => {
    // Override the mock to throw for unknown tickers (already handled above)
    const input = buildInput({
      positions: [{ ticker: "ZZZZ", quantity: 100 }],
    });

    const raw = await handleAnalyzeRisk(input, mockEnv, mockAuth);
    expect(raw.isError).toBe(true);
    const errorPayload = JSON.parse(raw.content[0].text);
    expect(errorPayload).toHaveProperty("error");
    expect(errorPayload).toHaveProperty("message");
  });
});
