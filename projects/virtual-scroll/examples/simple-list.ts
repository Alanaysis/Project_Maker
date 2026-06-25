/**
 * 简单列表示例
 * 演示基本的虚拟滚动功能
 */

import { VirtualScroll, ItemConfig } from '../src';

// 创建测试数据
const itemCount = 100000;
console.log(`Creating ${itemCount.toLocaleString()} items...`);

const items: ItemConfig[] = Array.from({ length: itemCount }, (_, i) => ({
  id: i,
  data: {
    title: `Item ${i + 1}`,
    description: `This is the description for item ${i + 1}`,
    timestamp: Date.now() - Math.random() * 1000000000
  }
}));

// 创建虚拟滚动实例
const virtualScroll = new VirtualScroll(
  {
    containerHeight: 500,
    itemHeight: 60,
    bufferCount: 10,
    dynamicHeight: false
  },
  {
    onScroll: (position) => {
      // 滚动事件处理
    },
    onVisibleChange: (range) => {
      // 可视范围变化
      console.log(`Visible range: ${range.startIndex} - ${range.endIndex}`);
    }
  }
);

// 设置数据源
virtualScroll.setDataSource(items);

// 模拟滚动
console.log('\nSimulating scroll...\n');

const scrollPositions = [0, 500, 1000, 5000, 10000, 50000, 99000];

scrollPositions.forEach((scrollTarget, index) => {
  setTimeout(() => {
    console.log(`\n--- Scroll Position: ${scrollTarget} ---`);
    virtualScroll.handleScroll(scrollTarget);

    const renderItems = virtualScroll.getRenderItems();
    const metrics = virtualScroll.getMetrics();

    console.log(`Rendered items: ${renderItems.length}`);
    console.log(`Visible range: ${virtualScroll.getVisibleRange().startIndex} - ${virtualScroll.getVisibleRange().endIndex}`);
    console.log(`Cache hit rate: ${(metrics.cacheHitRate * 100).toFixed(2)}%`);
    console.log(`Average render time: ${metrics.averageRenderTime.toFixed(3)}ms`);

    // 显示前 3 个渲染项
    console.log('\nFirst 3 rendered items:');
    renderItems.slice(0, 3).forEach(item => {
      console.log(`  [${item.index}] ${item.data.title}`);
    });
  }, index * 100);
});

// 测试 scrollToIndex
setTimeout(() => {
  console.log('\n--- Scroll to Index 50000 ---');
  const targetScrollTop = virtualScroll.scrollToIndex(50000, 'center');
  console.log(`Target scroll position: ${targetScrollTop}`);
  virtualScroll.handleScroll(targetScrollTop);

  const metrics = virtualScroll.getMetrics();
  console.log(`Total items: ${metrics.totalItems.toLocaleString()}`);
  console.log(`Rendered items: ${metrics.renderedItems}`);
  console.log(`FPS: ${metrics.scrollFPS}`);
}, scrollPositions.length * 100 + 100);

// 清理
setTimeout(() => {
  virtualScroll.destroy();
  console.log('\nVirtual scroll destroyed.');
}, scrollPositions.length * 100 + 200);
