# 03 - 实现细节

## 核心模块实现

### 1. Canvas 渲染器

Canvas 渲染器负责：
- 创建和管理 Canvas 元素
- 提供绑图 API
- 处理高 DPI 屏幕适配

```typescript
class CanvasRenderer {
  private canvas: HTMLCanvasElement;
  private ctx: CanvasRenderingContext2D;
  private dpr: number;

  constructor(container: HTMLElement, width: number, height: number) {
    this.dpr = window.devicePixelRatio || 1;
    this.canvas = document.createElement('canvas');
    this.setupCanvas(width, height);
    container.appendChild(this.canvas);
    this.ctx = this.canvas.getContext('2d')!;
  }

  private setupCanvas(width: number, height: number): void {
    this.canvas.width = width * this.dpr;
    this.canvas.height = height * this.dpr;
    this.canvas.style.width = `${width}px`;
    this.canvas.style.height = `${height}px`;
    this.ctx.scale(this.dpr, this.dpr);
  }
}
```

### 2. 比例尺系统

线性比例尺将数据值映射到像素坐标：

```typescript
class LinearScale implements Scale {
  domain: [number, number];
  range: [number, number];

  scale(value: number): number {
    const [d0, d1] = this.domain;
    const [r0, r1] = this.range;
    return r0 + (value - d0) / (d1 - d0) * (r1 - r0);
  }

  invert(pixel: number): number {
    const [d0, d1] = this.domain;
    const [r0, r1] = this.range;
    return d0 + (pixel - r0) / (r1 - r0) * (d1 - d0);
  }
}
```

### 3. 坐标轴绘制

```typescript
function drawAxis(ctx: CanvasRenderingContext2D, scale: Scale, options: AxisOptions): void {
  // 绘制轴线
  ctx.beginPath();
  ctx.moveTo(options.x, options.y);
  ctx.lineTo(options.x + options.length, options.y);
  ctx.stroke();

  // 绘制刻度
  const ticks = calculateTicks(scale.domain, options.tickCount);
  ticks.forEach(tick => {
    const x = scale.scale(tick);
    ctx.fillText(tick.toString(), x, options.y + 15);
  });
}
```

## 图表类型实现

### 折线图

```typescript
class LineChart extends Chart {
  render(): void {
    this.clear();
    this.drawAxes();
    this.drawGrid();
    this.drawLines();
    this.drawPoints();
    this.bindEvents();
  }

  private drawLines(): void {
    this.data.datasets.forEach(dataset => {
      this.ctx.beginPath();
      this.ctx.strokeStyle = dataset.color;
      dataset.data.forEach((value, index) => {
        const x = this.xScale.scale(index);
        const y = this.yScale.scale(value);
        if (index === 0) {
          this.ctx.moveTo(x, y);
        } else {
          this.ctx.lineTo(x, y);
        }
      });
      this.ctx.stroke();
    });
  }
}
```

### 柱状图

```typescript
class BarChart extends Chart {
  render(): void {
    this.clear();
    this.drawAxes();
    this.drawBars();
    this.bindEvents();
  }

  private drawBars(): void {
    const barWidth = this.calculateBarWidth();
    this.data.datasets.forEach((dataset, datasetIndex) => {
      dataset.data.forEach((value, index) => {
        const x = this.xScale.scale(index) - barWidth / 2;
        const y = this.yScale.scale(value);
        const height = this.yScale.scale(0) - y;

        this.ctx.fillStyle = dataset.color;
        this.ctx.fillRect(x, y, barWidth, height);
      });
    });
  }
}
```

### 饼图

```typescript
class PieChart extends Chart {
  render(): void {
    this.clear();
    this.drawPie();
    this.drawLabels();
    this.bindEvents();
  }

  private drawPie(): void {
    const total = this.data.datasets[0].data.reduce((a, b) => a + b, 0);
    let startAngle = -Math.PI / 2;

    this.data.datasets[0].data.forEach((value, index) => {
      const sliceAngle = (value / total) * Math.PI * 2;

      this.ctx.beginPath();
      this.ctx.moveTo(this.centerX, this.centerY);
      this.ctx.arc(this.centerX, this.centerY, this.radius, startAngle, startAngle + sliceAngle);
      this.ctx.closePath();
      this.ctx.fillStyle = COLORS[index % COLORS.length];
      this.ctx.fill();

      startAngle += sliceAngle;
    });
  }
}
```

## 交互系统

### Tooltip 实现

```typescript
class Tooltip {
  private element: HTMLDivElement;

  show(x: number, y: number, content: string): void {
    this.element.innerHTML = content;
    this.element.style.left = `${x}px`;
    this.element.style.top = `${y - 10}px`;
    this.element.style.opacity = '1';
  }

  hide(): void {
    this.element.style.opacity = '0';
  }
}
```

### 鼠标事件处理

```typescript
private bindEvents(): void {
  this.canvas.addEventListener('mousemove', (e) => {
    const rect = this.canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const dataPoint = this.getDataPointAt(x, y);
    if (dataPoint) {
      this.tooltip.show(x, y, this.formatTooltip(dataPoint));
    } else {
      this.tooltip.hide();
    }
  });
}
```
