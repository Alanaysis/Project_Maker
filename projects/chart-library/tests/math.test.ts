import {
  lerp,
  clamp,
  getMinMax,
  calculateNiceTicks,
  calculatePieAngles,
  distance,
  isPointInRect,
  formatNumber,
} from '../src/utils/math';

describe('Math Utils', () => {
  describe('lerp', () => {
    it('should interpolate between two values', () => {
      expect(lerp(0, 100, 0.5)).toBe(50);
      expect(lerp(0, 100, 0)).toBe(0);
      expect(lerp(0, 100, 1)).toBe(100);
    });

    it('should handle negative values', () => {
      expect(lerp(-100, 100, 0.5)).toBe(0);
      expect(lerp(-50, 50, 0.25)).toBe(-25);
    });
  });

  describe('clamp', () => {
    it('should clamp value within range', () => {
      expect(clamp(5, 0, 10)).toBe(5);
      expect(clamp(-5, 0, 10)).toBe(0);
      expect(clamp(15, 0, 10)).toBe(10);
    });
  });

  describe('getMinMax', () => {
    it('should find min and max values', () => {
      expect(getMinMax([1, 2, 3, 4, 5])).toEqual({ min: 1, max: 5 });
      expect(getMinMax([5, 3, 1, 4, 2])).toEqual({ min: 1, max: 5 });
    });

    it('should handle single value', () => {
      expect(getMinMax([42])).toEqual({ min: 42, max: 42 });
    });

    it('should handle empty array', () => {
      expect(getMinMax([])).toEqual({ min: 0, max: 0 });
    });

    it('should handle negative values', () => {
      expect(getMinMax([-5, -1, 0, 1, 5])).toEqual({ min: -5, max: 5 });
    });
  });

  describe('calculateNiceTicks', () => {
    it('should calculate nice tick values', () => {
      const ticks = calculateNiceTicks(0, 100, 5);
      expect(ticks[0]).toBeLessThanOrEqual(0);
      expect(ticks[ticks.length - 1]).toBeGreaterThanOrEqual(100);
    });

    it('should handle equal min and max', () => {
      const ticks = calculateNiceTicks(5, 5);
      expect(ticks).toEqual([5]);
    });

    it('should handle small range', () => {
      const ticks = calculateNiceTicks(0, 1, 5);
      expect(ticks.length).toBeGreaterThan(0);
    });
  });

  describe('calculatePieAngles', () => {
    it('should calculate pie angles correctly', () => {
      const angles = calculatePieAngles([25, 25, 50]);
      expect(angles).toHaveLength(3);
      expect(angles[0].end - angles[0].start).toBeCloseTo(Math.PI / 2);
      expect(angles[2].end - angles[2].start).toBeCloseTo(Math.PI);
    });

    it('should handle single value', () => {
      const angles = calculatePieAngles([100]);
      expect(angles).toHaveLength(1);
      expect(angles[0].end - angles[0].start).toBeCloseTo(Math.PI * 2);
    });

    it('should handle empty array', () => {
      const angles = calculatePieAngles([]);
      expect(angles).toHaveLength(0);
    });
  });

  describe('distance', () => {
    it('should calculate distance between two points', () => {
      expect(distance(0, 0, 3, 4)).toBe(5);
      expect(distance(0, 0, 0, 0)).toBe(0);
    });
  });

  describe('isPointInRect', () => {
    it('should detect point inside rectangle', () => {
      expect(isPointInRect(5, 5, 0, 0, 10, 10)).toBe(true);
      expect(isPointInRect(0, 0, 0, 0, 10, 10)).toBe(true);
      expect(isPointInRect(10, 10, 0, 0, 10, 10)).toBe(true);
    });

    it('should detect point outside rectangle', () => {
      expect(isPointInRect(15, 5, 0, 0, 10, 10)).toBe(false);
      expect(isPointInRect(5, 15, 0, 0, 10, 10)).toBe(false);
      expect(isPointInRect(-1, 5, 0, 0, 10, 10)).toBe(false);
    });
  });

  describe('formatNumber', () => {
    it('should format large numbers', () => {
      expect(formatNumber(1500000)).toBe('1.5M');
      expect(formatNumber(1500)).toBe('1.5K');
      expect(formatNumber(42)).toBe('42');
    });

    it('should handle decimals', () => {
      expect(formatNumber(42.5, 1)).toBe('42.5');
    });
  });
});
