/**
 * Risk analytics result types.
 * Plain TypeScript interfaces — not Zod-dependent.
 */

// ─── analyze_risk output ────────────────────────────────────────────────────

export interface RiskMetricsParameters {
  confidence_level: number;
  horizon_days: number;
  method: "historical" | "parametric" | "cornish_fisher";
  lookback_days: number;
}

export interface RiskMetrics {
  /** Dollar VaR at the given confidence level. */
  var_absolute: number;
  /** VaR expressed as a fraction of total portfolio value. */
  var_percent: number;
  /** Conditional VaR / Expected Shortfall in dollars. */
  cvar_absolute: number;
  /** CVaR expressed as a fraction of total portfolio value. */
  cvar_percent: number;
  /** Annualized portfolio volatility (decimal, e.g. 0.18 = 18%). */
  annual_volatility: number;
  /** Daily portfolio volatility (decimal). */
  daily_volatility: number;
  /** Portfolio beta relative to the chosen benchmark. */
  beta: number;
  /** Maximum drawdown over the lookback period (decimal, negative). */
  max_drawdown: number;
  /** Current total portfolio market value in dollars. */
  portfolio_value: number;
  /** Echo of the parameters used in the calculation. */
  parameters: RiskMetricsParameters;
  /** Human-readable paragraph summarizing all metrics. */
  summary: string;
}

// ─── VarResult (intermediate, used by engine) ───────────────────────────────

export interface VarResult {
  var_absolute: number;
  var_percent: number;
  cvar_absolute: number;
  cvar_percent: number;
  method: "historical" | "parametric" | "cornish_fisher";
  confidence_level: number;
  horizon_days: number;
}

// ─── monte_carlo_simulation output ──────────────────────────────────────────

export interface MonteCarloPercentiles {
  p1: number;
  p5: number;
  p10: number;
  p25: number;
  p50: number;
  p75: number;
  p90: number;
  p95: number;
  p99: number;
}

export interface MonteCarloResult {
  /** Percentile distribution of terminal portfolio values. */
  percentiles: MonteCarloPercentiles;
  /** Mean terminal portfolio value across all paths. */
  expected_value: number;
  /** Fraction of paths that end below the initial portfolio value. */
  probability_of_loss: number;
  /** Average loss in the worst 5% of paths. */
  expected_shortfall_5: number;
  /** Maximum terminal value across all paths. */
  best_path: number;
  /** Minimum terminal value across all paths. */
  worst_path: number;
  /** Standard deviation of terminal values. */
  std_dev: number;
  /** Starting portfolio value at simulation time. */
  initial_value: number;
  /** Actual number of simulation paths executed. */
  paths_run: number;
  /** Human-readable summary. */
  summary: string;
}

// ─── stress_test output ─────────────────────────────────────────────────────

export interface PositionPnL {
  ticker: string;
  pnl: number;
  pnl_percent: number;
}

export interface ScenarioResult {
  /** Scenario identifier, e.g. "gfc_2008". */
  scenario: string;
  /** Dollar P&L for the portfolio under this scenario. */
  portfolio_pnl: number;
  /** Percentage P&L for the portfolio under this scenario. */
  portfolio_pnl_percent: number;
  /** Position with the largest loss. */
  worst_position: PositionPnL;
  /** Position with the largest gain. */
  best_position: PositionPnL;
  /** Per-position P&L breakdown for the scenario. */
  position_details: PositionPnL[];
}

export interface StressTestResult {
  /** One ScenarioResult per requested scenario. */
  results: ScenarioResult[];
  /** Current portfolio value at the time of the stress test. */
  portfolio_value: number;
  /** Human-readable summary. */
  summary: string;
}

// ─── optimize_portfolio output ───────────────────────────────────────────────

export interface FrontierPoint {
  return: number;
  volatility: number;
  sharpe: number;
}

export interface OptimizationResult {
  /** Ticker -> optimal weight mapping (decimal, sums to 1.0). */
  weights: Record<string, number>;
  /** Annualized expected return of the optimized portfolio. */
  expected_return: number;
  /** Annualized expected volatility of the optimized portfolio. */
  expected_volatility: number;
  /** Expected Sharpe ratio of the optimized portfolio. */
  sharpe_ratio: number;
  /** 20 points along the efficient frontier. */
  efficient_frontier: FrontierPoint[];
  /** Human-readable summary. */
  summary: string;
}

// ─── correlation_matrix output ───────────────────────────────────────────────

