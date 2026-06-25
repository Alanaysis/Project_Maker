/**
 * 折线图实现
 */

import { Chart, ChartData, ChartOptions } from '../core/Chart';
import { ChartEvent } from '../core/Event';
import { withAlpha } from '../utils/color';
import { distance } from '../utils/math';

interface Point {
  x: number;
  y: number;
  value: number;
  label: string;
  datasetIndex: number;
  dataIndex: number;
}

export class LineChart extends Chart {
  private points: Point[] = [];

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
    this.drawLines();
    this.drawPoints();
    this.drawLegend();
  }

  private drawLines(): void {
    if (!this.xScale || !this.yScale) return;

    this.points = [];

    this.data.datasets.forEach((dataset, datasetIndex) => {
      const color = dataset.color || this.colors[datasetIndex % this.colors.length];
      const linePoints: { x: number; y: number }[] = [];

      dataset.data.forEach((value, index) => {
        const x = this.xScale!.scale(index);
        const y = this.yScale!.scale(value);

        linePoints.push({ x, y });
        this.points.push({
          x, y, value,
          label: this.data.labels?.[index] || index.toString(),
          datasetIndex,
          dataIndex: index,
        });
      });

      // 绘制填充区域
      const fillColor = withAlpha(color, 0.1);
      this.renderer.drawPath(linePoints, color, 2, fillColor, this.options.smooth);

      // 绘制线条
      this.renderer.drawPath(linePoints, color, 2, undefined, this.options.smooth);
    });
  }

  private drawPoints(): void {
    this.points.forEach(point => {
      const color = this.data.datasets[point.datasetIndex].color ||
        this.colors[point.datasetIndex % this.colors.length];

      this.renderer.drawCircle(point.x, point.y, 4, '#ffffff', color, 2);
    });
  }

  protected handleMouseMove(event: ChartEvent): void {
    const { x, y } = event;
    const nearestPoint = this.findNearestPoint(x, y);

    if (nearestPoint && distance(x, y, nearestPoint.x, nearestPoint.y) < 20) {
      this.eventManager.showTooltip(
        nearestPoint.x,
        nearestPoint.y,
        `<strong>${nearestPoint.label}</strong><br>${this.data.datasets[nearestPoint.datasetIndex].label}: ${nearestPoint.value}`
      );
      this.highlightPoint(nearestPoint);
    } else {
      this.eventManager.hideTooltip();
      this.render();
    }
  }

  protected onMouseLeave(): void {
    this.render();
  }

  protected handleClick(event: ChartEvent): void {
    const { x, y } = event;
    const nearestPoint = this.findNearestPoint(x, y);

    if (nearestPoint && distance(x, y, nearestPoint.x, nearestPoint.y) < 20) {
      this.eventManager.emit('pointClick', {
        ...event,
        dataIndex: nearestPoint.dataIndex,
        datasetIndex: nearestPoint.datasetIndex,
        value: nearestPoint.value,
      });
    }
  }

  private findNearestPoint(x: number, y: number): Point | null {
    let nearest: Point | null = null;
    let minDist = Infinity;

    this.points.forEach(point => {
      const dist = distance(x, y, point.x, point.y);
      if (dist < minDist) {
        minDist = dist;
        nearest = point;
      }
    });

    return nearest;
  }

  private highlightPoint(point: Point): void {
    this.render();

    const color = this.data.datasets[point.datasetIndex].color ||
      this.colors[point.datasetIndex % this.colors.length];

    this.renderer.drawCircle(point.x, point.y, 6, '#ffffff', color, 3);
    this.renderer.drawCircle(point.x, point.y, 3, color);
  }
}
