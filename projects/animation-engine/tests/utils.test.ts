/**
 * Utility Functions Tests
 */

import {
  lerp,
  clamp,
  mapRange,
  parseNumericValue,
  interpolateNumeric,
  parseColor,
  interpolateColor,
  interpolateStyle,
  generateId,
  now,
} from '../src/utils';

describe('Utility Functions', () => {
  describe('lerp', () => {
    test('returns start when t=0', () => {
      expect(lerp(0, 100, 0)).toBe(0);
    });

    test('returns end when t=1', () => {
      expect(lerp(0, 100, 1)).toBe(100);
    });

    test('returns midpoint when t=0.5', () => {
      expect(lerp(0, 100, 0.5)).toBe(50);
    });

    test('works with negative values', () => {
      expect(lerp(-10, 10, 0.5)).toBe(0);
    });

    test('works with decimal values', () => {
      expect(lerp(0, 1, 0.3)).toBeCloseTo(0.3);
    });
  });

  describe('clamp', () => {
    test('clamps value below minimum', () => {
      expect(clamp(-5, 0, 10)).toBe(0);
    });

    test('clamps value above maximum', () => {
      expect(clamp(15, 0, 10)).toBe(10);
    });

    test('returns value within range', () => {
      expect(clamp(5, 0, 10)).toBe(5);
    });

    test('works with equal bounds', () => {
      expect(clamp(5, 5, 5)).toBe(5);
    });
  });

  describe('mapRange', () => {
    test('maps value from 0-1 to 0-100', () => {
      expect(mapRange(0.5, 0, 1, 0, 100)).toBe(50);
    });

    test('maps value from 0-100 to 0-1', () => {
      expect(mapRange(50, 0, 100, 0, 1)).toBe(0.5);
    });

    test('maps value from 0-1 to 10-20', () => {
      expect(mapRange(0.5, 0, 1, 10, 20)).toBe(15);
    });
  });

  describe('parseNumericValue', () => {
    test('parses number input', () => {
      const result = parseNumericValue(42);
      expect(result).toEqual({ value: 42, unit: '' });
    });

    test('parses pixel value', () => {
      const result = parseNumericValue('100px');
      expect(result).toEqual({ value: 100, unit: 'px' });
    });

    test('parses percentage', () => {
      const result = parseNumericValue('50%');
      expect(result).toEqual({ value: 50, unit: '%' });
    });

    test('parses em value', () => {
      const result = parseNumericValue('1.5em');
      expect(result).toEqual({ value: 1.5, unit: 'em' });
    });

    test('parses negative value', () => {
      const result = parseNumericValue('-20px');
      expect(result).toEqual({ value: -20, unit: 'px' });
    });

    test('handles plain number string', () => {
      const result = parseNumericValue('42');
      expect(result).toEqual({ value: 42, unit: '' });
    });
  });

  describe('interpolateNumeric', () => {
    test('interpolates between numbers', () => {
      expect(interpolateNumeric(0, 100, 0.5)).toBe('50');
    });

    test('interpolates pixel values', () => {
      expect(interpolateNumeric('0px', '100px', 0.5)).toBe('50px');
    });

    test('interpolates percentage values', () => {
      expect(interpolateNumeric('0%', '100%', 0.5)).toBe('50%');
    });
  });

  describe('parseColor', () => {
    test('parses 3-digit hex', () => {
      const result = parseColor('#fff');
      expect(result).toEqual({ r: 255, g: 255, b: 255, a: 1 });
    });

    test('parses 6-digit hex', () => {
      const result = parseColor('#ff0000');
      expect(result).toEqual({ r: 255, g: 0, b: 0, a: 1 });
    });

    test('parses 8-digit hex with alpha', () => {
      const result = parseColor('#ff000080');
      expect(result.r).toBe(255);
      expect(result.g).toBe(0);
      expect(result.b).toBe(0);
      expect(result.a).toBeCloseTo(128 / 255, 2);
    });

    test('parses rgb()', () => {
      const result = parseColor('rgb(255, 128, 0)');
      expect(result).toEqual({ r: 255, g: 128, b: 0, a: 1 });
    });

    test('parses rgba()', () => {
      const result = parseColor('rgba(255, 128, 0, 0.5)');
      expect(result).toEqual({ r: 255, g: 128, b: 0, a: 0.5 });
    });

    test('defaults to black for unknown format', () => {
      const result = parseColor('unknown');
      expect(result).toEqual({ r: 0, g: 0, b: 0, a: 1 });
    });
  });

  describe('interpolateColor', () => {
    test('interpolates between two hex colors', () => {
      const result = interpolateColor('#000000', '#ffffff', 0.5);
      expect(result).toMatch(/rgb\(128, 128, 128\)/);
    });

    test('interpolates between rgb colors', () => {
      const result = interpolateColor('rgb(0, 0, 0)', 'rgb(255, 0, 0)', 0.5);
      expect(result).toMatch(/rgb\(128, 0, 0\)/);
    });

    test('preserves alpha when interpolating rgba', () => {
      const result = interpolateColor('rgba(0, 0, 0, 0)', 'rgba(255, 255, 255, 1)', 0.5);
      expect(result).toMatch(/rgba/);
    });
  });

  describe('interpolateStyle', () => {
    test('interpolates numbers', () => {
      expect(interpolateStyle(0, 100, 0.5)).toBe(50);
    });

    test('interpolates pixel values', () => {
      expect(interpolateStyle('0px', '100px', 0.5)).toBe('50px');
    });

    test('interpolates colors', () => {
      const result = interpolateStyle('#000000', '#ffffff', 0.5);
      expect(result).toMatch(/rgb/);
    });

    test('snaps at midpoint for non-interpolable values', () => {
      expect(interpolateStyle('block', 'none', 0.3)).toBe('block');
      expect(interpolateStyle('block', 'none', 0.7)).toBe('none');
    });
  });

  describe('generateId', () => {
    test('generates unique IDs', () => {
      const id1 = generateId();
      const id2 = generateId();
      expect(id1).not.toBe(id2);
    });

    test('generates string IDs', () => {
      const id = generateId();
      expect(typeof id).toBe('string');
      expect(id.length).toBeGreaterThan(0);
    });
  });

  describe('now', () => {
    test('returns a number', () => {
      const time = now();
      expect(typeof time).toBe('number');
      expect(time).toBeGreaterThan(0);
    });
  });
});
