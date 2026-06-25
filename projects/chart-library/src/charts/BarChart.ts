/**
 * 柱状图实现
 */

import { Chart, ChartData, ChartOptions } from '../core/Chart';
import { ChartEvent } from '../core/Event';
import { isPointInRect } from '../utils/math';
import { darken } from '../utils/color';

interface Bar {
  x: number;
  y: number;
  width: number;
  height: number;
  value: number;
  label: string;
  datasetIndex: number;
  dataIndex: number;
}

export class BarChart extends Chart {
  private bars: Bar[] = [];
  private highlightedBar: Bar | null = null;

  constructor(
    container: string | HTMLElement,
    data: ChartData,
    options: ChartOptions = {}
  ) {
    super(container, data, options);
    this.render();
  }

  render(): void {
    this.renderer.clear(this.options.backgroundColor);
    this.initScales();
    this.drawTitle();
    this.drawGrid();
    this.drawAxes();
    this.drawBars();
    this.drawLegend();
  }

  private drawBars(): void {
    if (!this.xScale || !this.yScale) return;

    this.bars = [];
    const plot = this.plotArea;
    const datasetCount = this.data.datasets.length;
    const barGroupWidth = this.xScale.getBandwidth() * 0.8;
    const barWidth = barGroupWidth / datasetCount;
    const groupOffset = (this.xScale.getBandwidth() - barGroupWidth) / 2;

    this.data.datasets.forEach((dataset, datasetIndex) => {
      const color = dataset.color || this.colors[datasetIndex % this.colors.length];

      dataset.data.forEach((value, index) => {
        const x = this.xScale!.scale(index) - barGroupWidth / 2 + groupOffset + datasetIndex * barWidth;
        const y = this.yScale!.scale(value);
        const baseY = this.yScale!.scale(0);
        const height = baseY - y;

        const isHighlighted = this.highlightedBar &&
          this.highlightedBar.datasetIndex === datasetIndex &&
          this.highlightedBar.dataIndex === index;

        const barColor = isHighlighted ? darken(color, 30) : color;

        // 绘制柱子
        this.renderer.drawRoundedRect(x, y, barWidth - 2, Math.abs(height), 3, barColor);

        // 添加阴影效果
        if (isHighlighted) {
          this.renderer.ctx.shadowColor = 'rgba(0, 0, 0, 0.2)';
          this.renderer.ctx.shadowBlur = 8;
          this.renderer.ctx.shadowOffsetX = 2;
          this.renderer.ctx.shadowOffsetY = 2;
        }

        this.bars.push({
          x, y, width: barWidth - 2, height: Math.abs(height),
          value,
          label: this.data.labels?.[index] || index.toString(),
          datasetIndex,
          dataIndex: index,
        });

        // 重置阴影
        this.renderer.ctx.shadowColor = 'transparent';
        this.renderer.ctx.shadowBlur = 0;
        this.renderer.ctx.shadowOffsetX = 0;
        this.renderer.ctx.shadowOffsetY = 0;
      });
    });
  }

  protected handleMouseMove(event: ChartEvent): void {
    const { x, y } = event;
    const hoveredBar = this.findBarAt(x, y);

    if (hoveredBar) {
      this.highlightedBar = hoveredBar;
      this.eventManager.showTooltip(
        hoveredBar.x + hoveredBar.width / 2,
        hoveredBar.y,
        `<strong>${hoveredBar.label}</strong><br>${this.data.datasets[hoveredBar.datasetIndex].label}: ${hoveredBar.value}`
      );
      this.render();
    } else if (this.highlightedBar) {
      this.highlightedBar = null;
      this.eventManager.hideTooltip();
      this.render();
    }
  }

  protected onMouseLeave(): void {
    this.highlightedBar = null;
    this.render();
  }

  protected handleClick(event: ChartEvent): void {
    const { x, y } = event;
    const clickedBar = this.findBarAt(x, y);

    if (clickedBar) {
      this.eventManager.emit('barClick', {
        ...event,
        dataIndex: clickedBar.dataIndex,
        datasetIndex: clickedBar.datasetIndex,
        value: clickedBar.value,
      });
    }
  }

  private findBarAt(x: number, y: number): Bar | null {
    for (const bar of this.bars) {
      if (isPointInRect(x, y, bar.x, bar.y, bar.width, bar.height)) {
        return bar;
      }
    }
    return null;
  }
}
