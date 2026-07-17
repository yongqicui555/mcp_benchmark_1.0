import { describe, it, expect } from 'vitest';
import {
  calculateLogReturns,
  calculateSimpleReturns,
  calculateCovarianceMatrix,
} from '../../src/engine/returns.js';

describe('calculateLogReturns', () => {
  it('computes log returns from a simple price series', () => {
    // prices: [100, 110, 105]
    // log returns: [ln(110/100), ln(105/110)] = [0.09531, -0.04652]
    const returns = calculateLogReturns([100, 110, 105]);
    expect(returns).toHaveLength(2);
    expect(returns[0]).toBeCloseTo(Math.log(1.1), 10);
    expect(returns[1]).toBeCloseTo(Math.log(105 / 110), 10);
  });

  it('returns an array of length n-1', () => {
    const returns = calculateLogReturns([100, 200, 300, 400]);
    expect(returns).toHaveLength(3);
  });

  it('log returns of constant prices are zero', () => {
    const returns = calculateLogReturns([50, 50, 50]);
    expect(returns[0]).toBe(0);
    expect(returns[1]).toBe(0);
  });

  it('throws when fewer than 2 prices', () => {
    expect(() => calculateLogReturns([100])).toThrow('at least 2');
  });

  it('throws for non-positive prices', () => {
    expect(() => calculateLogReturns([100, 0, 50])).toThrow('non-positive');
  });
});

describe('calculateSimpleReturns', () => {
  it('computes simple returns from a price series', () => {
    // prices: [100, 110, 105]
    // simple returns: [0.10, -0.04545...]
    const returns = calculateSimpleReturns([100, 110, 105]);
    expect(returns).toHaveLength(2);
    expect(returns[0]).toBeCloseTo(0.10, 10);
    expect(returns[1]).toBeCloseTo(-5 / 110, 10);
  });

  it('doubling price gives return of 1.0', () => {
    const returns = calculateSimpleReturns([100, 200]);
    expect(returns[0]).toBe(1.0);
  });

  it('throws for zero price', () => {
    expect(() => calculateSimpleReturns([0, 100])).toThrow('zero');
  });
});

describe('calculateCovarianceMatrix', () => {
  it('produces a 2x2 symmetric matrix', () => {
    const seriesA = [0.01, 0.02, -0.01, 0.03, 0.00];
    const seriesB = [0.02, 0.01, -0.02, 0.04, 0.01];
    const matrix = calculateCovarianceMatrix([seriesA, seriesB]);

    expect(matrix).toHaveLength(2);
    expect(matrix[0]).toHaveLength(2);
    // Symmetric: matrix[0][1] === matrix[1][0]
    expect(matrix[0][1]).toBeCloseTo(matrix[1][0], 15);
  });

  it('diagonal elements are the variances', () => {
    const seriesA = [0.01, 0.02, -0.01, 0.03, 0.00];
    const matrix = calculateCovarianceMatrix([seriesA]);

    // 1x1 matrix, element is variance of seriesA
    // mean = 0.01, deviations = [0, 0.01, -0.02, 0.02, -0.01]
    // sum sq = 0.001, var = 0.001/4 = 0.00025
    expect(matrix[0][0]).toBeCloseTo(0.00025, 10);
  });

  it('covariance of identical series equals variance', () => {
    const series = [0.05, -0.03, 0.02, 0.01, -0.01];
    const matrix = calculateCovarianceMatrix([series, series]);
    expect(matrix[0][1]).toBeCloseTo(matrix[0][0], 10);
  });
});
