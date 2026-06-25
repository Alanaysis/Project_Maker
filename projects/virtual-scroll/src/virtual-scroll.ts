/**
 * 虚拟滚动核心类
 * @module virtual-scroll
 */

import {
  VirtualScrollOptions,
  VirtualScrollEvents,
  ScrollPosition,
  VisibleRange,
  RenderItem,
  ItemConfig,
  PerformanceMetrics
} from './types';
import { HeightManager } from './height-manager';

/** 默认配置 */
const DEFAULT_OPTIONS: Required<VirtualScrollOptions> = {
  containerHeight: 400,
  itemHeight: 50,
  bufferCount: 5,
  dynamicHeight: false,
  estimatedHeight: 50,
  throttleInterval: 16,
  alignToTop: false
};

export class VirtualScroll {
  /** 配置选项 */
  private options: Required<VirtualScrollOptions>;

  /** 事件处理器 */
  private events: VirtualScrollEvents;

  /** 高度管理器 */
  private heightManager: HeightManager;

  /** 数据源 */
  private dataSource: ItemConfig[] = [];

  /** 当前滚动位置 */
  private scrollPosition: ScrollPosition = { scrollTop: 0, scrollLeft: 0 };

  /** 当前可视范围 */
  private visibleRange: VisibleRange = { startIndex: 0, endIndex: 0, offsetY: 0 };

  /** 渲染队列 */
  private renderQueue: RenderItem[] = [];

  /** 滚动节流定时器 */
  private scrollTimer: number | null = null;

  /** 性能统计 */
  private metrics: PerformanceMetrics = {
    totalItems: 0,
    renderedItems: 0,
    cacheHitRate: 0,
    scrollFPS: 0,
    averageRenderTime: 0
  };

  /** FPS 计算相关 */
  private frameCount: number = 0;
  private lastFrameTime: number = 0;
  private fpsTimer: number | null = null;

  /** 渲染时间记录 */
  private renderTimes: number[] = [];

  /** 是否已销毁 */
  private destroyed: boolean = false;

  constructor(
    options: Partial<VirtualScrollOptions> = {},
    events: VirtualScrollEvents = {}
  ) {
    this.options = { ...DEFAULT_OPTIONS, ...options };
    this.events = events;
    this.heightManager = new HeightManager(
      this.options.dynamicHeight ? this.options.estimatedHeight : this.options.itemHeight
    );

    // 启动 FPS 监控
    this.startFPSMonitor();
  }

  /**
   * 设置数据源
   * @param items 数据项数组
   */
  setDataSource(items: ItemConfig[]): void {
    this.dataSource = items;
    this.heightManager.setTotalCount(items.length);
    this.metrics.totalItems = items.length;

    // 清除高度缓存
    if (this.options.dynamicHeight) {
      this.heightManager.clearCache();
    }

    this.updateVisibleRange();
  }

  /**
   * 更新单个数据项
   * @param index 索引
   * @param item 新数据
   */
  updateItem(index: number, item: ItemConfig): void {
    if (index >= 0 && index < this.dataSource.length) {
      this.dataSource[index] = item;
      this.updateVisibleRange();
    }
  }

  /**
   * 添加数据项
   * @param items 新增数据项
   */
  appendItems(items: ItemConfig[]): void {
    this.dataSource.push(...items);
    this.heightManager.setTotalCount(this.dataSource.length);
    this.metrics.totalItems = this.dataSource.length;
    this.updateVisibleRange();
  }

  /**
   * 处理滚动事件
   * @param scrollTop 滚动位置
   * @param scrollLeft 水平滚动位置
   */
  handleScroll(scrollTop: number, scrollLeft: number = 0): void {
    if (this.destroyed) return;

    // 节流处理
    if (this.scrollTimer) {
      return;
    }

    this.scrollTimer = setTimeout(() => {
      this.scrollPosition = { scrollTop, scrollLeft };
      this.updateVisibleRange();

      // 触发滚动回调
      this.events.onScroll?.(this.scrollPosition);

      this.scrollTimer = null;
    }, this.options.throttleInterval) as any;
  }

  /**
   * 更新可视范围
   */
  private updateVisibleRange(): void {
    const startTime = performance.now();

    const { scrollTop } = this.scrollPosition;
    const { containerHeight, bufferCount } = this.options;

    // 查找起始索引
    const startIndex = this.heightManager.findStartIndex(scrollTop);

    // 计算结束索引
    let endIndex = startIndex;
    let currentHeight = 0;

    while (endIndex < this.dataSource.length && currentHeight < containerHeight) {
      currentHeight += this.heightManager.getItemHeight(endIndex);
      endIndex++;
    }

    // 添加缓冲区
    const bufferedStart = Math.max(0, startIndex - bufferCount);
    const bufferedEnd = Math.min(this.dataSource.length - 1, endIndex + bufferCount);

    // 计算偏移量
    const offsetY = this.heightManager.getItemOffset(bufferedStart);

    this.visibleRange = {
      startIndex: bufferedStart,
      endIndex: bufferedEnd,
      offsetY
    };

    // 生成渲染队列
    this.buildRenderQueue();

    // 触发可视范围变化回调
    this.events.onVisibleChange?.(this.visibleRange);

    // 记录渲染时间
    const renderTime = performance.now() - startTime;
    this.renderTimes.push(renderTime);

    // 保持最近 100 条记录
    if (this.renderTimes.length > 100) {
      this.renderTimes.shift();
    }

    // 更新性能指标
    this.updateMetrics();
  }

