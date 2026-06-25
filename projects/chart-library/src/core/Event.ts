/**
 * 事件系统
 */

export interface ChartEvent {
  x: number;
  y: number;
  dataX?: number;
  dataY?: number;
  dataIndex?: number;
  datasetIndex?: number;
  value?: number;
}

export type EventHandler = (event: ChartEvent) => void;

export class EventManager {
  private canvas: HTMLCanvasElement;
  private handlers: Map<string, EventHandler[]> = new Map();
  private tooltip: HTMLDivElement | null = null;

  constructor(canvas: HTMLCanvasElement) {
    this.canvas = canvas;
    this.setupEventListeners();
  }

  private setupEventListeners(): void {
    this.canvas.addEventListener('mousemove', this.handleMouseMove.bind(this));
    this.canvas.addEventListener('click', this.handleClick.bind(this));
    this.canvas.addEventListener('mouseleave', this.handleMouseLeave.bind(this));
  }

  private getMousePosition(event: MouseEvent): { x: number; y: number } {
    const rect = this.canvas.getBoundingClientRect();
    return {
      x: event.clientX - rect.left,
      y: event.clientY - rect.top,
    };
  }

  private handleMouseMove(event: MouseEvent): void {
    const pos = this.getMousePosition(event);
    this.emit('mousemove', { x: pos.x, y: pos.y });
  }

  private handleClick(event: MouseEvent): void {
    const pos = this.getMousePosition(event);
    this.emit('click', { x: pos.x, y: pos.y });
  }

  private handleMouseLeave(): void {
    this.emit('mouseleave', { x: 0, y: 0 });
  }

  on(event: string, handler: EventHandler): void {
    if (!this.handlers.has(event)) {
      this.handlers.set(event, []);
    }
    this.handlers.get(event)!.push(handler);
  }

  off(event: string, handler: EventHandler): void {
    const handlers = this.handlers.get(event);
    if (handlers) {
      const index = handlers.indexOf(handler);
      if (index > -1) {
        handlers.splice(index, 1);
      }
    }
  }

  emit(event: string, data: ChartEvent): void {
    const handlers = this.handlers.get(event);
    if (handlers) {
      handlers.forEach(handler => handler(data));
    }
  }

  createTooltip(): HTMLDivElement {
    if (this.tooltip) {
      return this.tooltip;
    }

    this.tooltip = document.createElement('div');
    this.tooltip.style.cssText = `
      position: absolute;
      background: rgba(0, 0, 0, 0.8);
      color: white;
      padding: 8px 12px;
      border-radius: 4px;
      font-size: 12px;
      pointer-events: none;
      opacity: 0;
      transition: opacity 0.2s;
      z-index: 1000;
      white-space: nowrap;
    `;

    const parent = this.canvas.parentElement;
    if (parent) {
      parent.style.position = 'relative';
      parent.appendChild(this.tooltip);
    }

    return this.tooltip;
  }

  showTooltip(x: number, y: number, content: string): void {
    const tooltip = this.createTooltip();
    tooltip.innerHTML = content;
    tooltip.style.left = `${x + 10}px`;
    tooltip.style.top = `${y - 10}px`;
    tooltip.style.opacity = '1';
  }

  hideTooltip(): void {
    if (this.tooltip) {
      this.tooltip.style.opacity = '0';
    }
  }

  destroy(): void {
    this.canvas.removeEventListener('mousemove', this.handleMouseMove.bind(this));
    this.canvas.removeEventListener('click', this.handleClick.bind(this));
    this.canvas.removeEventListener('mouseleave', this.handleMouseLeave.bind(this));
    this.handlers.clear();

    if (this.tooltip) {
      this.tooltip.remove();
      this.tooltip = null;
    }
  }
}
