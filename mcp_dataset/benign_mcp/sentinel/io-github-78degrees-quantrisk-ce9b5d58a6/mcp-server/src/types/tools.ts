/**
 * Tool input types — re-exported from Zod schemas.
 *
 * Every type here is derived via z.infer<> from the corresponding schema in
 * src/schemas/.  The schemas are the single source of truth; these re-exports
 * are convenience aliases so the rest of the codebase can import plain types
 * without importing Zod.
 */

export type { AnalyzeRiskInput } from "../schemas/analyze-risk.js";
export type { MonteCarloInput } from "../schemas/monte-carlo.js";
export type { StressTestInput } from "../schemas/stress-test.js";
export type { OptimizePortfolioInput } from "../schemas/optimize-portfolio.js";
export type { CorrelationMatrixInput } from "../schemas/correlation-matrix.js";
export type { PerformanceAttributionInput } from "../schemas/performance-attribution.js";
export type { SectorExposureInput } from "../schemas/sector-exposure.js";
export type { PriceHistoryInput } from "../schemas/price-history.js";
export type { ComparePortfoliosInput } from "../schemas/compare-portfolios.js";
export type { CalculateGreeksInput } from "../schemas/calculate-greeks.js";

// Also re-export the base position type from the position schema.
export type { PositionInput } from "../schemas/position.js";
