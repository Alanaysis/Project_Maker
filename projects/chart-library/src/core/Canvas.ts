/**
 * Canvas 渲染器
 */

export interface CanvasOptions {
  width: number;
  height: number;
  backgroundColor?: string;
}

export class CanvasRenderer {
  canvas: HTMLCanvasElement;
  ctx: CanvasRenderingContext2D;
  width: number;
  height: number;
  dpr: number;

  constructor(container: HTMLElement, options: CanvasOptions) {
    this.width = options.width;
    this.height = options.height;
    this.dpr = window.devicePixelRatio || 1;

    this.canvas = document.createElement('canvas');
    this.setupCanvas();

    container.appendChild(this.canvas);

    const ctx = this.canvas.getContext('2d');
    if (!ctx) {
      throw new Error('Failed to get 2d context');
    }
    this.ctx = ctx;

    if (options.backgroundColor) {
      this.clear(options.backgroundColor);
    }
  }

  private setupCanvas(): void {
    this.canvas.width = this.width * this.dpr;
    this.canvas.height = this.height * this.dpr;
    this.canvas.style.width = `${this.width}px`;
    this.canvas.style.height = `${this.height}px`;
    this.ctx.scale(this.dpr, this.dpr);
  }

  clear(color?: string): void {
    this.ctx.save();
    this.ctx.setTransform(1, 0, 0, 1, 0, 0);
    if (color) {
      this.ctx.fillStyle = color;
      this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
    } else {
      this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    }
    this.ctx.restore();
  }

  /**
   * 绘制线条
   */
  drawLine(
    x1: number, y1: number, x2: number, y2: number,
    color: string, lineWidth: number = 1
  ): void {
    this.ctx.beginPath();
    this.ctx.strokeStyle = color;
    this.ctx.lineWidth = lineWidth;
    this.ctx.moveTo(x1, y1);
    this.ctx.lineTo(x2, y2);
    this.ctx.stroke();
  }

  /**
   * 绘制矩形
   */
  drawRect(
    x: number, y: number, width: number, height: number,
    color: string, stroke?: string, strokeWidth?: number
  ): void {
    this.ctx.beginPath();
    this.ctx.fillStyle = color;
    this.ctx.fillRect(x, y, width, height);

    if (stroke) {
      this.ctx.strokeStyle = stroke;
      this.ctx.lineWidth = strokeWidth || 1;
      this.ctx.strokeRect(x, y, width, height);
    }
  }

  /**
   * 绘制圆角矩形
   */
  drawRoundedRect(
    x: number, y: number, width: number, height: number,
    radius: number, color: string
  ): void {
    this.ctx.beginPath();
    this.ctx.fillStyle = color;
    this.ctx.moveTo(x + radius, y);
    this.ctx.lineTo(x + width - radius, y);
    this.ctx.quadraticCurveTo(x + width, y, x + width, y + radius);
    this.ctx.lineTo(x + width, y + height - radius);
    this.ctx.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
    this.ctx.lineTo(x + radius, y + height);
    this.ctx.quadraticCurveTo(x, y + height, x, y + height - radius);
    this.ctx.lineTo(x, y + radius);
    this.ctx.quadraticCurveTo(x, y, x + radius, y);
    this.ctx.closePath();
    this.ctx.fill();
  }

  /**
   * 绘制圆
   */
  drawCircle(
    x: number, y: number, radius: number,
    color: string, stroke?: string, strokeWidth?: number
  ): void {
    this.ctx.beginPath();
    this.ctx.arc(x, y, radius, 0, Math.PI * 2);
    this.ctx.fillStyle = color;
    this.ctx.fill();

    if (stroke) {
      this.ctx.strokeStyle = stroke;
      this.ctx.lineWidth = strokeWidth || 1;
      this.ctx.stroke();
    }
  }

  /**
   * 绘制圆弧
   */
  drawArc(
    x: number, y: number, radius: number,
    startAngle: number, endAngle: number,
    color: string, stroke?: string
  ): void {
    this.ctx.beginPath();
    this.ctx.moveTo(x, y);
    this.ctx.arc(x, y, radius, startAngle, endAngle);
    this.ctx.closePath();
    this.ctx.fillStyle = color;
    this.ctx.fill();

    if (stroke) {
      this.ctx.strokeStyle = stroke;
      this.ctx.lineWidth = 1;
      this.ctx.stroke();
    }
  }

  /**
   * 绘制文字
   */
  drawText(
    text: string, x: number, y: number,
    options: {
      color?: string;
      font?: string;
      align?: CanvasTextAlign;
      baseline?: CanvasTextBaseline;
    } = {}
  ): void {
    this.ctx.fillStyle = options.color || '#333333';
    this.ctx.font = options.font || '12px sans-serif';
    this.ctx.textAlign = options.align || 'left';
    this.ctx.textBaseline = options.baseline || 'middle';
    this.ctx.fillText(text, x, y);
  }

  /**
   * 绘制路径
   */
  drawPath(
    points: { x: number; y: number }[],
    color: string, lineWidth: number = 2,
    fill?: string, smooth: boolean = false
  ): void {
    if (points.length < 2) return;

    this.ctx.beginPath();
    this.ctx.strokeStyle = color;
    this.ctx.lineWidth = lineWidth;
    this.ctx.lineJoin = 'round';
    this.ctx.lineCap = 'round';

    if (smooth && points.length > 2) {
      // 贝塞尔曲线平滑
      this.ctx.moveTo(points[0].x, points[0].y);

      for (let i = 0; i < points.length - 1; i++) {
        const cp1x = (points[i].x + points[i + 1].x) / 2;
        const cp1y = points[i].y;
        const cp2x = (points[i].x + points[i + 1].x) / 2;
        const cp2y = points[i + 1].y;
        this.ctx.bezierCurveTo(cp1x, cp1y, cp2x, cp2y, points[i + 1].x, points[i + 1].y);
      }
    } else {
      this.ctx.moveTo(points[0].x, points[0].y);
      for (let i = 1; i < points.length; i++) {
        this.ctx.lineTo(points[i].x, points[i].y);
      }
    }

    this.ctx.stroke();

    if (fill) {
      // 闭合路径进行填充
      this.ctx.lineTo(points[points.length - 1].x, this.height);
      this.ctx.lineTo(points[0].x, this.height);
      this.ctx.closePath();
      this.ctx.fillStyle = fill;
      this.ctx.fill();
    }
  }

  /**
   * 获取 Canvas 数据 URL
   */
  toDataURL(): string {
    return this.canvas.toDataURL();
  }

  /**
   * 销毁渲染器
   */
  destroy(): void {
    this.canvas.remove();
  }
}
