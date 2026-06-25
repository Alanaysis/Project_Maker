# 04 - 测试策略

## 测试目标

验证图表库的：
1. 坐标计算正确性
2. 渲染输出准确性
3. 交互功能完整性
4. 边界条件处理

## 测试分类

### 1. 单元测试

#### 比例尺测试
```typescript
describe('LinearScale', () => {
  it('should map domain to range correctly', () => {
    const scale = new LinearScale([0, 100], [0, 500]);
    expect(scale.scale(50)).toBe(250);
  });

  it('should handle inverted range', () => {
    const scale = new LinearScale([0, 100], [500, 0]);
    expect(scale.scale(50)).toBe(250);
  });
});
```

#### 数学工具测试
```typescript
describe('MathUtils', () => {
  it('should calculate nice ticks', () => {
    const ticks = calculateNiceTicks([0, 100], 5);
    expect(ticks).toEqual([0, 20, 40, 60, 80, 100]);
  });
});
```

### 2. 集成测试

#### 图表渲染测试
```typescript
describe('LineChart', () => {
  it('should render line chart correctly', () => {
    const chart = new LineChart(container, {
      data: {
        labels: ['A', 'B', 'C'],
        datasets: [{ label: 'Test', data: [10, 20, 30] }]
      }
    });

    // 验证 Canvas 有内容
    const imageData = chart.getImageData();
    expect(imageData).not.toBeNull();
  });
});
```

### 3. 视觉回归测试

使用截图对比验证渲染结果：
```typescript
it('should match visual snapshot', async () => {
  const chart = createTestChart();
  const screenshot = await captureScreenshot(chart);
  expect(screenshot).toMatchImageSnapshot();
});
```

## 测试工具

- **Jest**: 单元测试框架
- **Canvas Mock**: 模拟 Canvas API
- **jsdom**: DOM 环境模拟

## 测试覆盖率目标

- 语句覆盖率: > 90%
- 分支覆盖率: > 85%
- 函数覆盖率: > 95%

## 边界条件测试

1. 空数据集
2. 单个数据点
3. 负数值
4. 极大/极小值
5. 非数值输入
