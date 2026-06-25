# 04 - 测试策略

## 测试概述

虚拟滚动组件的测试需要覆盖以下几个关键方面：

1. **功能测试**：验证核心功能的正确性
2. **性能测试**：验证大规模数据下的性能表现
3. **边界测试**：验证边界条件和异常处理
4. **集成测试**：验证与浏览器环境的集成

## 测试环境

### 1. 单元测试环境

**工具链**：
- **测试框架**：Jest
- **断言库**：Jest 内置断言
- **覆盖率**：Istanbul
- **模拟环境**：jsdom

**配置**：
```javascript
// jest.config.js
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'node',
  roots: ['<rootDir>/tests'],
  testMatch: ['**/*.test.ts'],
  collectCoverageFrom: [
    'src/**/*.ts',
    '!src/**/*.d.ts'
  ],
  coverageDirectory: 'coverage',
  coverageReporters: ['text', 'lcov']
};
```

### 2. 性能测试环境

**工具**：
- Node.js 性能 API
- 自定义性能监控

**指标**：
- 执行时间（ms）
- 内存占用（MB）
- FPS（帧/秒）

### 3. 浏览器测试环境

**工具**：
- Playwright / Puppeteer
- Chrome DevTools

**测试场景**：
- 不同浏览器兼容性
- 移动端触摸滚动
- 键盘导航

## 单元测试

### 1. HeightManager 测试

**测试目标**：
- 高度缓存管理
- 偏移量计算
- 索引查找
- 边界条件

**测试用例**：

```typescript
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
  });

  describe('偏移量计算', () => {
    test('应该计算第一项的偏移量为 0', () => {
      manager.setTotalCount(10);
      expect(manager.getItemOffset(0)).toBe(0);
    });

    test('应该计算固定高度的偏移量', () => {
      manager.setTotalCount(10);
      expect(manager.getItemOffset(5)).toBe(250);
    });
  });

  describe('索引查找', () => {
    test('应该查找起始索引', () => {
      manager.setTotalCount(100);
      expect(manager.findStartIndex(0)).toBe(0);
      expect(manager.findStartIndex(100)).toBe(2);
      expect(manager.findStartIndex(250)).toBe(5);
    });
  });
});
```

**测试覆盖**：
- ✓ 基础属性设置和获取
- ✓ 高度缓存的创建和更新
- ✓ 偏移量计算的正确性
- ✓ 二分查找的准确性
- ✓ 边界条件处理

### 2. VirtualScroll 测试

**测试目标**：
- 数据源管理
- 滚动处理
- 可视范围计算
- 渲染队列生成
- 事件回调

**测试用例**：

```typescript
describe('VirtualScroll', () => {
  let virtualScroll: VirtualScroll;
  let items: ItemConfig[];

  beforeEach(() => {
    virtualScroll = new VirtualScroll({
      containerHeight: 400,
      itemHeight: 50,
      bufferCount: 5
    });

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
      expect(virtualScroll.getTotalHeight()).toBe(500000);
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
  });

  describe('滚动到指定位置', () => {
    test('应该滚动到顶部对齐', () => {
      virtualScroll.setDataSource(items);
      const scrollTop = virtualScroll.scrollToIndex(10, 'top');
      expect(scrollTop).toBe(500);
    });

    test('应该滚动到居中对齐', () => {
      virtualScroll.setDataSource(items);
      const scrollTop = virtualScroll.scrollToIndex(10, 'center');
      expect(scrollTop).toBe(300);
    });
  });
});
```

**测试覆盖**：
- ✓ 数据源设置和更新
- ✓ 滚动事件处理
- ✓ 可视范围计算
- ✓ 渲染队列生成
- ✓ scrollToIndex 功能
- ✓ 事件回调触发
- ✓ 实例销毁

### 3. 边界条件测试

**测试用例**：

```typescript
describe('边界条件', () => {
  test('应该处理空列表', () => {
    const scroll = new VirtualScroll({
      containerHeight: 400,
      itemHeight: 50
    });

    scroll.setDataSource([]);
    expect(scroll.getTotalHeight()).toBe(0);
    expect(scroll.getRenderItems()).toEqual([]);

    scroll.destroy();
  });

  test('应该处理单个项目', () => {
    const scroll = new VirtualScroll({
      containerHeight: 400,
      itemHeight: 50
    });

    scroll.setDataSource([{ id: 0, data: {} }]);
    scroll.handleScroll(0);

    const renderItems = scroll.getRenderItems();
    expect(renderItems.length).toBe(1);

    scroll.destroy();
  });

  test('应该处理超出范围的滚动', () => {
    const scroll = new VirtualScroll({
      containerHeight: 400,
      itemHeight: 50
    });

    scroll.setDataSource(items);
    scroll.handleScroll(999999999);

    const range = scroll.getVisibleRange();
    expect(range.endIndex).toBe(9999);

    scroll.destroy();
  });

  test('应该处理负数滚动位置', () => {
    const scroll = new VirtualScroll({
      containerHeight: 400,
      itemHeight: 50
    });

    scroll.setDataSource(items);
    scroll.handleScroll(-100);

    const range = scroll.getVisibleRange();
    expect(range.startIndex).toBe(0);

    scroll.destroy();
  });
});
```

