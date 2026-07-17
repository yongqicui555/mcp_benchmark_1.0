import { describe, it, expect } from 'vitest';
import {
  blackScholesPrice,
  blackScholesDelta,
  blackScholesGamma,
  blackScholesTheta,
  blackScholesVega,
  blackScholesRho,
  impliedVolatility,
} from '../../src/engine/greeks.js';
import type { BSParams } from '../../src/engine/greeks.js';

// Classic test case: S=100, K=100, T=1, r=0.05, sigma=0.2
const atmCall: BSParams = {
  spot: 100,
  strike: 100,
  timeToExpiry: 1,
  riskFreeRate: 0.05,
  volatility: 0.2,
  optionType: 'call',
};

const atmPut: BSParams = {
  ...atmCall,
  optionType: 'put',
};

describe('blackScholesPrice', () => {
  it('prices an ATM call at ~10.4506', () => {
    const price = blackScholesPrice(atmCall);
    expect(price).toBeCloseTo(10.4506, 2);
  });

  it('prices an ATM put correctly via put-call parity', () => {
    // Put-Call parity: C - P = S - K * e^(-rT)
    // P = C - S + K * e^(-rT)
    const callPrice = blackScholesPrice(atmCall);
    const putPrice = blackScholesPrice(atmPut);
    const parity = callPrice - putPrice;
    const expected = 100 - 100 * Math.exp(-0.05 * 1); // = 100 - 95.1229 = 4.8771
    expect(parity).toBeCloseTo(expected, 3);
  });

  it('ATM put price ~5.5735', () => {
    const price = blackScholesPrice(atmPut);
    expect(price).toBeCloseTo(5.5735, 2);
  });

  it('deep ITM call approaches intrinsic value', () => {
    const params: BSParams = {
      spot: 200,
      strike: 100,
      timeToExpiry: 0.01,
      riskFreeRate: 0.05,
      volatility: 0.2,
      optionType: 'call',
    };
    const price = blackScholesPrice(params);
    expect(price).toBeCloseTo(100, 0);
  });

  it('returns intrinsic value at expiry (T=0)', () => {
    const params: BSParams = { ...atmCall, spot: 110, timeToExpiry: 0 };
    expect(blackScholesPrice(params)).toBe(10);
  });
});

describe('blackScholesDelta', () => {
  it('ATM call delta ~0.6368', () => {
    const delta = blackScholesDelta(atmCall);
    expect(delta).toBeCloseTo(0.6368, 3);
  });

  it('ATM put delta ~-0.3632', () => {
    const delta = blackScholesDelta(atmPut);
    expect(delta).toBeCloseTo(-0.3632, 3);
  });

  it('call delta + |put delta| = e^(-qT) (no dividends => ~1)', () => {
    const callDelta = blackScholesDelta(atmCall);
    const putDelta = blackScholesDelta(atmPut);
    // call_delta - put_delta = e^(-qT) = 1 (q=0)
    expect(callDelta - putDelta).toBeCloseTo(1.0, 3);
  });
});

describe('blackScholesGamma', () => {
  it('gamma is positive for ATM options', () => {
    const gamma = blackScholesGamma(atmCall);
    expect(gamma).toBeGreaterThan(0);
  });

  it('gamma is the same for call and put', () => {
    const gammaCall = blackScholesGamma(atmCall);
    const gammaPut = blackScholesGamma(atmPut);
    expect(gammaCall).toBeCloseTo(gammaPut, 10);
  });

  it('ATM gamma ~0.01876', () => {
    const gamma = blackScholesGamma(atmCall);
    expect(gamma).toBeCloseTo(0.01876, 3);
  });
});

describe('blackScholesTheta', () => {
  it('theta is negative for long ATM call', () => {
    const theta = blackScholesTheta(atmCall);
    expect(theta).toBeLessThan(0);
  });

  it('ATM call theta per day ~-0.01757', () => {
    // Annual theta ≈ -6.414, per calendar day: -6.414 / 365 ≈ -0.01757
    const theta = blackScholesTheta(atmCall);
    expect(theta).toBeCloseTo(-0.01757, 3);
  });
});

describe('blackScholesVega', () => {
  it('vega is positive', () => {
    const vega = blackScholesVega(atmCall);
    expect(vega).toBeGreaterThan(0);
  });

  it('vega is the same for call and put', () => {
    const vegaCall = blackScholesVega(atmCall);
    const vegaPut = blackScholesVega(atmPut);
    expect(vegaCall).toBeCloseTo(vegaPut, 10);
  });

  it('ATM vega per 1% vol ~0.3752', () => {
    // Raw vega = S * N'(d1) * sqrt(T) ~ 37.52, per 1% = 0.3752
    const vega = blackScholesVega(atmCall);
    expect(vega).toBeCloseTo(0.3752, 2);
  });
});

describe('blackScholesRho', () => {
  it('call rho is positive', () => {
    const rho = blackScholesRho(atmCall);
    expect(rho).toBeGreaterThan(0);
  });

  it('put rho is negative', () => {
    const rho = blackScholesRho(atmPut);
    expect(rho).toBeLessThan(0);
  });
});

describe('impliedVolatility', () => {
  it('recovers the known volatility from a BS price', () => {
    const price = blackScholesPrice(atmCall);
    const iv = impliedVolatility(price, 100, 100, 1, 0.05, 'call');
    expect(iv).toBeCloseTo(0.2, 4);
  });

  it('works for puts too', () => {
    const price = blackScholesPrice(atmPut);
    const iv = impliedVolatility(price, 100, 100, 1, 0.05, 'put');
    expect(iv).toBeCloseTo(0.2, 4);
  });
});