  /**
   * 构建渲染队列
   */
  private buildRenderQueue(): void {
    this.renderQueue = [];

    for (let i = this.visibleRange.startIndex; i <= this.visibleRange.endIndex; i++) {
      const item = this.dataSource[i];
      if (!item) continue;

      const itemHeight = this.heightManager.getItemHeight(i);
      const itemOffset = this.heightManager.getItemOffset(i);

      this.renderQueue.push({
        index: i,
        data: item.data,
        style: {
          position: 'absolute',
          top: itemOffset,
          left: 0,
          width: '100%',
          height: this.options.dynamicHeight ? itemHeight : this.options.itemHeight
        }
      });

      // 触发项目渲染回调
      this.events.onItemRender?.(i, item);
    }
  }

  /**
   * 更新项目高度（动态高度模式）
   * @param index 项目索引
   * @param height 实际高度
   */
  updateItemHeight(index: number, height: number): void {
    if (!this.options.dynamicHeight) return;

    this.heightManager.updateItemHeight(index, height);
    this.updateVisibleRange();
  }

  /**
   * 滚动到指定位置
   * @param index 目标索引
   * @param align 对齐方式（'top' | 'center' | 'bottom'）
   * @returns 目标滚动位置
   */
  scrollToIndex(index: number, align: 'top' | 'center' | 'bottom' = 'top'): number {
    if (!this.heightManager.isValidIndex(index)) {
      return this.scrollPosition.scrollTop;
    }

    const itemOffset = this.heightManager.getItemOffset(index);
    const itemHeight = this.heightManager.getItemHeight(index);
    const containerHeight = this.options.containerHeight;

    let targetScrollTop: number;

    switch (align) {
      case 'center':
        targetScrollTop = itemOffset - (containerHeight - itemHeight) / 2;
        break;
      case 'bottom':
        targetScrollTop = itemOffset - containerHeight + itemHeight;
        break;
      case 'top':
      default:
        targetScrollTop = itemOffset;
        break;
    }

    // 确保不超出边界
    const maxScrollTop = this.heightManager.getTotalHeight() - containerHeight;
    targetScrollTop = Math.max(0, Math.min(targetScrollTop, maxScrollTop));

    return targetScrollTop;
  }

  /**
   * 获取渲染队列
   * @returns 渲染项目数组
   */
  getRenderItems(): RenderItem[] {
    return [...this.renderQueue];
  }

  /**
   * 获取可视范围
   * @returns 可视范围
   */
  getVisibleRange(): VisibleRange {
    return { ...this.visibleRange };
  }

  /**
   * 获取滚动位置
   * @returns 滚动位置
   */
  getScrollPosition(): ScrollPosition {
    return { ...this.scrollPosition };
  }

  /**
   * 获取总高度
   * @returns 列表总高度
   */
  getTotalHeight(): number {
    return this.heightManager.getTotalHeight();
  }

  /**
   * 获取性能指标
   * @returns 性能指标
   */
  getMetrics(): PerformanceMetrics {
    return { ...this.metrics };
  }

  /**
   * 更新性能指标
   */
  private updateMetrics(): void {
    this.metrics.renderedItems = this.renderQueue.length;
    this.metrics.cacheHitRate = this.heightManager.getCacheHitRate();
    this.metrics.averageRenderTime = this.renderTimes.length > 0
      ? this.renderTimes.reduce((a, b) => a + b, 0) / this.renderTimes.length
      : 0;
  }

  /**
   * 启动 FPS 监控
   */
  private startFPSMonitor(): void {
    this.lastFrameTime = performance.now();
    this.frameCount = 0;

    // 模拟 FPS 监控（实际使用时在浏览器环境）
    this.fpsTimer = setInterval(() => {
      this.frameCount++;
      const currentTime = performance.now();
      const elapsed = currentTime - this.lastFrameTime;

      if (elapsed >= 1000) {
        this.metrics.scrollFPS = Math.round((this.frameCount * 1000) / elapsed);
        this.frameCount = 0;
        this.lastFrameTime = currentTime;
      }
    }, 1000) as any;
  }

  /**
   * 更新配置
   * @param options 新配置
   */
  updateOptions(options: Partial<VirtualScrollOptions>): void {
    this.options = { ...this.options, ...options };

    if (options.estimatedHeight !== undefined) {
      this.heightManager.setEstimatedHeight(options.estimatedHeight);
    }

    this.updateVisibleRange();
  }

  /**
   * 销毁实例
   */
  destroy(): void {
    this.destroyed = true;

    if (this.scrollTimer) {
      clearTimeout(this.scrollTimer);
      this.scrollTimer = null;
    }

    if (this.fpsTimer) {
      clearInterval(this.fpsTimer);
      this.fpsTimer = null;
    }

    this.heightManager.clearCache();
    this.dataSource = [];
    this.renderQueue = [];
  }

  /**
   * 检查是否已销毁
   * @returns 是否已销毁
   */
  isDestroyed(): boolean {
    return this.destroyed;
  }
}
