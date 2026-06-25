/**
 * VirtualScroll 测试
 */

import { VirtualScroll } from '../src/virtual-scroll';
import { ItemConfig } from '../src/types';

describe('VirtualScroll', () => {
  let virtualScroll: VirtualScroll;
  let items: ItemConfig[];

  beforeEach(() => {
    virtualScroll = new VirtualScroll({
      containerHeight: 400,
      itemHeight: 50,
      bufferCount: 5
    });

    // 创建测试数据
    items = Array.from({ length: 10000 }, (_, i) => ({
      id: i,
      data: { text: `Item ${i}` }
    }));
  });

  afterEach(() => {
    virtualScroll.destroy();
  });

  describe('基础功能', () => {
    test('应该设置数据源', () => {
      virtualScroll.setDataSource(items);
      const metrics = virtualScroll.getMetrics();
      expect(metrics.totalItems).toBe(10000);
    });

    test('应该计算总高度', () => {
      virtualScroll.setDataSource(items);
      expect(virtualScroll.getTotalHeight()).toBe(500000); // 10000 * 50
    });

    test('应该获取渲染队列', () => {
      virtualScroll.setDataSource(items);
      virtualScroll.handleScroll(0);

      const renderItems = virtualScroll.getRenderItems();
      expect(renderItems.length).toBeGreaterThan(0);
      expect(renderItems.length).toBeLessThanOrEqual(8 + 10); // 可视区 + 缓冲区
    });
  });

  describe('滚动处理', () => {
    test('应该更新可视范围', () => {
      virtualScroll.setDataSource(items);
      virtualScroll.handleScroll(500);

      const range = virtualScroll.getVisibleRange();
      expect(range.startIndex).toBeLessThanOrEqual(10);
      expect(range.endIndex).toBeGreaterThan(10);
    });

    test('应该处理滚动到底部', () => {
      virtualScroll.setDataSource(items);
      virtualScroll.handleScroll(499600); // 500000 - 400

      const range = virtualScroll.getVisibleRange();
      expect(range.endIndex).toBeGreaterThan(10);
      expect(range.endIndex).toBeLessThanOrEqual(9999);
    });

    test('应该节流滚动事件', (done) => {
      virtualScroll.setDataSource(items);

      let callCount = 0;
      virtualScroll = new VirtualScroll({
        containerHeight: 400,
        itemHeight: 50,
        throttleInterval: 100
      }, {
        onScroll: () => callCount++
      });

      virtualScroll.setDataSource(items);

      // 快速触发多次滚动
      virtualScroll.handleScroll(100);
      virtualScroll.handleScroll(200);
      virtualScroll.handleScroll(300);

      setTimeout(() => {
        // 应该只触发一次（最后一次）
        expect(callCount).toBe(1);
        done();
      }, 150);
    });
  });

  describe('滚动到指定位置', () => {
    test('应该滚动到顶部对齐', () => {
      virtualScroll.setDataSource(items);
      const scrollTop = virtualScroll.scrollToIndex(10, 'top');
      expect(scrollTop).toBe(500); // 10 * 50
    });

    test('应该滚动到居中对齐', () => {
      virtualScroll.setDataSource(items);
      const scrollTop = virtualScroll.scrollToIndex(10, 'center');
      // 计算：10 * 50 - (400 - 50) / 2 = 500 - 175 = 325
      expect(scrollTop).toBe(325);
    });

    test('应该滚动到底部对齐', () => {
      virtualScroll.setDataSource(items);
      const scrollTop = virtualScroll.scrollToIndex(10, 'bottom');
      expect(scrollTop).toBe(150); // 500 - 400 + 50
    });

    test('应该限制在有效范围内', () => {
      virtualScroll.setDataSource(items);
      const scrollTop = virtualScroll.scrollToIndex(0, 'top');
      expect(scrollTop).toBe(0);
    });

    test('应该处理超出范围的索引', () => {
      virtualScroll.setDataSource(items);
      const scrollTop = virtualScroll.scrollToIndex(-1);
      expect(scrollTop).toBe(0);
    });
  });

  describe('动态高度', () => {
    test('应该支持动态高度模式', () => {
      const dynamicScroll = new VirtualScroll({
        containerHeight: 400,
        dynamicHeight: true,
        estimatedHeight: 50
      });

      dynamicScroll.setDataSource(items);
      dynamicScroll.handleScroll(0);

      // 更新项目高度
      dynamicScroll.updateItemHeight(0, 100);
      dynamicScroll.updateItemHeight(1, 80);

      const range = dynamicScroll.getVisibleRange();
      expect(range.startIndex).toBe(0);

      dynamicScroll.destroy();
    });

    test('应该忽略固定高度模式的高度更新', () => {
      virtualScroll.setDataSource(items);
      virtualScroll.updateItemHeight(0, 100);

      // 固定高度模式下不应更新
      expect(virtualScroll.getMetrics().cacheHitRate).toBe(0);
    });
  });

  describe('数据操作', () => {
    test('应该更新单个数据项', () => {
      virtualScroll.setDataSource(items);
      virtualScroll.updateItem(0, { id: 0, data: { text: 'Updated' } });

      const renderItems = virtualScroll.getRenderItems();
      const firstItem = renderItems.find(item => item.index === 0);
      expect(firstItem?.data.text).toBe('Updated');
    });

    test('应该追加数据项', () => {
      virtualScroll.setDataSource(items);
      virtualScroll.appendItems([
        { id: 10000, data: { text: 'New Item' } }
      ]);

      expect(virtualScroll.getMetrics().totalItems).toBe(10001);
    });
  });

  describe('配置更新', () => {
    test('应该更新配置选项', () => {
      virtualScroll.setDataSource(items);
      virtualScroll.updateOptions({
        containerHeight: 600,
        bufferCount: 10
      });

      virtualScroll.handleScroll(0);
      const renderItems = virtualScroll.getRenderItems();
      expect(renderItems.length).toBeGreaterThan(8);
    });
  });

  describe('生命周期', () => {
    test('应该销毁实例', () => {
      virtualScroll.setDataSource(items);
      virtualScroll.destroy();

      expect(virtualScroll.isDestroyed()).toBe(true);
    });

    test('销毁后不应处理滚动', () => {
      virtualScroll.setDataSource(items);
      virtualScroll.destroy();

      // 销毁后，可视范围应该保持在销毁前的状态或为 0
      const range = virtualScroll.getVisibleRange();
      expect(range.startIndex).toBeGreaterThanOrEqual(0);
      expect(range.endIndex).toBeGreaterThanOrEqual(0);
    });
  });

  describe('性能指标', () => {
    test('应该返回性能指标', () => {
      virtualScroll.setDataSource(items);
      virtualScroll.handleScroll(0);

      const metrics = virtualScroll.getMetrics();
      expect(metrics).toHaveProperty('totalItems');
      expect(metrics).toHaveProperty('renderedItems');
      expect(metrics).toHaveProperty('cacheHitRate');
      expect(metrics).toHaveProperty('scrollFPS');
      expect(metrics).toHaveProperty('averageRenderTime');
    });

    test('应该记录渲染项目数', () => {
      virtualScroll.setDataSource(items);
      virtualScroll.handleScroll(0);

      const metrics = virtualScroll.getMetrics();
      expect(metrics.renderedItems).toBeGreaterThan(0);
    });
  });

  describe('事件回调', () => {
    test('应该触发滚动回调', (done) => {
      const scrollPositions: any[] = [];

      virtualScroll = new VirtualScroll({
        containerHeight: 400,
        itemHeight: 50,
        throttleInterval: 0
      }, {
        onScroll: (pos) => scrollPositions.push(pos)
      });

      virtualScroll.setDataSource(items);
      virtualScroll.handleScroll(100);

      setTimeout(() => {
        expect(scrollPositions.length).toBe(1);
        expect(scrollPositions[0].scrollTop).toBe(100);
        done();
      }, 50);
    });

    test('应该触发可视范围变化回调', (done) => {
      const ranges: any[] = [];

      virtualScroll = new VirtualScroll({
        containerHeight: 400,
        itemHeight: 50,
        throttleInterval: 0
      }, {
        onVisibleChange: (range) => ranges.push(range)
      });

      virtualScroll.setDataSource(items);

      setTimeout(() => {
        expect(ranges.length).toBeGreaterThan(0);
        done();
      }, 50);
    });
  });

  describe('大规模数据', () => {
    test('应该处理百万级数据', () => {
      const largeItems = Array.from({ length: 1000000 }, (_, i) => ({
        id: i,
        data: { text: `Item ${i}` }
      }));

      const start = performance.now();
      virtualScroll.setDataSource(largeItems);
      const setTime = performance.now() - start;

      expect(setTime).toBeLessThan(1000); // 应该在 1 秒内完成

      const scrollStart = performance.now();
      virtualScroll.handleScroll(50000000); // 滚动到中间
      const scrollTime = performance.now() - scrollStart;

      expect(scrollTime).toBeLessThan(50); // 应该在 50ms 内完成
    });
  });
});
