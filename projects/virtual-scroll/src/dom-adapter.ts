/**
 * DOM 渲染适配器 - 用于浏览器环境
 * @module dom-adapter
 */

import { VirtualScroll } from './virtual-scroll';
import { ItemConfig, VirtualScrollOptions, VirtualScrollEvents, RenderItem } from './types';

export interface DOMAdapterOptions extends VirtualScrollOptions {
  /** 容器元素或选择器 */
  container: HTMLElement | string;
  /** 渲染函数 */
  renderItem: (item: RenderItem) => HTMLElement;
  /** 项目类名 */
  itemClassName?: string;
  /** 是否启用平滑滚动 */
  smoothScroll?: boolean;
}

export class DOMAdapter {
  /** 虚拟滚动实例 */
  private virtualScroll: VirtualScroll;

  /** 容器元素 */
  private container: HTMLElement;

  /** 视口元素 */
  private viewport: HTMLElement;

  /** 内容元素 */
  private content: HTMLElement;

  /** DOM 渲染函数 */
  private renderItem: (item: RenderItem) => HTMLElement;

  /** 项目类名 */
  private itemClassName: string;

  /** 是否启用平滑滚动 */
  private smoothScroll: boolean;

  /** 当前渲染的 DOM 元素 */
  private renderedElements: Map<number, HTMLElement> = new Map();

  /** 事件处理器 */
  private scrollHandler: (() => void) | null = null;

  constructor(options: DOMAdapterOptions) {
    // 获取容器元素
    if (typeof options.container === 'string') {
      const element = document.querySelector(options.container);
      if (!element) {
        throw new Error(`Container element not found: ${options.container}`);
      }
      this.container = element as HTMLElement;
    } else {
      this.container = options.container;
    }

    this.renderItem = options.renderItem;
    this.itemClassName = options.itemClassName || 'virtual-scroll-item';
    this.smoothScroll = options.smoothScroll ?? true;

    // 创建 DOM 结构
    this.viewport = this.createViewport();
    this.content = this.createContent();

    // 初始化虚拟滚动
    const scrollOptions: VirtualScrollOptions = {
      containerHeight: options.containerHeight,
      itemHeight: options.itemHeight,
      bufferCount: options.bufferCount,
      dynamicHeight: options.dynamicHeight,
      estimatedHeight: options.estimatedHeight,
      throttleInterval: options.throttleInterval
    };

    const events: VirtualScrollEvents = {
      onVisibleChange: () => this.renderVisibleItems(),
      ...options
    };

    this.virtualScroll = new VirtualScroll(scrollOptions, events);

    // 绑定滚动事件
    this.bindScrollEvent();
  }

  /**
   * 创建视口元素
   */
  private createViewport(): HTMLElement {
    const viewport = document.createElement('div');
    viewport.style.cssText = `
      overflow-y: auto;
      overflow-x: hidden;
      position: relative;
      width: 100%;
    `;

    this.container.appendChild(viewport);
    return viewport;
  }

  /**
   * 创建内容元素
   */
  private createContent(): HTMLElement {
    const content = document.createElement('div');
    content.style.cssText = `
      position: relative;
      width: 100%;
    `;

    this.viewport.appendChild(content);
    return content;
  }

  /**
   * 绑定滚动事件
   */
  private bindScrollEvent(): void {
    this.scrollHandler = () => {
      const scrollTop = this.viewport.scrollTop;
      const scrollLeft = this.viewport.scrollLeft;
      this.virtualScroll.handleScroll(scrollTop, scrollLeft);
    };

    this.viewport.addEventListener('scroll', this.scrollHandler, { passive: true });
  }

  /**
   * 设置数据源
   * @param items 数据项数组
   */
  setDataSource(items: ItemConfig[]): void {
    this.virtualScroll.setDataSource(items);

    // 更新内容高度
    this.content.style.height = `${this.virtualScroll.getTotalHeight()}px`;

    // 初始渲染
    this.renderVisibleItems();
  }

  /**
   * 渲染可视区域项目
   */
  private renderVisibleItems(): void {
    const renderItems = this.virtualScroll.getRenderItems();
    const startTime = performance.now();

    // 标记需要保留的项目
    const keepItems = new Set<number>();

    // 渲染新项目
    renderItems.forEach(item => {
      keepItems.add(item.index);

      let element = this.renderedElements.get(item.index);

      if (element) {
        // 更新已有元素位置
        element.style.top = `${item.style.top}px`;
        if (item.style.height !== 'auto') {
          element.style.height = `${item.style.height}px`;
        }
      } else {
        // 创建新元素
        element = this.renderItem(item);
        element.classList.add(this.itemClassName);
        element.style.position = 'absolute';
        element.style.top = `${item.style.top}px`;
        element.style.left = '0';
        element.style.width = '100%';

        if (item.style.height !== 'auto') {
          element.style.height = `${item.style.height}px`;
        }

        this.content.appendChild(element);
        this.renderedElements.set(item.index, element);

        // 动态高度模式下测量实际高度
        if (this.virtualScroll.getMetrics().totalItems > 0) {
          requestAnimationFrame(() => {
            if (element && element.parentNode) {
              const actualHeight = element.offsetHeight;
              this.virtualScroll.updateItemHeight(item.index, actualHeight);
            }
          });
        }
      }
    });

    // 移除不可见的元素
    for (const [index, element] of this.renderedElements) {
      if (!keepItems.has(index)) {
        element.remove();
        this.renderedElements.delete(index);
      }
    }

    // 更新总高度
    this.content.style.height = `${this.virtualScroll.getTotalHeight()}px`;
  }

  /**
   * 滚动到指定位置
   * @param index 目标索引
   * @param align 对齐方式
   */
  scrollToIndex(index: number, align: 'top' | 'center' | 'bottom' = 'top'): void {
    const targetScrollTop = this.virtualScroll.scrollToIndex(index, align);

    if (this.smoothScroll) {
      this.viewport.scrollTo({
        top: targetScrollTop,
        behavior: 'smooth'
      });
    } else {
      this.viewport.scrollTop = targetScrollTop;
    }
  }

  /**
   * 获取虚拟滚动实例
   */
  getVirtualScroll(): VirtualScroll {
    return this.virtualScroll;
  }

  /**
   * 获取性能指标
   */
  getMetrics() {
    return this.virtualScroll.getMetrics();
  }

  /**
   * 更新配置
   */
  updateOptions(options: Partial<VirtualScrollOptions>): void {
    this.virtualScroll.updateOptions(options);

    if (options.containerHeight !== undefined) {
      this.viewport.style.height = `${options.containerHeight}px`;
    }
  }

  /**
   * 销毁实例
   */
  destroy(): void {
    // 移除事件监听
    if (this.scrollHandler) {
      this.viewport.removeEventListener('scroll', this.scrollHandler);
    }

    // 清空 DOM
    this.renderedElements.forEach(element => element.remove());
    this.renderedElements.clear();

    // 销毁虚拟滚动实例
    this.virtualScroll.destroy();

    // 移除容器
    this.content.remove();
    this.viewport.remove();
  }
}
