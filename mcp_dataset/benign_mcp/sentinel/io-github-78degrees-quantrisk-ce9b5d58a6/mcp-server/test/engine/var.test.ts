import { describe, it, expect } from 'vitest';
import {
  historicalVaR,
  parametricVaR,
  cornishFisherVaR,
  conditionalVaR,
} from '../../src/engine/var.js';

// Construct a known return distribution: 100 returns evenly spaced from -0.10 to +0.10
// sorted: -0.10, -0.0980, ..., 0.0980, 0.10
// The 5th percentile (p=0.05) is at index 0.05 * 99 = 4.95
// sorted[4] = -0.10 + 4 * (0.20/99) = -0.10 + 0.00808... = -0.09192
// sorted[5] = -0.10 + 5 * (0.20/99) = -0.10 + 0.01010... = -0.08990
// interpolated: -0.09192 * 0.05 + -0.08990 * 0.95 = approx -0.09000...
// Actually let's use the exact formula:
// percentile = sorted[4]*(1-0.95) + sorted[5]*0.95
// Let me just use a simple hand-crafted set.

// Simple dataset: 20 returns, uniformly spaced -0.10 to 0.09
// sorted: [-0.10, -0.09, -0.08, ..., 0.08, 0.09] (step = 0.01)
function makeUniformReturns(): number[] {
  const returns: number[] = [];
  for (let i = -10; i <= 9; i++) {
    returns.push(i / 100);
  }
  return returns;
}

describe('historicalVaR', () => {
  it('computes VaR at 95% confidence from uniform returns', () => {
    const returns = makeUniformReturns();
    const result = historicalVaR(returns, 0.95);
    // 5th percentile: p=0.05, index = 0.05 * 19 = 0.95
    // sorted[0] = -0.10, sorted[1] = -0.09
    // interpolated = -0.10 * 0.05 + -0.09 * 0.95 = -0.005 + -0.0855 = -0.0905
    // VaR = -(-0.0905) = 0.0905
    expect(result.var).toBeCloseTo(0.0905, 4);
    expect(result.confidenceLevel).toBe(0.95);
    expect(result.horizonDays).toBe(1);
    expect(result.method).toBe('historical');
  });

  it('scales by sqrt of horizon', () => {
    const returns = makeUniformReturns();
    const var1 = historicalVaR(returns, 0.95, 1);
    const var10 = historicalVaR(returns, 0.95, 10);
    expect(var10.var).toBeCloseTo(var1.var * Math.sqrt(10), 10);
  });

  it('higher confidence = higher VaR', () => {
    const returns = makeUniformReturns();
    const var95 = historicalVaR(returns, 0.95);
    const var99 = historicalVaR(returns, 0.99);
    expect(var99.var).toBeGreaterThan(var95.var);
  });
});

describe('parametricVaR', () => {
  it('computes VaR assuming normality', () => {
    const returns = makeUniformReturns();
    const result = parametricVaR(returns, 0.95);
    // mean = -0.005, stdDev of uniform [-0.10..0.09] step 0.01
    // For these 20 values: sample std dev
    // parametricVaR = -(mean - z_0.95 * sigma)
    // z_0.95 ~ 1.6449
    expect(result.var).toBeGreaterThan(0);
    expect(result.method).toBe('parametric');
  });

  it('VaR is zero or positive', () => {
    // Even with positive mean returns, VaR should be >= 0 (clamped)
    const returns = [0.05, 0.06, 0.07, 0.08, 0.09];
    const result = parametricVaR(returns, 0.95);
    expect(result.var).toBeGreaterThanOrEqual(0);
  });
});

describe('cornishFisherVaR', () => {
  it('matches parametric VaR for near-normal returns', () => {
    // Symmetric, zero-ish skew and kurtosis -> CF should be close to parametric
    const returns = makeUniformReturns();
    const pVar = parametricVaR(returns, 0.95);
    const cfVar = cornishFisherVaR(returns, 0.95);
    // Should be in the same ballpark (within 20%)
    expect(cfVar.var).toBeCloseTo(pVar.var, 1);
    expect(cfVar.method).toBe('cornish_fisher');
  });

  it('differs from parametric VaR for skewed returns', () => {
    // Right-skewed returns (many small losses, few large gains)
    const returns = [-0.01, -0.01, -0.01, -0.01, -0.01, -0.01, -0.01, 0.10, 0.15, 0.20];
    const pVar = parametricVaR(returns, 0.95);
    const cfVar = cornishFisherVaR(returns, 0.95);
    // They should differ (CF adjusts for skewness)
    expect(cfVar.var).not.toBeCloseTo(pVar.var, 3);
  });

  it('requires at least 4 data points', () => {
    expect(() => cornishFisherVaR([0.01, -0.01, 0.02], 0.95)).toThrow('at least 4');
  });
});

describe('conditionalVaR', () => {
  it('CVaR is greater than or equal to VaR', () => {
    const returns = makeUniformReturns();
    const result = conditionalVaR(returns, 0.95);
    expect(result.cvar).toBeGreaterThanOrEqual(result.var);
  });

  it('returns both var and cvar fields', () => {
    const returns = makeUniformReturns();
    const result = conditionalVaR(returns, 0.95);
    expect(result).toHaveProperty('var');
    expect(result).toHaveProperty('cvar');
    expect(result.var).toBeGreaterThan(0);
    expect(result.cvar).toBeGreaterThan(0);
  });

  it('scales by sqrt of horizon', () => {
    const returns = makeUniformReturns();
    const r1 = conditionalVaR(returns, 0.95, 1);
    const r4 = conditionalVaR(returns, 0.95, 4);
    expect(r4.cvar).toBeCloseTo(r1.cvar * 2, 10); // sqrt(4) = 2
  });
});
