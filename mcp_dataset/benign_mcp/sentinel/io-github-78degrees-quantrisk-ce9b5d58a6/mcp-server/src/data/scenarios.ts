/**
 * Historical crisis scenario data for stress testing.
 *
 * Each scenario contains approximate peak-to-trough (or event-period) returns
 * for each GICS sector. Values are decimal fractions: -0.55 means -55%.
 *
 * Sources / methodology:
 * ─────────────────────
 * Returns are representative sector-level figures drawn from sector ETF
 * (XLK, XLF, XLE, etc.) performance during each event's primary stress period.
 * These are approximations intended for stress-testing illustration, not
 * precise backtesting. Each scenario's comment documents the reference window.
 *
 * GICS Sectors:
 *   Information Technology
 *   Financials
 *   Health Care
 *   Consumer Discretionary
 *   Consumer Staples
 *   Energy
 *   Materials
 *   Industrials
 *   Utilities
 *   Real Estate
 *   Communication Services
 */

export type GicsSector =
  | "Information Technology"
  | "Financials"
  | "Health Care"
  | "Consumer Discretionary"
  | "Consumer Staples"
  | "Energy"
  | "Materials"
  | "Industrials"
  | "Utilities"
  | "Real Estate"
  | "Communication Services";

export interface ScenarioData {
  /** Human-readable name shown in output summaries. */
  name: string;
  /** Brief description of the event and its primary driver. */
  description: string;
  /** ISO date of approximate scenario start (peak before the drawdown). */
  startDate: string;
  /** ISO date of approximate scenario end (trough or recovery point). */
  endDate: string;
  /** Sector-level returns (decimal). Sectors not listed default to 0. */
  sectorReturns: Record<GicsSector, number>;
  /** Overall broad-market return (S&P 500 total return, decimal). */
  marketReturn: number;
}