## 性能测试

### 1. 大规模数据测试

**测试目标**：验证百万级数据的处理能力

**测试用例**：

```typescript
describe('性能测试', () => {
  test('应该处理百万级数据', () => {
    const itemCount = 1000000;
    const items = Array.from({ length: itemCount }, (_, i) => ({
      id: i,
      data: { text: `Item ${i}` }
    }));

    const scroll = new VirtualScroll({
      containerHeight: 500,
      itemHeight: 50
    });

    // 测试设置数据源时间
    const setStart = performance.now();
    scroll.setDataSource(items);
    const setTime = performance.now() - setStart;

    expect(setTime).toBeLessThan(1000); // 应该在 1 秒内完成

    // 测试滚动性能
    const scrollStart = performance.now();
    scroll.handleScroll(50000000);
    const scrollTime = performance.now() - scrollStart;

    expect(scrollTime).toBeLessThan(50); // 应该在 50ms 内完成

    scroll.destroy();
  });
});
```

### 2. 滚动性能测试

**测试目标**：验证连续滚动的性能表现

**测试用例**：

```typescript
test('应该保持流畅滚动', () => {
  const scroll = new VirtualScroll({
    containerHeight: 500,
    itemHeight: 50,
    throttleInterval: 0 // 禁用节流以测试原始性能
  });

  scroll.setDataSource(items);

  const iterations = 1000;
  const startTime = performance.now();

  for (let i = 0; i < iterations; i++) {
    const randomPos = Math.random() * (items.length * 50 - 500);
    scroll.handleScroll(randomPos);
  }

  const totalTime = performance.now() - startTime;
  const avgTime = totalTime / iterations;

  expect(avgTime).toBeLessThan(1); // 每次滚动应该在 1ms 内完成

  scroll.destroy();
});
```

### 3. 内存占用测试

**测试目标**：验证内存占用在合理范围内

**测试用例**：

```typescript
test('应该控制内存占用', () => {
  const initialMemory = process.memoryUsage().heapUsed;

  const scroll = new VirtualScroll({
    containerHeight: 500,
    itemHeight: 50
  });

  scroll.setDataSource(items);

  // 多次滚动以触发缓存
  for (let i = 0; i < 100; i++) {
    scroll.handleScroll(i * 500);
  }

  const finalMemory = process.memoryUsage().heapUsed;
  const memoryIncrease = finalMemory - initialMemory;

  // 内存增长应该在合理范围内（小于 100MB）
  expect(memoryIncrease).toBeLessThan(100 * 1024 * 1024);

  scroll.destroy();
});
```

## 动态高度测试

### 1. 高度更新测试

**测试用例**：

```typescript
describe('动态高度', () => {
  test('应该更新项目高度', () => {
    const scroll = new VirtualScroll({
      containerHeight: 400,
      dynamicHeight: true,
      estimatedHeight: 50
    });

    scroll.setDataSource(items);
    scroll.handleScroll(0);

    // 更新高度
    scroll.updateItemHeight(0, 100);
    scroll.updateItemHeight(1, 80);

    // 验证总高度变化
    const totalHeight = scroll.getTotalHeight();
    expect(totalHeight).toBeGreaterThan(500000);

    scroll.destroy();
  });

  test('应该重新计算可视范围', () => {
    const scroll = new VirtualScroll({
      containerHeight: 400,
      dynamicHeight: true,
      estimatedHeight: 50
    });

    scroll.setDataSource(items);
    scroll.handleScroll(0);

    const rangeBefore = scroll.getVisibleRange();

    // 更新高度
    for (let i = 0; i < 100; i++) {
      scroll.updateItemHeight(i, 100);
    }

    const rangeAfter = scroll.getVisibleRange();

    // 可视范围应该调整
    expect(rangeAfter.endIndex).toBeLessThanOrEqual(rangeBefore.endIndex);

    scroll.destroy();
  });
});
```

## 事件回调测试

### 1. 回调触发测试

**测试用例**：

```typescript
describe('事件回调', () => {
  test('应该触发滚动回调', (done) => {
    const scrollPositions: any[] = [];

    const scroll = new VirtualScroll({
      containerHeight: 400,
      itemHeight: 50,
      throttleInterval: 0
    }, {
      onScroll: (pos) => scrollPositions.push(pos)
    });

    scroll.setDataSource(items);
    scroll.handleScroll(100);

    setTimeout(() => {
      expect(scrollPositions.length).toBe(1);
      expect(scrollPositions[0].scrollTop).toBe(100);
      done();
    }, 50);

    scroll.destroy();
  });

  test('应该触发可视范围变化回调', (done) => {
    const ranges: any[] = [];

    const scroll = new VirtualScroll({
      containerHeight: 400,
      itemHeight: 50,
      throttleInterval: 0
    }, {
      onVisibleChange: (range) => ranges.push(range)
    });

    scroll.setDataSource(items);

    setTimeout(() => {
      expect(ranges.length).toBeGreaterThan(0);
      done();
    }, 50);

    scroll.destroy();
  });
});
```

