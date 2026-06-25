# 02 - 架构设计

## 项目结构

```
chart-library/
├── src/
│   ├── core/              # 核心模块
│   │   ├── Chart.ts       # 图表基类
│   │   ├── Canvas.ts      # Canvas 渲染器
│   │   ├── Scale.ts       # 比例尺
│   │   └── Event.ts       # 事件系统
│   ├── charts/            # 图表类型
│   │   ├── LineChart.ts   # 折线图
│   │   ├── BarChart.ts    # 柱状图
│   │   └── PieChart.ts    # 饼图
│   ├── utils/             # 工具函数
│   │   ├── math.ts        # 数学计算
│   │   └── color.ts       # 颜色工具
│   └── index.ts           # 入口文件
├── tests/
├── examples/
└── docs/
```

## 核心类设计

### 1. Chart 基类
```typescript
abstract class Chart {
  protected canvas: HTMLCanvasElement;
  protected ctx: CanvasRenderingContext2D;
  protected data: ChartData;
  protected options: ChartOptions;

  constructor(container: string | HTMLElement, options?: ChartOptions);
  abstract render(): void;
  update(data: ChartData): void;
  destroy(): void;
}
```

### 2. 比例尺系统 (Scale)
```typescript
interface Scale {
  domain: [number, number];  // 数据范围
  range: [number, number];   // 像素范围
  scale(value: number): number;
  invert(pixel: number): number;
}
```

### 3. 数据格式
```typescript
interface ChartData {
  labels?: string[];
  datasets: Dataset[];
}

interface Dataset {
  label: string;
  data: number[];
  color?: string;
}
```

## 渲染流程

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  数据输入    │ →   │  坐标计算    │ →   │  图形绘制    │
└─────────────┘     └─────────────┘     └─────────────┘
       ↑                                        │
       │           ┌─────────────┐              │
       └───────────│  交互处理    │ ←────────────┘
                   └─────────────┘
```

## 交互设计

### 事件类型
- `mousemove`: 鼠标悬停
- `click`: 点击数据点
- `wheel`: 缩放

### Tooltip 实现
```typescript
interface Tooltip {
  show(x: number, y: number, content: string): void;
  hide(): void;
  position: 'top' | 'bottom' | 'left' | 'right';
}
```

## 配置系统

```typescript
interface ChartOptions {
  width?: number;
  height?: number;
  padding?: Padding;
  backgroundColor?: string;
  title?: string;
  legend?: LegendOptions;
  axes?: AxesOptions;
  animation?: AnimationOptions;
}
```