export const SCENARIOS: Record<string, ScenarioData> = {

  // ---------------------------------------------------------------------------
  // Global Financial Crisis — Oct 2007 – Mar 2009 (S&P 500: -56.8%)
  // Reference: S&P 500 peak 2007-10-09, trough 2009-03-09
  // ---------------------------------------------------------------------------
  gfc_2008: {
    name:        "Global Financial Crisis (2008–2009)",
    description: "Subprime mortgage collapse, Lehman Brothers bankruptcy, credit market freeze. The worst financial crisis since the Great Depression.",
    startDate:   "2007-10-09",
    endDate:     "2009-03-09",
    marketReturn: -0.568,
    sectorReturns: {
      "Information Technology":    -0.53,
      "Financials":                -0.79,
      "Health Care":               -0.35,
      "Consumer Discretionary":   -0.63,
      "Consumer Staples":         -0.28,
      "Energy":                   -0.56,
      "Materials":                -0.58,
      "Industrials":              -0.62,
      "Utilities":                -0.40,
      "Real Estate":              -0.72,
      "Communication Services":   -0.49,
    },
  },

  // ---------------------------------------------------------------------------
  // COVID-19 Crash — Feb 2020 – Mar 2020 (S&P 500: -33.9%, ~33 days)
  // Reference: 2020-02-19 peak to 2020-03-23 trough
  // ---------------------------------------------------------------------------
  covid_2020: {
    name:        "COVID-19 Crash (2020)",
    description: "Fastest 30%+ drawdown in S&P 500 history. Pandemic-driven demand shock, supply chain collapse, and forced liquidation across all asset classes.",
    startDate:   "2020-02-19",
    endDate:     "2020-03-23",
    marketReturn: -0.339,
    sectorReturns: {
      "Information Technology":    -0.24,
      "Financials":                -0.40,
      "Health Care":               -0.17,
      "Consumer Discretionary":   -0.39,
      "Consumer Staples":         -0.20,
      "Energy":                   -0.57,   // additional oil price war impact
      "Materials":                -0.35,
      "Industrials":              -0.41,
      "Utilities":                -0.22,
      "Real Estate":              -0.39,
      "Communication Services":   -0.25,
    },
  },

  // ---------------------------------------------------------------------------
  // Dot-Com Bust — Mar 2000 – Oct 2002 (S&P 500: -49.1%, Nasdaq: -78%)
  // Reference: 2000-03-24 S&P 500 peak, 2002-10-09 trough
  // ---------------------------------------------------------------------------
  dot_com_2000: {
    name:        "Dot-Com Bust (2000–2002)",
    description: "Collapse of the internet/technology bubble. Overvalued tech and telecom stocks fell 70-90%. Financials and other sectors had moderate declines.",
    startDate:   "2000-03-24",
    endDate:     "2002-10-09",
    marketReturn: -0.491,
    sectorReturns: {
      "Information Technology":    -0.81,
      "Financials":                -0.25,
      "Health Care":               -0.30,
      "Consumer Discretionary":   -0.38,
      "Consumer Staples":         -0.15,
      "Energy":                   -0.12,
      "Materials":                -0.23,
      "Industrials":              -0.35,
      "Utilities":                -0.40,   // telecom deregulation fallout
      "Real Estate":              +0.05,   // relative safe haven
      "Communication Services":   -0.75,
    },
  },

  // ---------------------------------------------------------------------------
  // Black Monday — Oct 19, 1987 (single-day S&P 500: -20.5%)
  // Reference: market close 1987-10-19; broad cross-sector selloff
  // ---------------------------------------------------------------------------
  black_monday_1987: {
    name:        "Black Monday (1987)",
    description: "Single largest one-day percentage decline in S&P 500 history (-20.5%). Triggered by portfolio insurance selling, program trading, and global contagion. No fundamental cause — pure liquidity crisis.",
    startDate:   "1987-10-19",
    endDate:     "1987-10-19",
    marketReturn: -0.205,
    sectorReturns: {
      "Information Technology":    -0.21,
      "Financials":                -0.24,
      "Health Care":               -0.17,
      "Consumer Discretionary":   -0.21,
      "Consumer Staples":         -0.15,
      "Energy":                   -0.18,
      "Materials":                -0.22,
      "Industrials":              -0.21,
      "Utilities":                -0.16,
      "Real Estate":              -0.18,
      "Communication Services":   -0.20,
    },
  },

  // ---------------------------------------------------------------------------
  // Taper Tantrum — May 2013 – Jun 2013 (10-yr yield: +100 bps in ~60 days)
  // Reference: Bernanke's May 22 2013 testimony; bond/equity selloff
  // S&P 500 correction: ~-5.8% (mild equity, severe fixed income/EM)
  // ---------------------------------------------------------------------------
  taper_tantrum_2013: {
    name:        "Taper Tantrum (2013)",
    description: "Fed Chairman Bernanke's suggestion of QE tapering caused a rapid spike in interest rates (+100 bps on 10-year Treasuries). Rate-sensitive sectors and Emerging Markets sold off sharply.",
    startDate:   "2013-05-22",
    endDate:     "2013-06-24",
    marketReturn: -0.058,
    sectorReturns: {
      "Information Technology":    -0.04,
      "Financials":                -0.02,   // banks benefit from higher rates (mild positive later)
      "Health Care":               -0.05,
      "Consumer Discretionary":   -0.06,
      "Consumer Staples":         -0.10,   // high-yield proxy sectors worst hit
      "Energy":                   -0.07,
      "Materials":                -0.08,
      "Industrials":              -0.06,
      "Utilities":                -0.14,   // worst performer — rate-sensitive
      "Real Estate":              -0.16,   // REITs most exposed to rising rates
      "Communication Services":   -0.07,
    },
  },

  // ---------------------------------------------------------------------------
  // Rate Hike Cycle 2022 — Jan 2022 – Oct 2022 (S&P 500: -25.4%, Nasdaq: -36%)
  // Reference: 2021-12-31 to 2022-10-12 trough
  // ---------------------------------------------------------------------------
  rate_hike_2022: {
    name:        "Fed Rate Hike Cycle (2022)",
    description: "Fastest Fed tightening cycle in 40 years (0% → 3.25% in 9 months), driven by 40-year-high CPI inflation. Growth/tech stocks repriced sharply; bonds fell alongside equities (no diversification).",
    startDate:   "2022-01-03",
    endDate:     "2022-10-12",
    marketReturn: -0.254,
    sectorReturns: {
      "Information Technology":    -0.36,
      "Financials":                -0.18,
      "Health Care":               -0.12,
      "Consumer Discretionary":   -0.40,
      "Consumer Staples":         -0.07,
      "Energy":                   +0.43,   // inflation/geopolitical hedge — best sector
      "Materials":                -0.20,
      "Industrials":              -0.22,
      "Utilities":                -0.05,
      "Real Estate":              -0.30,
      "Communication Services":   -0.42,
    },
  },

  // ---------------------------------------------------------------------------
  // Volmageddon — Feb 5, 2018 (VIX short squeeze; S&P 500: -4.1% intraday)
  // Reference: VIX spike from 17 to 50 intraday on 2018-02-05
  // The underlying equity selloff was ~-10% from Jan 26 to Feb 8 peak-to-trough
  // ---------------------------------------------------------------------------
  volmageddon_2018: {
    name:        "Volmageddon (2018)",
    description: "Implosion of short-volatility products (XIV, SVXY) as the VIX spiked from 17 to 50 intraday. Inverse VIX ETPs lost 90%+ overnight. S&P 500 correction of ~10% from late-January peak.",
    startDate:   "2018-01-26",
    endDate:     "2018-02-09",
    marketReturn: -0.102,
    sectorReturns: {
      "Information Technology":    -0.11,
      "Financials":                -0.10,
      "Health Care":               -0.09,
      "Consumer Discretionary":   -0.10,
      "Consumer Staples":         -0.11,   // high-dividend yield stocks sold with rising VIX
      "Energy":                   -0.10,
      "Materials":                -0.10,
      "Industrials":              -0.10,
      "Utilities":                -0.09,
      "Real Estate":              -0.10,
      "Communication Services":   -0.10,
    },
  },

  // ---------------------------------------------------------------------------
  // Euro Sovereign Debt Crisis — Apr 2010 – Sep 2011 (S&P 500: -21.6% in 2011 leg)
  // Reference: using the 2011 US equity impact: 2011-04-29 to 2011-10-03 trough
  // ---------------------------------------------------------------------------
  euro_crisis_2011: {
    name:        "European Sovereign Debt Crisis (2011)",
    description: "Greece, Ireland, Portugal, Spain and Italy faced sovereign debt downgrades and contagion fears. EU/ECB emergency measures prevented full breakup. US equities fell ~21% in the summer 2011 correction.",
    startDate:   "2011-04-29",
    endDate:     "2011-10-03",
    marketReturn: -0.216,
    sectorReturns: {
      "Information Technology":    -0.22,
      "Financials":                -0.32,   // most exposed via European bank holdings
      "Health Care":               -0.14,
      "Consumer Discretionary":   -0.22,
      "Consumer Staples":         -0.09,
      "Energy":                   -0.24,
      "Materials":                -0.28,
      "Industrials":              -0.24,
      "Utilities":                -0.12,
      "Real Estate":              -0.18,
      "Communication Services":   -0.20,
    },
  },

};

// ---------------------------------------------------------------------------
// Helper: get a scenario by key with type safety
// ---------------------------------------------------------------------------

export type ScenarioKey = keyof typeof SCENARIOS;

export const SCENARIO_KEYS = Object.keys(SCENARIOS) as ScenarioKey[];

/**
 * Retrieve scenario data by key.
 * Returns null if the key is not recognised (prevents runtime crashes when
 * the Zod schema and this map drift out of sync).
 */
export function getScenario(key: string): ScenarioData | null {
  return SCENARIOS[key as ScenarioKey] ?? null;
}

/**
 * Get the sector return for a specific sector in a scenario.
 * Returns 0 if the sector is not found (neutral assumption).
 */
export function getSectorReturn(
  scenario: ScenarioData,
  sector: string
): number {
  return (scenario.sectorReturns as Record<string, number>)[sector] ?? 0;
}
