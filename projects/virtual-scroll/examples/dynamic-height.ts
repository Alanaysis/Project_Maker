/**
 * 动态高度示例
 * 演示不同高度的列表项
 */

import { VirtualScroll, ItemConfig } from '../src';

// 创建不同高度的数据
const itemCount = 50000;
console.log(`Creating ${itemCount.toLocaleString()} items with dynamic heights...`);

const items: ItemConfig[] = Array.from({ length: itemCount }, (_, i) => {
  // 模拟不同内容长度导致的高度差异
  const contentLength = Math.floor(Math.random() * 5) + 1;
  const estimatedHeight = 40 + contentLength * 20;

  return {
    id: i,
    data: {
      title: `Item ${i + 1}`,
      content: 'Lorem ipsum '.repeat(contentLength),
      estimatedHeight
    }
  };
});

// 创建虚拟滚动实例（动态高度模式）
const virtualScroll = new VirtualScroll(
  {
    containerHeight: 600,
    dynamicHeight: true,
    estimatedHeight: 60,
    bufferCount: 8
  },
  {
    onVisibleChange: (range) => {
      // 模拟测量实际高度并更新
      for (let i = range.startIndex; i <= range.endIndex; i++) {
        const item = items[i];
        if (item) {
          // 模拟实际高度（实际使用中由 DOM 测量）
          const actualHeight = item.data.estimatedHeight + Math.random() * 20 - 10;
          virtualScroll.updateItemHeight(i, Math.round(actualHeight));
        }
      }
    }
  }
);

// 设置数据源
virtualScroll.setDataSource(items);

// 模拟滚动测试
console.log('\nTesting dynamic height scrolling...\n');

const testPositions = [0, 1000, 5000, 20000, 40000];

testPositions.forEach((pos, index) => {
  setTimeout(() => {
    console.log(`\n--- Position: ${pos} ---`);
    virtualScroll.handleScroll(pos);

    const range = virtualScroll.getVisibleRange();
    const renderItems = virtualScroll.getRenderItems();

    console.log(`Visible range: ${range.startIndex} - ${range.endIndex}`);
    console.log(`Total height: ${virtualScroll.getTotalHeight().toLocaleString()}px`);

    // 显示高度变化
    if (renderItems.length > 0) {
      const heights = renderItems.slice(0, 5).map(item => {
        const height = virtualScroll.getMetrics().totalItems > 0
          ? 'dynamic'
          : '60';
        return `[${item.index}]`;
      });
      console.log(`Sample items: ${heights.join(', ')}`);
    }
  }, index * 150);
});

// 性能测试
setTimeout(() => {
  console.log('\n--- Performance Test ---');
  const iterations = 100;
  const startTime = performance.now();

  for (let i = 0; i < iterations; i++) {
    const randomPos = Math.random() * (virtualScroll.getTotalHeight() - 600);
    virtualScroll.handleScroll(randomPos);
  }

  const endTime = performance.now();
  const avgTime = (endTime - startTime) / iterations;

  console.log(`Iterations: ${iterations}`);
  console.log(`Total time: ${(endTime - startTime).toFixed(2)}ms`);
  console.log(`Average time per scroll: ${avgTime.toFixed(3)}ms`);
  console.log(`Scrolls per second: ${(1000 / avgTime).toFixed(0)}`);

  const metrics = virtualScroll.getMetrics();
  console.log(`\nFinal metrics:`);
  console.log(`  Total items: ${metrics.totalItems.toLocaleString()}`);
  console.log(`  Cache hit rate: ${(metrics.cacheHitRate * 100).toFixed(2)}%`);
}, testPositions.length * 150 + 200);

// 清理
setTimeout(() => {
  virtualScroll.destroy();
  console.log('\nVirtual scroll destroyed.');
}, testPositions.length * 150 + 400);
