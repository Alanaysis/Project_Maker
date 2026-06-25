/**
 * 拖拽系统工具函数
 *
 * 提供拖拽系统中常用的工具函数
 */

import { Position, Rect, Size, EventHandler, RemoveEventListener } from './types';

/**
 * 获取元素相对于文档的位置
 */
export function getElementRect(element: HTMLElement): Rect {
  const rect = element.getBoundingClientRect();
  return {
    x: rect.left + window.scrollX,
    y: rect.top + window.scrollY,
    width: rect.width,
    height: rect.height,
  };
}

/**
 * 获取元素中心点
 */
export function getElementCenter(element: HTMLElement): Position {
  const rect = getElementRect(element);
  return {
    x: rect.x + rect.width / 2,
    y: rect.y + rect.height / 2,
  };
}

/**
 * 计算两点之间的距离
 */
export function getDistance(p1: Position, p2: Position): number {
  const dx = p2.x - p1.x;
  const dy = p2.y - p1.y;
  return Math.sqrt(dx * dx + dy * dy);
}

/**
 * 检查点是否在矩形内
 */
export function isPointInRect(point: Position, rect: Rect): boolean {
  return (
    point.x >= rect.x &&
    point.x <= rect.x + rect.width &&
    point.y >= rect.y &&
    point.y <= rect.y + rect.height
  );
}

/**
 * 计算两个矩形的重叠面积
 */
export function getOverlapArea(rect1: Rect, rect2: Rect): number {
  const xOverlap = Math.max(
    0,
    Math.min(rect1.x + rect1.width, rect2.x + rect2.width) -
      Math.max(rect1.x, rect2.x)
  );
  const yOverlap = Math.max(
    0,
    Math.min(rect1.y + rect1.height, rect2.y + rect2.height) -
      Math.max(rect1.y, rect2.y)
  );
  return xOverlap * yOverlap;
}

/**
 * 克隆 DOM 元素
 */
export function cloneElement(element: HTMLElement, deep: boolean = true): HTMLElement {
  return element.cloneNode(deep) as HTMLElement;
}

/**
 * 设置元素样式
 */
export function setStyles(
  element: HTMLElement,
  styles: Partial<CSSStyleDeclaration>
): void {
  Object.assign(element.style, styles);
}

/**
 * 添加类名
 */
export function addClass(element: HTMLElement, ...classNames: string[]): void {
  element.classList.add(...classNames.filter(Boolean));
}

/**
 * 移除类名
 */
export function removeClass(element: HTMLElement, ...classNames: string[]): void {
  element.classList.remove(...classNames.filter(Boolean));
}

/**
 * 切换类名
 */
export function toggleClass(
  element: HTMLElement,
  className: string,
  force?: boolean
): boolean {
  return element.classList.toggle(className, force);
}

/**
 * 生成唯一 ID
 */