## 集成测试

### 1. DOM 集成测试

**测试环境**：jsdom 或真实浏览器

**测试用例**：

```typescript
describe('DOM 集成', () => {
  let container: HTMLElement;

  beforeEach(() => {
    container = document.createElement('div');
    container.style.height = '500px';
    document.body.appendChild(container);
  });

  afterEach(() => {
    document.body.removeChild(container);
  });

  test('应该创建 DOM 结构', () => {
    const adapter = new DOMAdapter({
      container,
      containerHeight: 500,
      itemHeight: 50,
      renderItem: (item) => {
        const div = document.createElement('div');
        div.textContent = item.data.text;
        return div;
      }
    });

    adapter.setDataSource(items);

    // 验证 DOM 结构
    expect(container.querySelector('.virtual-scroll-viewport')).toBeTruthy();
    expect(container.querySelector('.virtual-scroll-content')).toBeTruthy();

    adapter.destroy();
  });

  test('应该渲染可见项目', () => {
    const adapter = new DOMAdapter({
      container,
      containerHeight: 500,
      itemHeight: 50,
      renderItem: (item) => {
        const div = document.createElement('div');
        div.textContent = item.data.text;
        return div;
      }
    });

    adapter.setDataSource(items);

    // 验证渲染的项目
    const renderedItems = container.querySelectorAll('.virtual-scroll-item');
    expect(renderedItems.length).toBeGreaterThan(0);

    adapter.destroy();
  });
});
```

### 2. 浏览器兼容性测试

**测试矩阵**：

| 浏览器 | 版本 | 测试状态 |
|--------|------|----------|
| Chrome | 90+ | ✓ |
| Firefox | 88+ | ✓ |
| Safari | 14+ | ✓ |
| Edge | 90+ | ✓ |
| iOS Safari | 14+ | ✓ |
| Android Chrome | 90+ | ✓ |

**测试工具**：Playwright

```typescript
import { test, expect } from '@playwright/test';

test('should work in Chrome', async ({ page }) => {
  await page.goto('/demo');

  // 验证虚拟滚动功能
  const container = await page.$('.scroll-container');
  expect(container).toBeTruthy();

  // 模拟滚动
  await container.evaluate(el => el.scrollTop = 1000);

  // 验证渲染的项目
  const items = await page.$$('.list-item');
  expect(items.length).toBeGreaterThan(0);
});
```

## 测试覆盖率目标

### 1. 代码覆盖率

**目标**：
- 语句覆盖率：> 90%
- 分支覆盖率：> 85%
- 函数覆盖率：> 95%

**配置**：
```javascript
// jest.config.js
coverageThreshold: {
  global: {
    statements: 90,
    branches: 85,
    functions: 95,
    lines: 90
  }
}
```

### 2. 功能覆盖率

**必须覆盖的功能**：
- ✓ 数据源设置和更新
- ✓ 滚动处理和节流
- ✓ 可视范围计算
- ✓ 渲染队列生成
- ✓ scrollToIndex 功能
- ✓ 动态高度支持
- ✓ 事件回调
- ✓ 实例销毁

**必须覆盖的边界条件**：
- ✓ 空列表
- ✓ 单个项目
- ✓ 超出范围的滚动
- ✓ 负数滚动位置
- ✓ 极端高度值

## 测试运行

### 1. 运行所有测试

```bash
npm test
```

### 2. 运行特定测试

```bash
npm test -- --testPathPattern=height-manager
```

### 3. 生成覆盖率报告

```bash
npm test -- --coverage
```

### 4. 监听模式

```bash
npm test -- --watch
```

## 持续集成

### 1. GitHub Actions 配置

```yaml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    strategy:
      matrix:
        node-version: [14.x, 16.x, 18.x]

    steps:
      - uses: actions/checkout@v2
      - name: Use Node.js ${{ matrix.node-version }}
        uses: actions/setup-node@v2
        with:
          node-version: ${{ matrix.node-version }}
      - run: npm install
      - run: npm test
      - run: npm run build
```

### 2. 测试报告

**报告内容**：
- 测试总数和通过率
- 代码覆盖率
- 性能基准对比
- 失败测试详情

## 总结

测试策略的关键点：

1. **全面覆盖**：单元测试、性能测试、边界测试、集成测试
2. **自动化**：使用 Jest 和 CI/CD 自动运行测试
3. **性能监控**：测试大规模数据下的性能表现
4. **兼容性**：验证不同浏览器和设备的兼容性
5. **覆盖率**：确保代码覆盖率在 90% 以上

通过完善的测试策略，我们可以确保虚拟滚动组件的质量和稳定性。
