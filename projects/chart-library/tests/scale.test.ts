import { LinearScale, CategoryScale } from '../src/core/Scale';

describe('Scale', () => {
  describe('LinearScale', () => {
    it('should scale values correctly', () => {
      const scale = new LinearScale([0, 100], [0, 500]);
      expect(scale.scale(0)).toBe(0);
      expect(scale.scale(50)).toBe(250);
      expect(scale.scale(100)).toBe(500);
    });

    it('should handle inverted range', () => {
      const scale = new LinearScale([0, 100], [500, 0]);
      expect(scale.scale(0)).toBe(500);
      expect(scale.scale(50)).toBe(250);
      expect(scale.scale(100)).toBe(0);
    });

    it('should invert values correctly', () => {
      const scale = new LinearScale([0, 100], [0, 500]);
      expect(scale.invert(0)).toBe(0);
      expect(scale.invert(250)).toBe(50);
      expect(scale.invert(500)).toBe(100);
    });

    it('should handle zero range', () => {
      const scale = new LinearScale([50, 50], [0, 100]);
      expect(scale.scale(50)).toBe(50);
    });

    it('should generate ticks', () => {
      const scale = new LinearScale([0, 100], [0, 500]);
      const ticks = scale.getTicks(5);
      expect(ticks.length).toBeGreaterThan(0);
      expect(ticks[0]).toBeLessThanOrEqual(0);
      expect(ticks[ticks.length - 1]).toBeGreaterThanOrEqual(100);
    });

    it('should handle negative values', () => {
      const scale = new LinearScale([-100, 100], [0, 500]);
      expect(scale.scale(0)).toBe(250);
      expect(scale.scale(-100)).toBe(0);
      expect(scale.scale(100)).toBe(500);
    });
  });

  describe('CategoryScale', () => {
    const labels = ['A', 'B', 'C', 'D', 'E'];
    const range: [number, number] = [0, 500] as [number, number];

    it('should scale category index correctly', () => {
      const scale = new CategoryScale(labels, range);
      expect(scale.scale(0)).toBe(50);
      expect(scale.scale(1)).toBe(150);
      expect(scale.scale(4)).toBe(450);
    });

    it('should get index from pixel value', () => {
      const scale = new CategoryScale(labels, range);
      expect(scale.getIndex(0)).toBe(0);
      expect(scale.getIndex(100)).toBe(1);
      expect(scale.getIndex(200)).toBe(2);
    });

    it('should calculate bandwidth', () => {
      const scale = new CategoryScale(labels, range);
      expect(scale.getBandwidth()).toBe(100);
    });

    it('should handle out of range values', () => {
      const scale = new CategoryScale(labels, range);
      expect(scale.getIndex(-10)).toBe(0);
      expect(scale.getIndex(600)).toBe(4);
    });
  });
});
