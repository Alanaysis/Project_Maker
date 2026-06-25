/**
 * 饼图实现
 */

import { Chart, ChartData, ChartOptions } from '../core/Chart';
import { ChartEvent } from '../core/Event';
import { calculatePieAngles, isPointInArc, distance } from '../utils/math';
import { lighten, getContrastColor } from '../utils/color';

interface Slice {
  startAngle: number;
  endAngle: number;
  value: number;
  percentage: number;
  label: string;
  color: string;
  index: number;
}

export class PieChart extends Chart {
  private slices: Slice[] = [];
  private centerX: number = 0;
  private centerY: number = 0;
  private radius: number = 0;
  private highlightedSlice: Slice | null = null;

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
    this.drawTitle();
    this.calculateGeometry();
    this.drawPie();
    this.drawLabels();
    this.drawLegend();
  }

  private calculateGeometry(): void {
    const { width, height, padding } = this.options;
    this.centerX = width / 2;
    this.centerY = (height - padding.bottom) / 2 + padding.top / 2;
    this.radius = Math.min(
      width - padding.left - padding.right,
      height - padding.top - padding.bottom
    ) / 2 - 20;
  }

  private drawPie(): void {
    const values = this.data.datasets[0].data;
    const total = values.reduce((sum, val) => sum + val, 0);

    if (total === 0) return;

    const angles = calculatePieAngles(values);
    this.slices = [];

    angles.forEach((angle, index) => {
      const color = this.data.datasets[0].color ||
        this.colors[index % this.colors.length];
      const value = values[index];
      const percentage = (value / total) * 100;

      const isHighlighted = this.highlightedSlice?.index === index;
      const sliceColor = isHighlighted ? lighten(color, 20) : color;

      // 绘制扇形
      this.renderer.ctx.beginPath();
      if (isHighlighted) {
        // 高亮时稍微偏移
        const midAngle = (angle.start + angle.end) / 2;
        const offsetX = Math.cos(midAngle) * 10;
        const offsetY = Math.sin(midAngle) * 10;
        this.renderer.ctx.moveTo(this.centerX + offsetX, this.centerY + offsetY);
        this.renderer.ctx.arc(
          this.centerX + offsetX,
          this.centerY + offsetY,
          this.radius,
          angle.start,
          angle.end
        );
      } else {
        this.renderer.ctx.moveTo(this.centerX, this.centerY);
        this.renderer.ctx.arc(this.centerX, this.centerY, this.radius, angle.start, angle.end);
      }
      this.renderer.ctx.closePath();

      // 填充颜色
      this.renderer.ctx.fillStyle = sliceColor;
      this.renderer.ctx.fill();

      // 边框
      this.renderer.ctx.strokeStyle = '#ffffff';
      this.renderer.ctx.lineWidth = 2;
      this.renderer.ctx.stroke();

      this.slices.push({
        startAngle: angle.start,
        endAngle: angle.end,
        value,
        percentage,
        label: this.data.labels?.[index] || `Slice ${index + 1}`,
        color,
        index,
      });
    });
  }

  private drawLabels(): void {
    this.slices.forEach(slice => {
      const midAngle = (slice.startAngle + slice.endAngle) / 2;
      const labelRadius = this.radius * 0.7;
      const x = this.centerX + Math.cos(midAngle) * labelRadius;
      const y = this.centerY + Math.sin(midAngle) * labelRadius;

      // 只显示占比大于 5% 的标签
      if (slice.percentage >= 5) {
        const textColor = getContrastColor(slice.color);
        this.renderer.drawText(
          `${slice.percentage.toFixed(1)}%`,
          x, y,
          {
            color: textColor,
            font: 'bold 12px sans-serif',
            align: 'center',
            baseline: 'middle',
          }
        );
      }
    });
  }

  protected handleMouseMove(event: ChartEvent): void {
    const { x, y } = event;
    const hoveredSlice = this.findSliceAt(x, y);

    if (hoveredSlice) {
      this.highlightedSlice = hoveredSlice;
      this.eventManager.showTooltip(
        x, y,
        `<strong>${hoveredSlice.label}</strong><br>值: ${hoveredSlice.value}<br>占比: ${hoveredSlice.percentage.toFixed(1)}%`
      );
      this.render();
    } else if (this.highlightedSlice) {
      this.highlightedSlice = null;
      this.eventManager.hideTooltip();
      this.render();
    }
  }

  protected onMouseLeave(): void {
    this.highlightedSlice = null;
    this.render();
  }

  protected handleClick(event: ChartEvent): void {
    const { x, y } = event;
    const clickedSlice = this.findSliceAt(x, y);

    if (clickedSlice) {
      this.eventManager.emit('sliceClick', {
        ...event,
        dataIndex: clickedSlice.index,
        value: clickedSlice.value,
      });
    }
  }

  private findSliceAt(x: number, y: number): Slice | null {
    if (distance(x, y, this.centerX, this.centerY) > this.radius) {
      return null;
    }

    for (const slice of this.slices) {
      if (isPointInArc(x, y, this.centerX, this.centerY, this.radius, slice.startAngle, slice.endAngle)) {
        return slice;
      }
    }

    return null;
  }
}
