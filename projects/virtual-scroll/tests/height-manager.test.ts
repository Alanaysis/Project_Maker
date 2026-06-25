/**
 * HeightManager 测试
 */

import { HeightManager } from '../src/height-manager';

describe('HeightManager', () => {
  let manager: HeightManager;

  beforeEach(() => {
    manager = new HeightManager(50);
  });

  describe('基础功能', () => {
    test('应该设置和获取总数', () => {
      manager.setTotalCount(100);
      expect(manager.getTotalCount()).toBe(100);
    });

    test('应该设置和获取预估高度', () => {
      manager.setEstimatedHeight(60);
      expect(manager.getEstimatedHeight()).toBe(60);
    });

    test('应该使用默认预估高度', () => {
      expect(manager.getEstimatedHeight()).toBe(50);
    });
  });

  describe('高度缓存', () => {
    test('应该缓存项目高度', () => {
      manager.setTotalCount(10);
      manager.updateItemHeight(0, 100);
      expect(manager.getItemHeight(0)).toBe(100);
    });

    test('应该使用预估高度作为默认值', () => {
      manager.setTotalCount(10);
      expect(manager.getItemHeight(5)).toBe(50);
    });

    test('应该返回缓存大小', () => {
      manager.setTotalCount(10);
      manager.updateItemHeight(0, 100);
      manager.updateItemHeight(1, 120);
      expect(manager.getCacheSize()).toBe(2);
    });

    test('应该清除缓存', () => {
      manager.setTotalCount(10);
      manager.updateItemHeight(0, 100);
      manager.clearCache();
      expect(manager.getCacheSize()).toBe(0);
    });
  });

  describe('偏移量计算', () => {
    test('应该计算第一项的偏移量为 0', () => {
      manager.setTotalCount(10);
      expect(manager.getItemOffset(0)).toBe(0);
    });

    test('应该计算固定高度的偏移量', () => {
      manager.setTotalCount(10);
      expect(manager.getItemOffset(5)).toBe(250); // 5 * 50
    });

    test('应该使用缓存高度计算偏移量', () => {
      manager.setTotalCount(10);
      manager.updateItemHeight(0, 100);
      manager.updateItemHeight(1, 80);
      expect(manager.getItemOffset(2)).toBe(180); // 100 + 80
    });

    test('应该计算总高度', () => {
      manager.setTotalCount(10);
      expect(manager.getTotalHeight()).toBe(500); // 10 * 50
    });

    test('应该使用缓存计算总高度', () => {
      manager.setTotalCount(10);
      manager.updateItemHeight(9, 100);
      // 最后一项偏移 + 最后一项高度
      const expectedHeight = 9 * 50 + 100;
      expect(manager.getTotalHeight()).toBe(expectedHeight);
    });
  });

  describe('索引查找', () => {
    test('应该查找起始索引', () => {
      manager.setTotalCount(100);
      expect(manager.findStartIndex(0)).toBe(0);
      expect(manager.findStartIndex(100)).toBe(2); // 100 / 50 = 2
      expect(manager.findStartIndex(250)).toBe(5); // 250 / 50 = 5
    });

    test('应该使用缓存高度查找索引', () => {
      manager.setTotalCount(10);
      manager.updateItemHeight(0, 100);
      manager.updateItemHeight(1, 80);

      // 索引 0: 0-100
      // 索引 1: 100-180
      // 索引 2: 180-230
      expect(manager.findStartIndex(150)).toBe(1);
      expect(manager.findStartIndex(190)).toBe(2);
    });

    test('应该验证索引有效性', () => {
      manager.setTotalCount(10);
      expect(manager.isValidIndex(0)).toBe(true);
      expect(manager.isValidIndex(9)).toBe(true);
      expect(manager.isValidIndex(10)).toBe(false);
      expect(manager.isValidIndex(-1)).toBe(false);
    });
  });

  describe('缓存统计', () => {
    test('应该计算缓存命中率', () => {
      manager.setTotalCount(100);
      manager.updateItemHeight(0, 100);
      manager.updateItemHeight(1, 100);

      expect(manager.getCacheHitRate()).toBeCloseTo(0.02);
    });

    test('空列表应该返回 0', () => {
      expect(manager.getCacheHitRate()).toBe(0);
    });
  });

  describe('边界情况', () => {
    test('应该处理空列表', () => {
      manager.setTotalCount(0);
      expect(manager.getTotalHeight()).toBe(0);
      expect(manager.getItemOffset(0)).toBe(0);
    });

    test('应该清理超出范围的缓存', () => {
      manager.setTotalCount(10);
      manager.updateItemHeight(5, 100);
      manager.setTotalCount(5);
      expect(manager.getCacheSize()).toBe(0);
    });

    test('应该处理连续更新', () => {
      manager.setTotalCount(100);

      for (let i = 0; i < 100; i++) {
        manager.updateItemHeight(i, 50 + i);
      }

      // 验证偏移量递增
      let prevOffset = 0;
      for (let i = 0; i < 100; i++) {
        const offset = manager.getItemOffset(i);
        expect(offset).toBeGreaterThanOrEqual(prevOffset);
        prevOffset = offset;
      }
    });
  });
});
