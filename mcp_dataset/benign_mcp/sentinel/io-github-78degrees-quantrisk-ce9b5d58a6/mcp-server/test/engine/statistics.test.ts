import { describe, it, expect } from 'vitest';
import {
  mean,
  stdDev,
  variance,
  percentile,
  skewness,
  kurtosis,
  normalCDF,
  normalInverseCDF,
  covariance,
} from '../../src/engine/statistics.js';

describe('mean', () => {
  it('computes mean of [1,2,3,4,5] = 3', () => {
    expect(mean([1, 2, 3, 4, 5])).toBe(3);
  });

  it('computes mean of a single element', () => {
    expect(mean([7])).toBe(7);
  });

  it('throws on empty array', () => {
    expect(() => mean([])).toThrow('empty');
  });
});

describe('variance', () => {
  // Sample variance of [1,2,3,4,5]: sum of squared deviations = 10, divide by 4 = 2.5
  it('computes sample variance of [1,2,3,4,5] = 2.5', () => {
    expect(variance([1, 2, 3, 4, 5])).toBe(2.5);
  });

  it('throws with fewer than 2 values', () => {
    expect(() => variance([1])).toThrow('at least 2');
  });
});

describe('stdDev', () => {
  // sqrt(2.5) = 1.5811388...
  it('computes sample std dev of [1,2,3,4,5]', () => {
    expect(stdDev([1, 2, 3, 4, 5])).toBeCloseTo(1.5811388, 5);
  });
});

describe('percentile', () => {
  it('computes the median (50th percentile) of [1,2,3,4,5] = 3', () => {
    expect(percentile([1, 2, 3, 4, 5], 0.5)).toBe(3);
  });

  it('computes the 0th percentile = minimum', () => {
    expect(percentile([5, 3, 1, 2, 4], 0)).toBe(1);
  });

  it('computes the 100th percentile = maximum', () => {
    expect(percentile([5, 3, 1, 2, 4], 1)).toBe(5);
  });

  it('interpolates the 25th percentile of [1,2,3,4,5] = 2', () => {
    // index = 0.25 * 4 = 1.0, so sorted[1] = 2
    expect(percentile([1, 2, 3, 4, 5], 0.25)).toBe(2);
  });

  it('interpolates a fractional index correctly', () => {
    // For [1,2,3,4], p=0.5: index = 0.5 * 3 = 1.5 -> lerp(2, 3, 0.5) = 2.5
    expect(percentile([1, 2, 3, 4], 0.5)).toBe(2.5);
  });
});

describe('skewness', () => {
  // Symmetric distribution should have skewness near 0
  it('returns ~0 for symmetric [1,2,3,4,5]', () => {
    expect(skewness([1, 2, 3, 4, 5])).toBeCloseTo(0, 10);
  });

  // Right-skewed data
  it('returns positive skewness for right-skewed data', () => {
    expect(skewness([1, 1, 1, 1, 10])).toBeGreaterThan(0);
  });

  it('throws with fewer than 3 values', () => {
    expect(() => skewness([1, 2])).toThrow('at least 3');
  });
});

describe('kurtosis', () => {
  // For a uniform-like small sample [1,2,3,4,5], excess kurtosis is negative (platykurtic)
  it('returns negative excess kurtosis for [1,2,3,4,5]', () => {
    // Fisher bias-adjusted excess kurtosis of {1,2,3,4,5} = -1.2
    expect(kurtosis([1, 2, 3, 4, 5])).toBeCloseTo(-1.2, 5);
  });

  it('throws with fewer than 4 values', () => {
    expect(() => kurtosis([1, 2, 3])).toThrow('at least 4');
  });
});

describe('normalCDF', () => {
  it('returns 0.5 at z=0', () => {
    expect(normalCDF(0)).toBeCloseTo(0.5, 6);
  });

  it('returns ~0.8413 at z=1', () => {
    expect(normalCDF(1)).toBeCloseTo(0.8413, 3);
  });

  it('returns ~0.9772 at z=2', () => {
    expect(normalCDF(2)).toBeCloseTo(0.9772, 3);
  });

  it('returns ~0.0228 at z=-2', () => {
    expect(normalCDF(-2)).toBeCloseTo(0.0228, 3);
  });

  it('CDF(-x) + CDF(x) = 1 (symmetry)', () => {
    expect(normalCDF(-1.5) + normalCDF(1.5)).toBeCloseTo(1, 6);
  });
});

describe('normalInverseCDF', () => {
  it('returns 0 at p=0.5', () => {
    expect(normalInverseCDF(0.5)).toBeCloseTo(0, 6);
  });

  it('returns ~1.6449 at p=0.95', () => {
    expect(normalInverseCDF(0.95)).toBeCloseTo(1.6449, 3);
  });

  it('returns ~-1.6449 at p=0.05', () => {
    expect(normalInverseCDF(0.05)).toBeCloseTo(-1.6449, 3);
  });

  it('returns ~2.3263 at p=0.99', () => {
    expect(normalInverseCDF(0.99)).toBeCloseTo(2.3263, 3);
  });

  it('is the inverse of normalCDF (round-trip)', () => {
    const z = 1.234;
    const p = normalCDF(z);
    // Due to CDF approximation, use moderate precision
    expect(normalInverseCDF(p)).toBeCloseTo(z, 3);
  });

  it('throws for p outside (0,1)', () => {
    expect(() => normalInverseCDF(0)).toThrow();
    expect(() => normalInverseCDF(1)).toThrow();
  });
});

describe('covariance', () => {
  it('returns variance when computing cov(x, x)', () => {
    const x = [1, 2, 3, 4, 5];
    expect(covariance(x, x)).toBeCloseTo(variance(x), 10);
  });

  it('returns 0 for uncorrelated constant + varying', () => {
    // cov([c,c,c], anything) should throw or return 0
    // Actually it won't throw, mean subtraction makes deviations 0
    const x = [1, 2, 3, 4, 5];
    const y = [3, 3, 3, 3, 3];
    expect(covariance(x, y)).toBeCloseTo(0, 10);
  });
});