export interface CorrelationMatrixResult {
  /** Ticker x Ticker correlation values. */
  matrix: Record<string, Record<string, number>>;
  /** Pair with the highest absolute positive correlation. */
  highest_correlation: { pair: [string, string]; value: number };
  /** Pair with the lowest (most negative) correlation. */
  lowest_correlation: { pair: [string, string]; value: number };
  /** Eigenvalues of the correlation matrix for PCA-style decomposition. */
  eigenvalues: number[];
  /** Human-readable summary. */
  summary: string;
}

// ─── performance_attribution output ─────────────────────────────────────────

export interface PositionContribution {
  ticker: string;
  /** Portfolio weight as a decimal. */
  weight: number;
  /** Position-level return as a decimal. */
  return: number;
  /** Contribution to total portfolio return as a decimal. */
  contribution: number;
}

export interface PerformanceAttributionResult {
  /** Total return over the period as a decimal. */
  total_return: number;
  /** Annualized return as a decimal. */
  annualized_return: number;
  /** Annualized Sharpe ratio. */
  sharpe_ratio: number;
  /** Sortino ratio using downside deviation. */
  sortino_ratio: number;
  /** Treynor ratio. */
  treynor_ratio: number;
  /** Calmar ratio (annualized return / max drawdown). */
  calmar_ratio: number;
  /** Information ratio versus the benchmark. */
  information_ratio: number;
  /** Annualized tracking error versus the benchmark. */
  tracking_error: number;
  /** GICS sector -> portfolio weight mapping. */
  sector_exposure: Record<string, number>;
  /** Top 5 positions by P&L contribution. */
  top_contributors: PositionContribution[];
  /** Bottom 5 positions by P&L contribution. */
  bottom_contributors: PositionContribution[];
  /** Human-readable summary. */
  summary: string;
}

// ─── sector_exposure output ──────────────────────────────────────────────────

export interface ExposureBucket {
  /** Fraction of portfolio value (decimal). */
  weight: number;
  /** Dollar value in this bucket. */
  value: number;
  /** Tickers that belong to this bucket. */
  tickers: string[];
}

export interface SectorExposureResult {
  /** GICS sector -> ExposureBucket. */
  by_sector: Record<string, ExposureBucket>;
  /** Market cap tier -> ExposureBucket. Tiers: mega/large/mid/small/micro. */
  by_market_cap: Record<string, ExposureBucket>;
  /** Herfindahl-Hirschman Index for sector concentration (0-10000). */
  hhi_sector: number;
  /** Single largest position by portfolio weight. */
  largest_single_position: { ticker: string; weight: number };
  /** Human-readable summary. */
  summary: string;
}

// ─── compare_portfolios output ───────────────────────────────────────────────

export interface PortfolioMetrics extends RiskMetrics {
  /** Portfolio name (from the NamedPortfolio input). */
  name: string;
  total_return: number;
  annualized_return: number;
  sharpe_ratio: number;
  sortino_ratio: number;
  treynor_ratio: number;
  calmar_ratio: number;
  information_ratio: number;
  tracking_error: number;
}

export interface ComparePortfoliosResult {
  /** Full metrics for each portfolio. */
  comparison: PortfolioMetrics[];
  /** Name of the portfolio with the highest Sharpe ratio. */
  winner_by_sharpe: string;
  /** Name of the portfolio with the lowest VaR. */
  winner_by_risk: string;
  /** Human-readable comparison summary. */
  summary: string;
}

// ─── calculate_greeks output ─────────────────────────────────────────────────

export interface GreekResult {
  underlying: string;
  strike: number;
  expiry: string;
  option_type: "call" | "put";
  /** Delta: sensitivity to underlying price change. */
  delta: number;
  /** Gamma: rate of change of delta. */
  gamma: number;
  /** Theta: time decay per day. */
  theta: number;
  /** Vega: sensitivity per 1% change in implied volatility. */
  vega: number;
  /** Rho: sensitivity per 1% change in risk-free rate. */
  rho: number;
  /** Implied volatility used or computed (decimal). */
  implied_volatility: number;
  /** Theoretical option price from the model. */
  theoretical_price: number;
}

export interface PortfolioGreeks {
  delta: number;
  gamma: number;
  theta: number;
  vega: number;
  rho: number;
}

export interface CalculateGreeksResult {
  /** Per-option Greeks. */
  positions: GreekResult[];
  /** Net Greeks aggregated across the entire option portfolio. */
  portfolio_greeks: PortfolioGreeks;
  /** Human-readable summary. */
  summary: string;
}
