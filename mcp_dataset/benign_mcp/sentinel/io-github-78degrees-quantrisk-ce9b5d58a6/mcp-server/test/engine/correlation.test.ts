import { describe, it, expect } from 'vitest';
import { pearsonCorrelation, buildCorrelationMatrix } from '../../src/engine/correlation.js';

describe('pearsonCorrelation', () => {
  it('returns 1 for perfectly positively correlated series', () => {
    const x = [1, 2, 3, 4, 5];
    const y = [2, 4, 6, 8, 10]; // y = 2x
    expect(pearsonCorrelation(x, y)).toBeCloseTo(1.0, 10);
  });

  it('returns -1 for perfectly negatively correlated series', () => {
    const x = [1, 2, 3, 4, 5];
    const y = [10, 8, 6, 4, 2]; // y = 12 - 2x
    expect(pearsonCorrelation(x, y)).toBeCloseTo(-1.0, 10);
  });

  it('returns ~0 for uncorrelated series', () => {
    // Construct series with zero correlation:
    // x = [1, -1, 1, -1], y = [1, 1, -1, -1]
    // cov = mean of products - product of means
    // products: [1, -1, -1, 1], mean = 0
    // means: 0, 0 -> cov = 0
    const x = [1, -1, 1, -1];
    const y = [1, 1, -1, -1];
    expect(pearsonCorrelation(x, y)).toBeCloseTo(0, 10);
  });

  it('returns 0 for a constant series', () => {
    const x = [1, 2, 3, 4, 5];
    const y = [5, 5, 5, 5, 5];
    expect(pearsonCorrelation(x, y)).toBe(0);
  });

  it('is symmetric: corr(x,y) = corr(y,x)', () => {
    const x = [1, 3, 5, 2, 4];
    const y = [2, 1, 4, 5, 3];
    expect(pearsonCorrelation(x, y)).toBeCloseTo(pearsonCorrelation(y, x), 15);
  });

  it('correlation of a series with itself is 1', () => {
    const x = [1.5, -2.3, 0.7, 4.1, -1.2];
    expect(pearsonCorrelation(x, x)).toBeCloseTo(1.0, 10);
  });

  it('throws for arrays of different lengths', () => {
    expect(() => pearsonCorrelation([1, 2], [1, 2, 3])).toThrow('same length');
  });

  it('throws for arrays with fewer than 2 elements', () => {
    expect(() => pearsonCorrelation([1], [2])).toThrow('at least 2');
  });
});

describe('buildCorrelationMatrix', () => {
  it('builds a 2x2 correlation matrix', () => {
    const x = [1, 2, 3, 4, 5];
    const y = [2, 4, 6, 8, 10];
    const matrix = buildCorrelationMatrix([x, y]);

    expect(matrix).toHaveLength(2);
    // Diagonal = 1
    expect(matrix[0][0]).toBeCloseTo(1.0, 10);
    expect(matrix[1][1]).toBeCloseTo(1.0, 10);
    // Off-diagonal = 1 (perfectly correlated)
    expect(matrix[0][1]).toBeCloseTo(1.0, 10);
    expect(matrix[1][0]).toBeCloseTo(1.0, 10);
  });

  it('matrix is symmetric', () => {
    const a = [1, 3, 2, 5, 4];
    const b = [2, 1, 4, 3, 5];
    const c = [5, 4, 3, 2, 1];
    const matrix = buildCorrelationMatrix([a, b, c]);

    expect(matrix[0][1]).toBeCloseTo(matrix[1][0], 15);
    expect(matrix[0][2]).toBeCloseTo(matrix[2][0], 15);
    expect(matrix[1][2]).toBeCloseTo(matrix[2][1], 15);
  });
});
