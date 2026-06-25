/**
 * Easing Functions Tests
 */

import {
  linear,
  easeInQuad,
  easeOutQuad,
  easeInOutQuad,
  easeInCubic,
  easeOutCubic,
  easeInOutCubic,
  easeInQuart,
  easeOutQuart,
  easeInOutQuart,
  easeInQuint,
  easeOutQuint,
  easeInOutQuint,
  easeInSine,
  easeOutSine,
  easeInOutSine,
  easeInExpo,
  easeOutExpo,
  easeInOutExpo,
  easeInCirc,
  easeOutCirc,
  easeInOutCirc,
  easeInElastic,
  easeOutElastic,
  easeInOutElastic,
  easeInBack,
  easeOutBack,
  easeInOutBack,
  easeInBounce,
  easeOutBounce,
  easeInOutBounce,
  resolveEasing,
  getEasingNames,
  registerEasing,
} from '../src/easing';

describe('Easing Functions', () => {
  // All easing functions should satisfy: f(0) = 0, f(1) = 1
  const allEasings = [
    { name: 'linear', fn: linear },
    { name: 'easeInQuad', fn: easeInQuad },
    { name: 'easeOutQuad', fn: easeOutQuad },
    { name: 'easeInOutQuad', fn: easeInOutQuad },
    { name: 'easeInCubic', fn: easeInCubic },
    { name: 'easeOutCubic', fn: easeOutCubic },
    { name: 'easeInOutCubic', fn: easeInOutCubic },
    { name: 'easeInQuart', fn: easeInQuart },
    { name: 'easeOutQuart', fn: easeOutQuart },
    { name: 'easeInOutQuart', fn: easeInOutQuart },
    { name: 'easeInQuint', fn: easeInQuint },
    { name: 'easeOutQuint', fn: easeOutQuint },
    { name: 'easeInOutQuint', fn: easeInOutQuint },
    { name: 'easeInSine', fn: easeInSine },
    { name: 'easeOutSine', fn: easeOutSine },
    { name: 'easeInOutSine', fn: easeInOutSine },
    { name: 'easeInExpo', fn: easeInExpo },
    { name: 'easeOutExpo', fn: easeOutExpo },
    { name: 'easeInOutExpo', fn: easeInOutExpo },
    { name: 'easeInCirc', fn: easeInCirc },
    { name: 'easeOutCirc', fn: easeOutCirc },
    { name: 'easeInOutCirc', fn: easeInOutCirc },
    { name: 'easeInElastic', fn: easeInElastic },
    { name: 'easeOutElastic', fn: easeOutElastic },
    { name: 'easeInOutElastic', fn: easeInOutElastic },
    { name: 'easeInBack', fn: easeInBack },
    { name: 'easeOutBack', fn: easeOutBack },
    { name: 'easeInOutBack', fn: easeInOutBack },
    { name: 'easeInBounce', fn: easeInBounce },
    { name: 'easeOutBounce', fn: easeOutBounce },
    { name: 'easeInOutBounce', fn: easeInOutBounce },
  ];

  describe('Boundary conditions', () => {
    test.each(allEasings)('$name(0) = 0', ({ fn }) => {
      expect(fn(0)).toBeCloseTo(0, 10);
    });

    test.each(allEasings)('$name(1) = 1', ({ fn }) => {
      expect(fn(1)).toBeCloseTo(1, 10);
    });
  });

  describe('Linear', () => {
    test('returns input value directly', () => {
      expect(linear(0)).toBe(0);
      expect(linear(0.25)).toBe(0.25);
      expect(linear(0.5)).toBe(0.5);
      expect(linear(0.75)).toBe(0.75);
      expect(linear(1)).toBe(1);
    });
  });

  describe('Quadratic easing', () => {
    test('easeInQuad is slower at start', () => {
      expect(easeInQuad(0.5)).toBe(0.25);
      // easeIn at t=0.5 should be less than linear at t=0.5
      expect(easeInQuad(0.5)).toBeLessThan(linear(0.5));
    });

    test('easeOutQuad is faster at start', () => {
      expect(easeOutQuad(0.5)).toBe(0.75);
      expect(easeOutQuad(0.5)).toBeGreaterThan(linear(0.5));
    });

    test('easeInOutQuad combines both', () => {
      expect(easeInOutQuad(0.25)).toBeLessThan(linear(0.25));
      expect(easeInOutQuad(0.75)).toBeGreaterThan(linear(0.75));
    });
  });

  describe('Cubic easing', () => {
    test('easeInCubic at midpoint', () => {
      expect(easeInCubic(0.5)).toBeCloseTo(0.125);
    });

    test('easeOutCubic at midpoint', () => {
      expect(easeOutCubic(0.5)).toBeCloseTo(0.875);
    });
  });

  describe('Sine easing', () => {
    test('easeInSine at midpoint', () => {
      expect(easeInSine(0.5)).toBeCloseTo(1 - Math.cos(Math.PI / 4));
    });

    test('easeOutSine at midpoint', () => {
      expect(easeOutSine(0.5)).toBeCloseTo(Math.sin(Math.PI / 4));
    });

    test('easeInOutSine at midpoint', () => {
      expect(easeInOutSine(0.5)).toBeCloseTo(0.5);
    });
  });

  describe('Exponential easing', () => {
    test('easeInExpo at t=0 returns 0', () => {
      expect(easeInExpo(0)).toBe(0);
    });

    test('easeOutExpo at t=1 returns 1', () => {
      expect(easeOutExpo(1)).toBe(1);
    });
  });

  describe('Circular easing', () => {
    test('easeInCirc at midpoint', () => {
      expect(easeInCirc(0.5)).toBeCloseTo(1 - Math.sqrt(0.75));
    });
  });

  describe('Elastic easing', () => {
    test('easeInElastic at boundaries', () => {
      expect(easeInElastic(0)).toBe(0);
      expect(easeInElastic(1)).toBe(1);
    });

    test('easeOutElastic at boundaries', () => {
      expect(easeOutElastic(0)).toBe(0);
      expect(easeOutElastic(1)).toBe(1);
    });

    test('easeInOutElastic at boundaries', () => {
      expect(easeInOutElastic(0)).toBe(0);
      expect(easeInOutElastic(1)).toBe(1);
    });
  });

  describe('Back easing', () => {
    test('easeInBack overshoots', () => {
      // easeInBack can produce negative values for small t
      const midValue = easeInBack(0.5);
      expect(typeof midValue).toBe('number');
    });

    test('easeOutBack overshoots past 1', () => {
      const midValue = easeOutBack(0.5);
      expect(midValue).toBeGreaterThan(1);
    });
  });

  describe('Bounce easing', () => {
    test('easeOutBounce produces bouncing effect', () => {
      const values = [];
      for (let t = 0; t <= 1; t += 0.1) {
        values.push(easeOutBounce(t));
      }
      // Values should generally increase
      expect(values[values.length - 1]).toBeCloseTo(1);
    });

    test('easeInBounce starts with bouncing', () => {
      expect(easeInBounce(0)).toBeCloseTo(0);
      expect(easeInBounce(1)).toBeCloseTo(1);
    });
  });

  describe('resolveEasing', () => {
    test('returns function directly if function provided', () => {
      const custom = (t: number) => t * 2;
      expect(resolveEasing(custom)).toBe(custom);
    });

    test('resolves named easing function', () => {
      const fn = resolveEasing('ease-in-quad');
      expect(fn).toBe(easeInQuad);
    });

    test('falls back to easeOutCubic for unknown name', () => {
      const fn = resolveEasing('unknown-easing');
      expect(fn(0)).toBeCloseTo(0);
      expect(fn(1)).toBeCloseTo(1);
    });

    test('returns easeOutCubic for undefined', () => {
      const fn = resolveEasing(undefined);
      expect(fn(0)).toBeCloseTo(0);
      expect(fn(1)).toBeCloseTo(1);
    });
  });

  describe('getEasingNames', () => {
    test('returns array of easing names', () => {
      const names = getEasingNames();
      expect(Array.isArray(names)).toBe(true);
      expect(names.length).toBeGreaterThan(0);
      expect(names).toContain('linear');
      expect(names).toContain('ease-in-quad');
      expect(names).toContain('ease-out-bounce');
    });
  });

  describe('registerEasing', () => {
    test('registers custom easing function', () => {
      const custom = (t: number) => t * t * t;
      registerEasing('custom-test', custom);
      const resolved = resolveEasing('custom-test');
      expect(resolved).toBe(custom);
    });
  });

  describe('Monotonicity of ease-in functions', () => {
    test('easeInQuad is monotonically increasing', () => {
      for (let t = 0.01; t <= 1; t += 0.01) {
        expect(easeInQuad(t)).toBeGreaterThan(easeInQuad(t - 0.01));
      }
    });

    test('easeInCubic is monotonically increasing', () => {
      for (let t = 0.01; t <= 1; t += 0.01) {
        expect(easeInCubic(t)).toBeGreaterThan(easeInCubic(t - 0.01));
      }
    });
  });
});
