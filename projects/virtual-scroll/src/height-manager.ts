/**
 * 高度管理器 - 负责动态高度计算和缓存
 * @module height-manager
 */

import { CachedItem } from './types';

export class HeightManager {
  /** 高度缓存 */
  private cache: Map<number, CachedItem> = new Map();

  /** 预估高度 */
  private estimatedHeight: number;

  /** 缓存总数 */
  private totalCount: number = 0;

  /** 累计高度数组（用于快速查找） */
  private cumulativeHeights: number[] = [];

  /** 是否需要重新计算累计高度 */
  private dirty: boolean = true;

  constructor(estimatedHeight: number = 50) {
    this.estimatedHeight = estimatedHeight;
  }

  /**
   * 设置列表总数
   * @param count 列表项总数
   */
  setTotalCount(count: number): void {
    this.totalCount = count;
    this.dirty = true;

    // 清理超出范围的缓存
    for (const [index] of this.cache) {
      if (index >= count) {
        this.cache.delete(index);
      }
    }
  }

  /**
   * 获取列表总数
   */
  getTotalCount(): number {
    return this.totalCount;
  }

  /**
   * 设置预估高度
   * @param height 预估高度
   */
  setEstimatedHeight(height: number): void {
    this.estimatedHeight = height;
    this.dirty = true;
  }

  /**
   * 获取预估高度
   */
  getEstimatedHeight(): number {
    return this.estimatedHeight;
  }

  /**
   * 更新项目高度
   * @param index 项目索引
   * @param height 实际高度
   */
  updateItemHeight(index: number, height: number): void {
    const existing = this.cache.get(index);
    const offsetTop = this.calculateOffsetTop(index);

    this.cache.set(index, {
      index,
      height,
      offsetTop
    });

    this.dirty = true;

    // 更新后续项目的偏移量
    this.updateSubsequentOffsets(index);
  }

  /**
   * 获取项目高度
   * @param index 项目索引
   * @returns 项目高度
   */
  getItemHeight(index: number): number {
    const cached = this.cache.get(index);
    return cached ? cached.height : this.estimatedHeight;
  }

  /**
   * 获取项目偏移量
   * @param index 项目索引
   * @returns 项目顶部偏移量
   */
  getItemOffset(index: number): number {
    const cached = this.cache.get(index);
    if (cached) {
      return cached.offsetTop;
    }

    // 使用缓存数组快速计算
    if (this.dirty) {
      this.rebuildCumulativeHeights();
    }

    if (index < this.cumulativeHeights.length) {
      return this.cumulativeHeights[index];
    }

    // 估算位置
    return this.estimateOffset(index);
  }

  /**
   * 获取总高度
   * @returns 列表总高度
   */
  getTotalHeight(): number {
    if (this.totalCount === 0) return 0;

    if (this.dirty) {
      this.rebuildCumulativeHeights();
    }

    // 如果有最后缓存项，使用它
    if (this.cache.has(this.totalCount - 1)) {
      const lastItem = this.cache.get(this.totalCount - 1)!;
      return lastItem.offsetTop + lastItem.height;
    }

    // 估算总高度
    return this.totalCount * this.estimatedHeight;
  }

  /**
   * 根据滚动位置查找起始索引
   * @param scrollTop 滚动位置
   * @returns 起始索引
   */
  findStartIndex(scrollTop: number): number {
    if (this.dirty) {
      this.rebuildCumulativeHeights();
    }

    // 使用二分查找
    let low = 0;
    let high = this.totalCount - 1;

    while (low <= high) {
      const mid = Math.floor((low + high) / 2);
      const offset = this.getItemOffset(mid);

      if (offset === scrollTop) {
        return mid;
      } else if (offset < scrollTop) {
        low = mid + 1;
      } else {
        high = mid - 1;
      }
    }

    return Math.max(0, low - 1);
  }

  /**
   * 重建累计高度数组
   */
  private rebuildCumulativeHeights(): void {
    this.cumulativeHeights = new Array(this.totalCount);
    let cumulative = 0;

    for (let i = 0; i < this.totalCount; i++) {
      this.cumulativeHeights[i] = cumulative;
      cumulative += this.getItemHeight(i);
    }

    this.dirty = false;
  }

  /**
   * 计算项目偏移量
   * @param index 项目索引
   * @returns 偏移量
   */
  private calculateOffsetTop(index: number): number {
    let offset = 0;

    // 向前查找已缓存的项
    for (let i = index - 1; i >= Math.max(0, index - 100); i--) {
      const cached = this.cache.get(i);
      if (cached) {
        offset = cached.offsetTop + cached.height;

        // 计算中间未缓存项的高度
        for (let j = i + 1; j < index; j++) {
          offset += this.getItemHeight(j);
        }

        return offset;
      }
    }

    // 没找到缓存，从头计算
    for (let i = 0; i < index; i++) {
      offset += this.getItemHeight(i);
    }

    return offset;
  }

  /**
   * 更新后续项目的偏移量
   * @param index 更新的项目索引
   */
  private updateSubsequentOffsets(index: number): void {
    const current = this.cache.get(index);
    if (!current) return;

    // 更新后续缓存项的偏移量
    for (let i = index + 1; i < this.totalCount; i++) {
      const next = this.cache.get(i);
      if (next) {
        next.offsetTop = current.offsetTop + current.height;
        // 继续更新
        current.offsetTop = next.offsetTop;
        current.height = next.height;
      } else {
        break;
      }
    }
  }

  /**
   * 估算偏移量
   * @param index 项目索引
   * @returns 估算的偏移量
   */
  private estimateOffset(index: number): number {
    // 查找最近的已缓存项
    let nearestIndex = -1;
    let nearestOffset = 0;

    for (let i = index - 1; i >= Math.max(0, index - 100); i--) {
      const cached = this.cache.get(i);
      if (cached) {
        nearestIndex = i;
        nearestOffset = cached.offsetTop + cached.height;
        break;
      }
    }

    // 估算中间项的高度
    const itemsToEstimate = index - nearestIndex - 1;
    return nearestOffset + (itemsToEstimate * this.estimatedHeight);
  }

  /**
   * 清除缓存
   */
  clearCache(): void {
    this.cache.clear();
    this.dirty = true;
  }

  /**
   * 获取缓存大小
   */
  getCacheSize(): number {
    return this.cache.size;
  }

  /**
   * 获取缓存命中率
   * @returns 缓存命中率（0-1）
   */
  getCacheHitRate(): number {
    if (this.totalCount === 0) return 0;
    return this.cache.size / this.totalCount;
  }

  /**
   * 检查索引是否有效
   * @param index 项目索引
   * @returns 是否有效
   */
  isValidIndex(index: number): boolean {
    return index >= 0 && index < this.totalCount;
  }
}
