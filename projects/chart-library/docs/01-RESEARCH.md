# 01 - 市场调研

## 主流图表库分析

### Canvas 方案

| 库 | 特点 | 优势 | 劣势 |
|---|------|------|------|
| Chart.js | 最流行的 Canvas 图表库 | 简单易用、轻量 | 自定义能力有限 |
| ECharts | Apache 开源，功能强大 | 功能全面、性能好 | 学习曲线陡峭 |
| uPlot | 专注时序数据 | 极致性能、体积小 | 功能单一 |

### SVG 方案

| 库 | 特点 | 优势 | 劣势 |
|---|------|------|------|
| D3.js | 底层可视化库 | 灵活性最高 | 学习成本高 |
| Victory | React + SVG | 组件化、易集成 | 依赖 React |
| Recharts | React + D3 | 声明式 API | 依赖 React |

## 核心技术原理

### 1. 坐标系统转换
```
数据坐标 → 画布坐标
(x, y) → (canvasX, canvasY)

canvasX = padding + (x - minX) / (maxX - minX) * plotWidth
canvasY = height - padding - (y - minY) / (maxY - minY) * plotHeight
```

### 2. 渲染流程
```
数据输入 → 数据处理 → 坐标计算 → 图形绘制 → 交互绑定
```

### 3. Canvas vs SVG 选择
- **Canvas**: 像素级渲染，适合大数据量、高频更新
- **SVG**: 矢量图形，适合交互多、需要缩放的场景

## 设计决策

选择 **Canvas** 作为主要渲染方案，原因：
1. 性能更好，适合大数据集
2. 像素级控制，渲染更精确
3. 内存占用更低

同时支持 **SVG** 导出，满足不同场景需求。

## 参考实现

- Chart.js 的插件架构
- D3.js 的比例尺（Scale）设计
- ECharts 的交互系统

Sources:
- [Chart.js](https://www.chartjs.org/)
- [ECharts](https://echarts.apache.org/)
- [D3.js](https://d3js.org/)
