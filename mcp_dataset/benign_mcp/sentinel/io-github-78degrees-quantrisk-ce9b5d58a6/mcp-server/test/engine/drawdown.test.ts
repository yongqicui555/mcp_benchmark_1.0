import { describe, it, expect } from 'vitest';
import { maxDrawdown, maxDrawdownFromReturns } from '../../src/engine/drawdown.js';

describe('maxDrawdown', () => {
  it('computes max drawdown from a known equity curve', () => {
    // Prices: 100 -> 120 -> 90 -> 110
    // Peak at 120, trough at 90, drawdown = (120-90)/120 = 0.25
    const result = maxDrawdown([100, 120, 90, 110]);
    expect(result.maxDrawdown).toBeCloseTo(0.25, 10);
    expect(result.peakIndex).toBe(1);
    expect(result.troughIndex).toBe(2);
    expect(result.peakValue).toBe(120);
    expect(result.troughValue).toBe(90);
  });

  it('returns 0 for a monotonically increasing series', () => {
    const result = maxDrawdown([100, 110, 120, 130, 140]);
    expect(result.maxDrawdown).toBe(0);
  });

  it('handles a series that only declines', () => {
    // 100 -> 80 -> 60 -> 40
    // max dd = (100 - 40) / 100 = 0.60
    const result = maxDrawdown([100, 80, 60, 40]);
    expect(result.maxDrawdown).toBeCloseTo(0.6, 10);
    expect(result.peakIndex).toBe(0);
    expect(result.troughIndex).toBe(3);
  });

  it('picks the largest drawdown among multiple dips', () => {
    // 100 -> 95 -> 110 -> 80 -> 105
    // Dip 1: peak 100, trough 95, dd = 5%
    // Dip 2: peak 110, trough 80, dd = 27.27%
    const result = maxDrawdown([100, 95, 110, 80, 105]);
    expect(result.maxDrawdown).toBeCloseTo(30 / 110, 10);
    expect(result.peakIndex).toBe(2); // 110
    expect(result.troughIndex).toBe(3); // 80
  });

  it('throws with fewer than 2 prices', () => {
    expect(() => maxDrawdown([100])).toThrow('at least 2');
  });
});

describe('maxDrawdownFromReturns', () => {
  it('computes max drawdown from return series', () => {
    // Returns: [0.20, -0.25, 0.2222]
    // Equity curve: 1.0 -> 1.2 -> 0.9 -> 1.1
    // Max DD = (1.2 - 0.9) / 1.2 = 0.25
    const result = maxDrawdownFromReturns([0.20, -0.25, 0.2222222]);
    expect(result.maxDrawdown).toBeCloseTo(0.25, 4);
  });

  it('returns 0 drawdown for all-positive returns', () => {
    const result = maxDrawdownFromReturns([0.1, 0.1, 0.1]);
    expect(result.maxDrawdown).toBe(0);
  });
});
