/**
 * 图表基类
 */

import { CanvasRenderer, CanvasOptions } from './Canvas';
import { LinearScale, CategoryScale } from './Scale';
import { EventManager, ChartEvent } from './Event';
import { DEFAULT_COLORS } from '../utils/color';
import { getMinMax } from '../utils/math';

export interface Padding {
  top: number;
  right: number;
  bottom: number;
  left: number;
}

export interface ChartData {
  labels?: string[];
  datasets: Dataset[];
}

export interface Dataset {
  label: string;
  data: number[];
  color?: string;
}

export interface ChartOptions {
  width?: number;
  height?: number;
  padding?: Padding;
  backgroundColor?: string;
  title?: string;
  showLegend?: boolean;
  showGrid?: boolean;
  showTooltip?: boolean;
  smooth?: boolean;
  animation?: boolean;
}

export abstract class Chart {
  protected container: HTMLElement;
  protected renderer: CanvasRenderer;
  protected eventManager: EventManager;
  protected data: ChartData;
  protected options: Required<ChartOptions>;
  protected xScale: CategoryScale | null = null;
  protected yScale: LinearScale | null = null;
  protected colors: string[];

  constructor(
    container: string | HTMLElement,
    data: ChartData,
    options: ChartOptions = {}
  ) {
    // 获取容器元素
    if (typeof container === 'string') {
      const el = document.querySelector(container);
      if (!el) {
        throw new Error(`Container "${container}" not found`);
      }
      this.container = el as HTMLElement;
    } else {
      this.container = container;
    }

    // 合并默认选项
    this.options = {
      width: options.width || 600,
      height: options.height || 400,
      padding: options.padding || { top: 40, right: 40, bottom: 60, left: 60 },
      backgroundColor: options.backgroundColor || '#ffffff',
      title: options.title || '',
      showLegend: options.showLegend !== false,
      showGrid: options.showGrid !== false,
      showTooltip: options.showTooltip !== false,
      smooth: options.smooth || false,
      animation: options.animation !== false,
    };

    this.data = data;
    this.colors = DEFAULT_COLORS;

    // 创建渲染器
    this.renderer = new CanvasRenderer(this.container, {
      width: this.options.width,
      height: this.options.height,
      backgroundColor: this.options.backgroundColor,
    });

    // 创建事件管理器
    this.eventManager = new EventManager(this.renderer.canvas);

    // 绑定事件
    this.bindEvents();
  }

  /**
   * 计算绘图区域
   */
  protected get plotArea() {
    const { width, height, padding } = this.options;
    return {
      x: padding.left,
      y: padding.top,
      width: width - padding.left - padding.right,
      height: height - padding.top - padding.bottom,
    };
  }

  /**
   * 初始化比例尺
   */
  protected initScales(): void {
    const { labels, datasets } = this.data;
    const plot = this.plotArea;

    // X 轴分类比例尺
    if (labels && labels.length > 0) {
      this.xScale = new CategoryScale(labels, [plot.x, plot.x + plot.width]);
    }

    // Y 轴线性比例尺
    const allValues = datasets.flatMap(ds => ds.data);
    const { min, max } = getMinMax(allValues);
    const yPadding = (max - min) * 0.1 || 10;

    this.yScale = new LinearScale(
      [Math.min(0, min - yPadding), max + yPadding],
      [plot.y + plot.height, plot.y]
    );
  }

  /**
   * 绘制标题
   */
  protected drawTitle(): void {
    if (!this.options.title) return;

    const { width } = this.options;
    this.renderer.drawText(this.options.title, width / 2, 20, {
      color: '#333333',
      font: 'bold 16px sans-serif',
      align: 'center',
    });
  }

  /**
   * 绘制网格
   */
  protected drawGrid(): void {
    if (!this.options.showGrid || !this.yScale) return;

    const plot = this.plotArea;
    const ticks = this.yScale.getTicks(5);

    ticks.forEach(tick => {
      const y = this.yScale!.scale(tick);
      this.renderer.drawLine(plot.x, y, plot.x + plot.width, y, '#e0e0e0', 0.5);

      // Y 轴标签
      this.renderer.drawText(
        tick.toString(),
        plot.x - 10,
        y,
        { color: '#666666', font: '11px sans-serif', align: 'right' }
      );
    });
  }

  /**
   * 绘制坐标轴
   */
  protected drawAxes(): void {
    const plot = this.plotArea;

    // X 轴
    this.renderer.drawLine(
      plot.x, plot.y + plot.height,
      plot.x + plot.width, plot.y + plot.height,
      '#333333', 1
    );

    // Y 轴
    this.renderer.drawLine(
      plot.x, plot.y,
      plot.x, plot.y + plot.height,
      '#333333', 1
    );

    // X 轴标签
    if (this.data.labels && this.xScale) {
      this.data.labels.forEach((label, index) => {
        const x = this.xScale!.scale(index);
        this.renderer.drawText(
          label,
          x,
          plot.y + plot.height + 20,
          { color: '#666666', font: '11px sans-serif', align: 'center' }
        );
      });
    }
  }

  /**
   * 绘制图例
   */
  protected drawLegend(): void {
    if (!this.options.showLegend || this.data.datasets.length <= 1) return;

    const { width } = this.options;
    const legendY = this.options.height - 15;

    let legendX = width / 2 - (this.data.datasets.length * 80) / 2;

    this.data.datasets.forEach((dataset, index) => {
      const color = dataset.color || this.colors[index % this.colors.length];

      // 色块
      this.renderer.drawRect(legendX, legendY - 5, 12, 12, color);

      // 标签
      this.renderer.drawText(
        dataset.label,
        legendX + 16,
        legendY + 1,
        { color: '#666666', font: '11px sans-serif' }
      );

      legendX += 80;
    });
  }

  /**
   * 绑定事件
   */
  protected bindEvents(): void {
    if (this.options.showTooltip) {
      this.eventManager.on('mousemove', this.handleMouseMove.bind(this));
      this.eventManager.on('mouseleave', () => {
        this.eventManager.hideTooltip();
        this.onMouseLeave();
      });
    }

    this.eventManager.on('click', this.handleClick.bind(this));
  }

  /**
   * 处理鼠标移动（子类实现）
   */
  protected abstract handleMouseMove(event: ChartEvent): void;

  /**
   * 处理鼠标离开（子类实现）
   */
  protected abstract onMouseLeave(): void;

  /**
   * 处理点击（子类实现）
   */
  protected abstract handleClick(event: ChartEvent): void;

  /**
   * 渲染图表
   */
  abstract render(): void;

  /**
   * 更新数据
   */
  update(data: ChartData): void {
    this.data = data;
    this.render();
  }

  /**
   * 获取 Canvas 数据 URL
   */
  toDataURL(): string {
    return this.renderer.toDataURL();
  }

  /**
   * 销毁图表
   */
  destroy(): void {
    this.eventManager.destroy();
    this.renderer.destroy();
  }
}
