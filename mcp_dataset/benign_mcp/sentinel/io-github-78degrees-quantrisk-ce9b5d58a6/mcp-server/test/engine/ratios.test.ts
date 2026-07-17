import { describe, it, expect } from 'vitest';
import { sharpeRatio, sortinoRatio } from '../../src/engine/ratios.js';

describe('sharpeRatio', () => {
  it('computes Sharpe for a simple daily return series', () => {
    // 5 daily returns: all 0.001 (0.1% per day)
    // annReturn = 0.001 * 252 = 0.252
    // stdDev = 0 => Sharpe = 0 (degenerate case, constant returns)
    const returns = [0.001, 0.001, 0.001, 0.001, 0.001];
    expect(sharpeRatio(returns, 0.05, 252)).toBe(0);
  });

  it('computes Sharpe for varying returns', () => {
    // returns: [0.01, 0.02, -0.01, 0.03, 0.00]
    // mean = 0.01, annReturn = 0.01 * 252 = 2.52
    // sample stdDev = sqrt(var), var = sum of sq dev / 4
    // deviations: [0, 0.01, -0.02, 0.02, -0.01]
    // sum sq = 0.001, var = 0.00025, sd = 0.015811
    // annVol = 0.015811 * sqrt(252) = 0.25099
    // Sharpe = (2.52 - 0.05) / 0.25099 = 9.842
    const returns = [0.01, 0.02, -0.01, 0.03, 0.00];
    const sharpe = sharpeRatio(returns, 0.05, 252);
    expect(sharpe).toBeCloseTo(9.842, 1);
  });

  it('negative Sharpe for losing portfolio', () => {
    const returns = [-0.01, -0.02, -0.01, -0.03, -0.02];
    expect(sharpeRatio(returns, 0.05, 252)).toBeLessThan(0);
  });

  it('throws with fewer than 2 returns', () => {
    expect(() => sharpeRatio([0.01])).toThrow('at least 2');
  });
});

describe('sortinoRatio', () => {
  it('computes Sortino for a simple return series', () => {
    // returns: [0.01, 0.02, -0.01, 0.03, 0.00]
    // mean = 0.01, annReturn = 2.52
    // Downside: returns below MAR=0: [-0.01, 0.00]
    // Wait, 0.00 is not below 0 (diff=0, not < 0)
    // Only -0.01 is below MAR=0, diff=-0.01, sq=0.0001
    // downsideVar = 0.0001 / 5 = 0.00002
    // downsideDev = sqrt(0.00002) * sqrt(252) = 0.004472 * 15.875 = 0.070997
    // Sortino = (2.52 - 0.05) / 0.070997 = 34.79
    const returns = [0.01, 0.02, -0.01, 0.03, 0.00];
    const sortino = sortinoRatio(returns, 0.05, 252, 0);
    expect(sortino).toBeCloseTo(34.79, 0);
  });

  it('Sortino >= Sharpe when there are negative returns', () => {
    // Sortino should be higher than Sharpe when upside volatility dominates
    const returns = [0.01, 0.02, -0.005, 0.03, 0.015, -0.003, 0.02, 0.01];
    const sharpe = sharpeRatio(returns, 0.05, 252);
    const sortino = sortinoRatio(returns, 0.05, 252, 0);
    expect(sortino).toBeGreaterThan(sharpe);
  });

  it('returns 0 when no downside returns', () => {
    // All positive returns: no downside deviation => sortino = 0
    const returns = [0.01, 0.02, 0.03, 0.04, 0.05];
    expect(sortinoRatio(returns, 0.05, 252, 0)).toBe(0);
  });

  it('throws with fewer than 2 returns', () => {
    expect(() => sortinoRatio([0.01])).toThrow('at least 2');
  });
});
