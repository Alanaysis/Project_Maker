import {
  parseColor,
  toRGBA,
  withAlpha,
  lighten,
  darken,
  generateGradientColors,
  getContrastColor,
} from '../src/utils/color';

describe('Color Utils', () => {
  describe('parseColor', () => {
    it('should parse hex colors', () => {
      const color = parseColor('#ff0000');
      expect(color).toEqual({ r: 255, g: 0, b: 0, a: 1 });
    });

    it('should parse short hex colors', () => {
      const color = parseColor('#f00');
      expect(color).toEqual({ r: 255, g: 0, b: 0, a: 1 });
    });

    it('should parse rgb colors', () => {
      const color = parseColor('rgb(255, 0, 0)');
      expect(color).toEqual({ r: 255, g: 0, b: 0, a: 1 });
    });

    it('should parse rgba colors', () => {
      const color = parseColor('rgba(255, 0, 0, 0.5)');
      expect(color).toEqual({ r: 255, g: 0, b: 0, a: 0.5 });
    });

    it('should return black for invalid colors', () => {
      const color = parseColor('invalid');
      expect(color).toEqual({ r: 0, g: 0, b: 0, a: 1 });
    });
  });

  describe('toRGBA', () => {
    it('should convert to rgba string', () => {
      expect(toRGBA(255, 0, 0)).toBe('rgba(255, 0, 0, 1)');
      expect(toRGBA(0, 255, 0, 0.5)).toBe('rgba(0, 255, 0, 0.5)');
    });
  });

  describe('withAlpha', () => {
    it('should add alpha to color', () => {
      expect(withAlpha('#ff0000', 0.5)).toBe('rgba(255, 0, 0, 0.5)');
    });
  });

  describe('lighten', () => {
    it('should lighten color', () => {
      const result = lighten('#000000', 50);
      const color = parseColor(result);
      expect(color.r).toBe(50);
      expect(color.g).toBe(50);
      expect(color.b).toBe(50);
    });
  });

  describe('darken', () => {
    it('should darken color', () => {
      const result = darken('#ffffff', 50);
      const color = parseColor(result);
      expect(color.r).toBe(205);
      expect(color.g).toBe(205);
      expect(color.b).toBe(205);
    });
  });

  describe('generateGradientColors', () => {
    it('should generate gradient colors', () => {
      const colors = generateGradientColors('#ff0000', '#0000ff', 3);
      expect(colors).toHaveLength(3);
    });
  });

  describe('getContrastColor', () => {
    it('should return black for light colors', () => {
      expect(getContrastColor('#ffffff')).toBe('#000000');
    });

    it('should return white for dark colors', () => {
      expect(getContrastColor('#000000')).toBe('#ffffff');
    });
  });
});
