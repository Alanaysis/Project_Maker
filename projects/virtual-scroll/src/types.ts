/**
 * 虚拟滚动组件类型定义
 * @module types
 */

/** 滚动位置 */
export interface ScrollPosition {
  scrollTop: number;
  scrollLeft: number;
}

/** 可视区域范围 */
export interface VisibleRange {
  startIndex: number;
  endIndex: number;
  offsetY: number;
}

/** 列表项配置 */
export interface ItemConfig {
  /** 唯一标识符 */
  id: string | number;
  /** 高度（固定高度模式） */
  height?: number;
  /** 数据 */
  data: any;
}

/** 缓存项信息 */
export interface CachedItem {
  index: number;
  height: number;
  offsetTop: number;
}

/** 虚拟滚动配置选项 */
export interface VirtualScrollOptions {
  /** 容器高度 */
  containerHeight: number;
  /** 项目高度（固定高度模式） */
  itemHeight?: number;
  /** 缓冲区项目数量 */
  bufferCount?: number;
  /** 是否使用动态高度 */
  dynamicHeight?: boolean;
  /** 预估高度（动态高度模式下的初始估算） */
  estimatedHeight?: number;
  /** 滚动节流间隔（毫秒） */
  throttleInterval?: number;
  /** 是否启用滚动对齐 */
  alignToTop?: boolean;
}

/** 虚拟滚动事件 */
export interface VirtualScrollEvents {
  onScroll?: (position: ScrollPosition) => void;
  onVisibleChange?: (range: VisibleRange) => void;
  onItemRender?: (index: number, item: ItemConfig) => void;
  onItemDestroy?: (index: number) => void;
}

/** 渲染项目信息 */
export interface RenderItem {
  index: number;
  data: any;
  style: {
    position: 'absolute';
    top: number;
    left: number;
    width: string;
    height: number | 'auto';
  };
}

/** 性能统计信息 */
export interface PerformanceMetrics {
  totalItems: number;
  renderedItems: number;
  cacheHitRate: number;
  scrollFPS: number;
  averageRenderTime: number;
}
