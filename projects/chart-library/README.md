# 图表库 (Chart Library)

基础图表库，支持折线图、柱状图、饼图，基于 Canvas 实现。

## 功能特性

- **折线图**: 支持多数据系列、平滑曲线、区域填充
- **柱状图**: 支持分组柱状图、圆角柱子、高亮效果
- **饼图**: 支持扇形分离、百分比标签、交互高亮
- **交互**: Tooltip 提示、鼠标悬停高亮、点击事件
- **响应式**: 自动适配不同屏幕尺寸

## 技术栈

- TypeScript
- Canvas 2D API
- 无外部依赖

## 项目结构

```
chart-library/
├── src/
│   ├── core/              # 核心模块
│   │   ├── Chart.ts       # 图表基类
│   │   ├── Canvas.ts      # Canvas 渲染器
│   │   ├── Scale.ts       # 比例尺系统
│   │   └── Event.ts       # 事件管理
│   ├── charts/            # 图表类型
│   │   ├── LineChart.ts   # 折线图
│   │   ├── BarChart.ts    # 柱状图
│   │   └── PieChart.ts    # 饼图
│   ├── utils/             # 工具函数
│   │   ├── math.ts        # 数学计算
│   │   └── color.ts       # 颜色工具
│   └── index.ts           # 入口文件
├── tests/                 # 测试文件
├── examples/              # 使用示例
├── docs/                  # 项目文档
├── package.json
└── tsconfig.json
```

## 快速开始

### 安装依赖

```bash
npm install
```

### 构建项目

```bash
npm run build
```

### 运行测试

```bash
npm test
```

## 使用示例

### 折线图

```typescript
import { LineChart } from 'chart-library';

const chart = new LineChart('#chart', {
  labels: ['1月', '2月', '3月', '4月', '5月', '6月'],
  datasets: [
    {
      label: '销售额',
      data: [120, 190, 300, 250, 280, 350],
      color: '#4e79a7',
    },
  ],
}, {
  width: 600,
  height: 400,
  smooth: true,
});
```

### 柱状图

```typescript
import { BarChart } from 'chart-library';

const chart = new BarChart('#chart', {
  labels: ['北京', '上海', '广州', '深圳'],
  datasets: [
    {
      label: '2023年',
      data: [1200, 1500, 900, 1100],
      color: '#4e79a7',
    },
    {
      label: '2024年',
      data: [1400, 1600, 1000, 1300],
      color: '#f28e2b',
    },
  ],
});
```

### 饼图

```typescript
import { PieChart } from 'chart-library';

const chart = new PieChart('#chart', {
  labels: ['Chrome', 'Safari', 'Firefox', 'Edge'],
  datasets: [
    {
      label: '浏览器',
      data: [65, 18, 8, 5],
      color: '#4e79a7',
    },
  ],
});
```

## 配置选项

### 通用选项

| 选项 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| width | number | 600 | 图表宽度 |
| height | number | 400 | 图表高度 |
| padding | Padding | { top: 40, right: 40, bottom: 60, left: 60 } | 内边距 |
| backgroundColor | string | '#ffffff' | 背景颜色 |
| title | string | '' | 图表标题 |
| showLegend | boolean | true | 是否显示图例 |
| showGrid | boolean | true | 是否显示网格 |
| showTooltip | boolean | true | 是否显示提示框 |
| smooth | boolean | false | 是否平滑曲线（折线图） |
| animation | boolean | true | 是否启用动画 |

## 事件系统

```typescript
// 监听数据点点击
chart.on('pointClick', (event) => {
  console.log('点击了:', event.dataIndex, event.value);
});

// 监听鼠标悬停
chart.on('mousemove', (event) => {
  console.log('鼠标位置:', event.x, event.y);
});
```

## 示例文件

- `examples/line-chart.html` - 折线图示例
- `examples/bar-chart.html` - 柱状图示例
- `examples/pie-chart.html` - 饼图示例
- `examples/all-charts.html` - 综合示例

## 文档

- [市场调研](docs/01-RESEARCH.md)
- [架构设计](docs/02-DESIGN.md)
- [实现细节](docs/03-IMPLEMENTATION.md)
- [测试策略](docs/04-TESTING.md)
- [开发指南](docs/05-DEVELOPMENT.md)
- [学习笔记](LEARNING_NOTES.md)

## 核心原理

### 坐标转换
```
数据坐标 → 归一化 → 屏幕坐标

canvasX = padding + (value - min) / (max - min) * plotWidth
canvasY = height - padding - (value - min) / (max - min) * plotHeight
```

### 渲染流程
```
数据输入 → 比例尺计算 → 坐标转换 → Canvas 绘制 → 事件绑定
```

## License

MIT
