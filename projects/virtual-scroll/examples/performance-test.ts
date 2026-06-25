/**
 * 性能测试示例
 * 测试虚拟滚动在不同规模数据下的性能表现
 */

import { VirtualScroll, ItemConfig } from '../src';

interface TestResult {
  itemCount: number;
  scrollTime: number;
  renderTime: number;
  memoryUsage: number;
  cacheHitRate: number;
}

async function runPerformanceTest(itemCount: number): Promise<TestResult> {
  // 生成测试数据
  const items: ItemConfig[] = Array.from({ length: itemCount }, (_, i) => ({
    id: i,
    data: { text: `Item ${i}` }
  }));

  // 创建实例
  const virtualScroll = new VirtualScroll({
    containerHeight: 500,
    itemHeight: 50,
    bufferCount: 10
  });

  // 测试设置数据源时间
  const setStart = performance.now();
  virtualScroll.setDataSource(items);
  const setTime = performance.now() - setStart;

  // 测试滚动性能
  const scrollIterations = 1000;
  const scrollStart = performance.now();

  for (let i = 0; i < scrollIterations; i++) {
    const randomPos = Math.random() * (itemCount * 50 - 500);
    virtualScroll.handleScroll(randomPos);
  }

  const scrollTime = (performance.now() - scrollStart) / scrollIterations;

  // 测试渲染性能
  const renderStart = performance.now();
  virtualScroll.handleScroll(itemCount * 25); // 滚动到中间
  const renderItems = virtualScroll.getRenderItems();
  const renderTime = performance.now() - renderStart;

  // 获取内存使用情况（如果可用）
  const memoryUsage = (process as any).memoryUsage?.()?.heapUsed || 0;

  // 获取性能指标
  const metrics = virtualScroll.getMetrics();

  // 清理
  virtualScroll.destroy();

  return {
    itemCount,
    scrollTime,
    renderTime,
    memoryUsage,
    cacheHitRate: metrics.cacheHitRate
  };
}

async function main() {
  console.log('=== Virtual Scroll Performance Test ===\n');

  const testCases = [1000, 10000, 100000, 500000, 1000000];
  const results: TestResult[] = [];

  for (const itemCount of testCases) {
    console.log(`Testing with ${itemCount.toLocaleString()} items...`);
    const result = await runPerformanceTest(itemCount);
    results.push(result);
    console.log(`  ✓ Completed\n`);
  }

  // 显示结果
  console.log('\n=== Results ===\n');
  console.log('Items'.padEnd(12) + 'Scroll (ms)'.padEnd(15) + 'Render (ms)'.padEnd(15) + 'Memory (MB)'.padEnd(15) + 'Cache Hit');
  console.log('-'.repeat(70));

  results.forEach(r => {
    console.log(
      r.itemCount.toLocaleString().padEnd(12) +
      r.scrollTime.toFixed(4).padEnd(15) +
      r.renderTime.toFixed(4).padEnd(15) +
      (r.memoryUsage / 1024 / 1024).toFixed(2).padEnd(15) +
      (r.cacheHitRate * 100).toFixed(2) + '%'
    );
  });

  // 计算性能指标
  console.log('\n=== Analysis ===\n');

  const millionItemResult = results.find(r => r.itemCount === 1000000);
  if (millionItemResult) {
    console.log(`1 Million Items Performance:`);
    console.log(`  Average scroll time: ${millionItemResult.scrollTime.toFixed(4)}ms`);
    console.log(`  This means ${(1000 / millionItemResult.scrollTime).toFixed(0)} scrolls per second`);
    console.log(`  Cache hit rate: ${(millionItemResult.cacheHitRate * 100).toFixed(2)}%`);

    if (millionItemResult.scrollTime < 16) {
      console.log(`  ✓ Performance: EXCELLENT (under 16ms frame budget)`);
    } else if (millionItemResult.scrollTime < 33) {
      console.log(`  ✓ Performance: GOOD (under 33ms for 30fps)`);
    } else {
      console.log(`  ⚠ Performance: NEEDS OPTIMIZATION`);
    }
  }

  // 内存效率
  console.log('\n=== Memory Efficiency ===\n');

  const baseMemory = results[0].memoryUsage;
  results.forEach(r => {
    const memoryPerItem = r.memoryUsage > 0 ? (r.memoryUsage - baseMemory) / r.itemCount : 0;
    console.log(`${r.itemCount.toLocaleString()} items: ${memoryPerItem.toFixed(2)} bytes/item`);
  });
}

// 运行测试
main().catch(console.error);
