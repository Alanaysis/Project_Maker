/**
 * Tests for easing functions
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
  describe('Boundary Conditions', () => {
    it('all easing functions should map 0->0', () => {
      const easings = [
        linear, easeInQuad, easeOutQuad, easeInOutQuad,
        easeInCubic, easeOutCubic, easeInOutCubic,
        easeInQuart, easeOutQuart, easeInOutQuart,
        easeInQuint, easeOutQuint, easeInOutQuint,
        easeInSine, easeOutSine, easeInOutSine,
        easeInExpo, easeOutExpo, easeInOutExpo,
        easeInCirc, easeOutCirc, easeInOutCirc,
        easeInElastic, easeOutElastic, easeInOutElastic,
        easeInBack, easeOutBack, easeInOutBack,
        easeInBounce, easeOutBounce, easeInOutBounce,
      ];

      for (const easing of easings) {
        expect(easing(0)).toBeCloseTo(0, 10);
      }
    });

    it('all easing functions should map 1->1', () => {
      const easings = [
        linear, easeInQuad, easeOutQuad, easeInOutQuad,
        easeInCubic, easeOutCubic, easeInOutCubic,
        easeInQuart, easeOutQuart, easeInOutQuart,
        easeInQuint, easeOutQuint, easeInOutQuint,
        easeInSine, easeOutSine, easeInOutSine,
        easeInExpo, easeOutExpo, easeInOutExpo,
        easeInCirc, easeOutCirc, easeInOutCirc,
        easeInElastic, easeOutElastic, easeInOutElastic,
        easeInBack, easeOutBack, easeInOutBack,
        easeInBounce, easeOutBounce, easeInOutBounce,
      ];

      for (const easing of easings) {
        expect(easing(1)).toBeCloseTo(1, 10);
      }
    });
  });

  describe('Linear', () => {
    it('should return input unchanged', () => {
      expect(linear(0)).toBe(0);
      expect(linear(0.5)).toBe(0.5);
      expect(linear(1)).toBe(1);
    });
  });

  describe('Quadratic', () => {
    it('easeInQuad should be convex', () => {
      expect(easeInQuad(0.5)).toBeCloseTo(0.25, 5);
      expect(easeInQuad(0.5)).toBeLessThan(0.5);
    });

    it('easeOutQuad should be concave', () => {
      expect(easeOutQuad(0.5)).toBeCloseTo(0.75, 5);
      expect(easeOutQuad(0.5)).toBeGreaterThan(0.5);
    });

    it('easeInOutQuad should be symmetric', () => {
      expect(easeInOutQuad(0.5)).toBeCloseTo(0.5, 5);
    });
  });

  describe('Cubic', () => {
    it('easeInCubic should be convex', () => {
      expect(easeInCubic(0.5)).toBeCloseTo(0.125, 5);
      expect(easeInCubic(0.5)).toBeLessThan(0.5);
    });

    it('easeOutCubic should be concave', () => {
      expect(easeOutCubic(0.5)).toBeCloseTo(0.875, 5);
      expect(easeOutCubic(0.5)).toBeGreaterThan(0.5);
    });

    it('easeInOutCubic should be symmetric', () => {
      expect(easeInOutCubic(0.5)).toBeCloseTo(0.5, 5);
    });
  });

  describe('Sine', () => {
    it('easeInSine should be convex', () => {
      const val = easeInSine(0.5);
      expect(val).toBeLessThan(0.5);
    });

    it('easeOutSine should be concave', () => {
      const val = easeOutSine(0.5);
      expect(val).toBeGreaterThan(0.5);
    });

    it('easeInOutSine should be symmetric', () => {
      expect(easeInOutSine(0.5)).toBeCloseTo(0.5, 5);
    });
  });

  describe('Exponential', () => {
    it('easeInExpo should be very convex', () => {
      const val = easeInExpo(0.5);
      expect(val).toBeLessThan(0.1);
    });

    it('easeOutExpo should be very concave', () => {
      const val = easeOutExpo(0.5);
      expect(val).toBeGreaterThan(0.9);
    });

    it('easeInOutExpo should be symmetric', () => {
      expect(easeInOutExpo(0.5)).toBeCloseTo(0.5, 5);
    });
  });

  describe('Back', () => {
    it('easeInBack should not overshoot below 0 for t in [0,1]', () => {
      const val = easeInBack(0.5);
      expect(val).toBeGreaterThanOrEqual(0);
    });

    it('easeOutBack should have overshoot near end', () => {
      const val = easeOutBack(0.9);
      expect(val).toBeGreaterThan(1);
    });
  });

  describe('Bounce', () => {
    it('easeOutBounce should bounce near 1', () => {
      const val = easeOutBounce(0.9);
      expect(val).toBeGreaterThan(0.9);
      expect(val).toBeLessThan(1.0);
    });

    it('easeInBounce should start slowly', () => {
      const val = easeInBounce(0.1);
      expect(val).toBeLessThan(0.1);
    });

    it('easeInOutBounce should be symmetric', () => {
      expect(easeInOutBounce(0.5)).toBeCloseTo(0.5, 5);
    });
  });

  describe('Elastic', () => {
    it('easeOutElastic should oscillate near 1', () => {
      const val = easeOutElastic(0.9);
      expect(val).toBeLessThan(1.0);
    });

    it('easeOutElastic should oscillate near 1', () => {
      const val = easeOutElastic(0.9);
      expect(val).toBeLessThan(1.0);
    });

    it('easeInOutElastic should be symmetric', () => {
      expect(easeInOutElastic(0.5)).toBeCloseTo(0.5, 5);
    });
  });

  describe('resolveEasing', () => {
    it('should return default for undefined', () => {
      const result = resolveEasing(undefined);
      expect(result).toBeDefined();
      expect(result(0)).toBeCloseTo(0, 10);
      expect(result(1)).toBeCloseTo(1, 10);
    });

    it('should return function for function input', () => {
      const custom = (t: number) => t * t;
      const result = resolveEasing(custom);
      expect(result).toBe(custom);
    });

    it('should resolve named easing', () => {
      const result = resolveEasing('linear');
      expect(result(0.5)).toBeCloseTo(0.5, 10);
    });

    it('should fall back for unknown name', () => {
      const result = resolveEasing('nonexistent-easing');
      expect(result).toBeDefined();
      expect(result(0)).toBeCloseTo(0, 10);
      expect(result(1)).toBeCloseTo(1, 10);
    });
  });

  describe('getEasingNames', () => {
    it('should return non-empty array', () => {
      const names = getEasingNames();
      expect(names.length).toBeGreaterThan(0);
    });

    it('should include common easings', () => {
      const names = getEasingNames();
      expect(names).toContain('linear');
      expect(names).toContain('ease-in-cubic');
      expect(names).toContain('ease-out-cubic');
      expect(names).toContain('ease-in-out-cubic');
    });
  });

  describe('registerEasing', () => {
    it('should register custom easing', () => {
      const custom = (t: number) => t * t;
      registerEasing('custom-quad', custom);
      const names = getEasingNames();
      expect(names).toContain('custom-quad');

      const resolved = resolveEasing('custom-quad');
      expect(resolved(0.5)).toBeCloseTo(0.25, 10);
      expect(resolved(0)).toBeCloseTo(0, 10);
      expect(resolved(1)).toBeCloseTo(1, 10);
    });
  });
});