export function generateId(prefix: string = 'dd'): string {
  return `${prefix}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * 节流函数
 */
export function throttle<T extends (...args: unknown[]) => unknown>(
  fn: T,
  delay: number
): T {
  let lastTime = 0;
  let timer: ReturnType<typeof setTimeout> | null = null;

  return ((...args: unknown[]) => {
    const now = Date.now();
    const remaining = delay - (now - lastTime);

    if (remaining <= 0) {
      if (timer) {
        clearTimeout(timer);
        timer = null;
      }
      lastTime = now;
      fn(...args);
    } else if (!timer) {
      timer = setTimeout(() => {
        lastTime = Date.now();
        timer = null;
        fn(...args);
      }, remaining);
    }
  }) as unknown as T;
}

/**
 * 防抖函数
 */
export function debounce<T extends (...args: unknown[]) => unknown>(
  fn: T,
  delay: number
): T {
  let timer: ReturnType<typeof setTimeout> | null = null;

  return ((...args: unknown[]) => {
    if (timer) {
      clearTimeout(timer);
    }
    timer = setTimeout(() => {
      timer = null;
      fn(...args);
    }, delay);
  }) as unknown as T;
}

/**
 * 获取滚动容器
 */
export function getScrollParent(element: HTMLElement): HTMLElement {
  const style = getComputedStyle(element);
  const overflow = style.overflow + style.overflowY + style.overflowX;

  if (/auto|scroll/.test(overflow)) {
    return element;
  }

  if (element.parentElement) {
    return getScrollParent(element.parentElement);
  }

  return document.documentElement;
}

/**
 * 自动滚动
 */
export function autoScroll(
  container: HTMLElement,
  position: Position,
  speed: number = 10
): { stop: () => void } {
  let animFrameId: number | null = null;
  let scrollX = 0;
  let scrollY = 0;

  const update = () => {
    if (scrollX !== 0 || scrollY !== 0) {
      container.scrollLeft += scrollX;
      container.scrollTop += scrollY;
      animFrameId = requestAnimationFrame(update);
    }
  };

  const onMove = (pos: Position) => {
    const rect = container.getBoundingClientRect();
    const threshold = 40;

    scrollX = 0;
    scrollY = 0;

    if (pos.y - rect.top < threshold) {
      scrollY = -speed;
    } else if (rect.bottom - pos.y < threshold) {
      scrollY = speed;
    }

    if (pos.x - rect.left < threshold) {
      scrollX = -speed;
    } else if (rect.right - pos.x < threshold) {
      scrollX = speed;
    }

    if (scrollX !== 0 || scrollY !== 0) {
      if (!animFrameId) {
        animFrameId = requestAnimationFrame(update);
      }
    }
  };

  const stop = () => {
    scrollX = 0;
    scrollY = 0;
    if (animFrameId) {
      cancelAnimationFrame(animFrameId);
      animFrameId = null;
    }
  };

  // Return stop function and a way to update position
  return { stop };
}

/**
 * 验证文件类型
 */
export function validateFileType(file: File, accept: string[]): boolean {
  if (accept.length === 0) return true;

  return accept.some((pattern) => {
    // Handle MIME types like "image/*"
    if (pattern.endsWith('/*')) {
      const baseType = pattern.slice(0, -2);
      return file.type.startsWith(baseType);
    }

    // Handle extensions like ".jpg", ".png"
    if (pattern.startsWith('.')) {
      const ext = file.name.toLowerCase().split('.').pop();
      return ext === pattern.slice(1).toLowerCase();
    }

    // Handle exact MIME types
    return file.type === pattern;
  });
}

/**
 * 验证文件大小
 */
export function validateFileSize(file: File, maxSize: number): boolean {
  return file.size <= maxSize;
}

/**
 * 格式化文件大小
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';

  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  const k = 1024;
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return `${(bytes / Math.pow(k, i)).toFixed(2)} ${units[i]}`;
}

/**
 * 创建文件预览
 */
export function createFilePreview(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    if (!file.type.startsWith('image/')) {
      reject(new Error('File is not an image'));
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      resolve(e.target?.result as string);
    };
    reader.onerror = () => {
      reject(new Error('Failed to read file'));
    };
    reader.readAsDataURL(file);
  });
}

/**
 * 创建事件总线
 */
export class EventBus<T extends Record<string, unknown>> {
  private listeners = new Map<keyof T, Set<EventHandler<unknown>>>();

  on<K extends keyof T>(event: K, handler: EventHandler<T[K]>): RemoveEventListener {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)!.add(handler as EventHandler<unknown>);

    return () => {
      this.off(event, handler);
    };
  }

  off<K extends keyof T>(event: K, handler: EventHandler<T[K]>): void {
    this.listeners.get(event)?.delete(handler as EventHandler<unknown>);
  }

  emit<K extends keyof T>(event: K, data: T[K]): void {
    this.listeners.get(event)?.forEach((handler) => {
      try {
        (handler as EventHandler<T[K]>)(data);
      } catch (error) {
        console.error(`Error in event handler for ${String(event)}:`, error);
      }
    });
  }

  clear(): void {
    this.listeners.clear();
  }
}
