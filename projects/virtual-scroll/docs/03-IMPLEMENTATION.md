# 03 - 实现细节

## 核心算法实现

### 1. 可视范围计算算法

**问题描述**：给定滚动位置，计算需要渲染的项目范围。

**算法思路**：
```
输入：scrollTop, containerHeight, bufferCount
输出：{ startIndex, endIndex, offsetY }

1. 查找起始索引：使用二分查找找到 scrollTop 对应的项目索引
2. 计算结束索引：从起始索引开始累加高度，直到超过容器高度
3. 添加缓冲区：向前后扩展 bufferCount 个项目
4. 计算偏移量：缓冲区起始项的顶部偏移
```

**代码实现**：
```typescript
private updateVisibleRange(): void {
  const { scrollTop } = this.scrollPosition;
  const { containerHeight, bufferCount } = this.options;

  // 步骤 1：查找起始索引
  const startIndex = this.heightManager.findStartIndex(scrollTop);

  // 步骤 2：计算结束索引
  let endIndex = startIndex;
  let currentHeight = 0;

  while (endIndex < this.dataSource.length && currentHeight < containerHeight) {
    currentHeight += this.heightManager.getItemHeight(endIndex);
    endIndex++;
  }

  // 步骤 3：添加缓冲区
  const bufferedStart = Math.max(0, startIndex - bufferCount);
  const bufferedEnd = Math.min(this.dataSource.length - 1, endIndex + bufferCount);

  // 步骤 4：计算偏移量
  const offsetY = this.heightManager.getItemOffset(bufferedStart);

  this.visibleRange = {
    startIndex: bufferedStart,
    endIndex: bufferedEnd,
    offsetY
  };
}
```

**时间复杂度**：
- findStartIndex: O(log n)
- 计算 endIndex: O(k)，k 为可视区域项目数
- 总体: O(log n + k)

**空间复杂度**：O(1)

### 2. 二分查找优化

**问题描述**：在累计高度数组中查找目标高度对应的索引。

**标准二分查找**：
```typescript
findStartIndex(scrollTop: number): number {
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
```

**优化变体 - 插值查找**：
```typescript
findStartIndexInterpolation(scrollTop: number): number {
  if (this.totalCount === 0) return 0;

  const totalHeight = this.getTotalHeight();
  if (totalHeight === 0) return 0;

  // 估算初始位置
  let estimate = Math.floor((scrollTop / totalHeight) * this.totalCount);
  estimate = Math.max(0, Math.min(estimate, this.totalCount - 1));

  // 在估算位置附近线性搜索
  const offset = this.getItemOffset(estimate);

  if (offset <= scrollTop) {
    // 向后搜索
    let i = estimate;
    while (i < this.totalCount - 1 && this.getItemOffset(i + 1) <= scrollTop) {
      i++;
    }
    return i;
  } else {
    // 向前搜索
    let i = estimate;
    while (i > 0 && this.getItemOffset(i) > scrollTop) {
      i--;
    }
    return i;
  }
}
```

### 3. 高度缓存管理

**缓存数据结构**：
```typescript
interface CachedItem {
  index: number;
  height: number;
  offsetTop: number;
  timestamp: number; // 用于 LRU 淘汰
}
```

**缓存更新策略**：
```typescript
updateItemHeight(index: number, height: number): void {
  const existing = this.cache.get(index);
  const offsetTop = this.calculateOffsetTop(index);

  this.cache.set(index, {
    index,
    height,
    offsetTop,
    timestamp: Date.now()
  });

  this.dirty = true;

  // 更新后续项目的偏移量
  this.updateSubsequentOffsets(index);

  // 缓存淘汰
  this.evictIfNeeded();
}
```

**LRU 淘汰实现**：
```typescript
private evictIfNeeded(): void {
  const maxCacheSize = 1000;

  if (this.cache.size > maxCacheSize) {
    // 按时间戳排序，淘汰最旧的
    const entries = Array.from(this.cache.entries());
    entries.sort((a, b) => a[1].timestamp - b[1].timestamp);

    const toEvict = entries.slice(0, this.cache.size - maxCacheSize);
    toEvict.forEach(([key]) => this.cache.delete(key));
  }
}
```

### 4. 累计高度数组优化

**问题描述**：频繁计算偏移量导致性能问题。

**解决方案**：预计算累计高度数组。

```typescript
private cumulativeHeights: number[] = [];
private dirty: boolean = true;

rebuildCumulativeHeights(): void {
  if (!this.dirty) return;

  this.cumulativeHeights = new Array(this.totalCount);
  let cumulative = 0;

  for (let i = 0; i < this.totalCount; i++) {
    this.cumulativeHeights[i] = cumulative;
    cumulative += this.getItemHeight(i);
  }

  this.dirty = false;
}

getItemOffset(index: number): number {
  if (this.dirty) {
    this.rebuildCumulativeHeights();
  }

  if (index < this.cumulativeHeights.length) {
    return this.cumulativeHeights[index];
  }

  // 超出数组范围，使用估算
  return this.estimateOffset(index);
}
```

**内存优化**：使用 Float64Array 替代普通数组。

```typescript
private cumulativeHeights: Float64Array = new Float64Array(0);

rebuildCumulativeHeights(): void {
  if (this.cumulativeHeights.length !== this.totalCount) {
    this.cumulativeHeights = new Float64Array(this.totalCount);
  }

  let cumulative = 0;
  for (let i = 0; i < this.totalCount; i++) {
    this.cumulativeHeights[i] = cumulative;
    cumulative += this.getItemHeight(i);
  }

  this.dirty = false;
}
```

## 滚动处理实现

### 1. 节流策略实现

**setTimeout 节流**：
```typescript
private scrollTimer: ReturnType<typeof setTimeout> | null = null;

handleScroll(scrollTop: number): void {
  if (this.scrollTimer) {
    return;
  }

  this.scrollTimer = setTimeout(() => {
    this.scrollPosition.scrollTop = scrollTop;
    this.updateVisibleRange();
    this.events.onScroll?.(this.scrollPosition);
    this.scrollTimer = null;
  }, this.options.throttleInterval);
}
```

**requestAnimationFrame 节流**：
```typescript
private rafId: number | null = null;

handleScroll(scrollTop: number): void {
  if (this.rafId !== null) {
    return;
  }

  this.rafId = requestAnimationFrame(() => {
    this.scrollPosition.scrollTop = scrollTop;
    this.updateVisibleRange();
    this.events.onScroll?.(this.scrollPosition);
    this.rafId = null;
  });
}
```

**双重节流（推荐）**：
```typescript
private rafId: number | null = null;
private lastScrollTop: number = 0;

handleScroll(scrollTop: number): void {
  this.lastScrollTop = scrollTop;

  if (this.rafId !== null) {
    return;
  }

  this.rafId = requestAnimationFrame(() => {
    this.scrollPosition.scrollTop = this.lastScrollTop;
    this.updateVisibleRange();
    this.events.onScroll?.(this.scrollPosition);
    this.rafId = null;
  });
}
```

### 2. 滚动边界处理

**边界检测**：
```typescript
handleScroll(scrollTop: number): void {
  // 限制在有效范围内
  const maxScrollTop = this.heightManager.getTotalHeight() - this.options.containerHeight;
  scrollTop = Math.max(0, Math.min(scrollTop, maxScrollTop));

  // 防止重复触发
  if (scrollTop === this.scrollPosition.scrollTop) {
    return;
  }

  this.scrollPosition.scrollTop = scrollTop;
  this.updateVisibleRange();
}
```

### 3. 滚动到指定位置

**算法实现**：
```typescript
scrollToIndex(index: number, align: 'top' | 'center' | 'bottom' = 'top'): number {
  if (!this.heightManager.isValidIndex(index)) {
    return this.scrollPosition.scrollTop;
  }

  const itemOffset = this.heightManager.getItemOffset(index);
  const itemHeight = this.heightManager.getItemHeight(index);
  const containerHeight = this.options.containerHeight;

  let targetScrollTop: number;

  switch (align) {
    case 'top':
      targetScrollTop = itemOffset;
      break;
    case 'center':
      targetScrollTop = itemOffset - (containerHeight - itemHeight) / 2;
      break;
    case 'bottom':
      targetScrollTop = itemOffset - containerHeight + itemHeight;
      break;
    default:
      targetScrollTop = itemOffset;
  }

  // 确保不超出边界
  const maxScrollTop = this.heightManager.getTotalHeight() - containerHeight;
  return Math.max(0, Math.min(targetScrollTop, maxScrollTop));
}
```

**平滑滚动实现**：
```typescript
async smoothScrollTo(targetScrollTop: number, duration: number = 300): Promise<void> {
  const startScrollTop = this.scrollPosition.scrollTop;
  const distance = targetScrollTop - startScrollTop;
  const startTime = performance.now();

  return new Promise((resolve) => {
    const animate = (currentTime: number) => {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);

      // easeOutCubic 缓动函数
      const eased = 1 - Math.pow(1 - progress, 3);

      const currentScrollTop = startScrollTop + distance * eased;
      this.handleScroll(currentScrollTop);

      if (progress < 1) {
        requestAnimationFrame(animate);
      } else {
        resolve();
      }
    };

    requestAnimationFrame(animate);
  });
}
```

## DOM 渲染实现

### 1. 元素创建

**基础实现**：
```typescript
private createItemElement(item: RenderItem): HTMLElement {
  const element = document.createElement('div');
  element.className = this.options.itemClassName || 'virtual-scroll-item';
  element.style.position = 'absolute';
  element.style.top = `${item.style.top}px`;
  element.style.left = '0';
  element.style.width = '100%';

  if (item.style.height !== 'auto') {
    element.style.height = `${item.style.height}px`;
  }

  // 调用用户提供的渲染函数
  const content = this.options.renderItem(item);
  element.appendChild(content);

  return element;
}
```

**使用 DocumentFragment 批量创建**：
```typescript
private createItemsFragment(items: RenderItem[]): DocumentFragment {
  const fragment = document.createDocumentFragment();

  items.forEach(item => {
    const element = this.createItemElement(item);
    fragment.appendChild(element);
  });

  return fragment;
}
```

### 2. 元素更新

**最小化更新策略**：
```typescript
private updateExistingElement(element: HTMLElement, item: RenderItem): void {
  // 只更新变化的属性
  const currentTop = parseFloat(element.style.top);
  const newTop = item.style.top;

  if (currentTop !== newTop) {
    element.style.top = `${newTop}px`;
  }

  if (item.style.height !== 'auto') {
    const currentHeight = parseFloat(element.style.height);
    const newHeight = item.style.height as number;

    if (currentHeight !== newHeight) {
      element.style.height = `${newHeight}px`;
    }
  }
}
```

### 3. 元素回收

**对象池实现**：
```typescript
class ElementPool {
  private pool: HTMLElement[] = [];
  private factory: () => HTMLElement;

  constructor(factory: () => HTMLElement, initialSize: number = 10) {
    this.factory = factory;

    // 预创建元素
    for (let i = 0; i < initialSize; i++) {
      this.pool.push(factory());
    }
  }

  acquire(): HTMLElement {
    return this.pool.pop() || this.factory();
  }

  release(element: HTMLElement): void {
    // 清理元素状态
    element.textContent = '';
    element.className = '';

    this.pool.push(element);
  }
}
```

### 4. DOM 操作优化

**批量读写**：
```typescript
private renderVisibleItems(): void {
  const renderItems = this.getRenderItems();

  // 批量读取（只读一次）
  const existingElements = new Map<number, HTMLElement>();
  this.renderedElements.forEach((element, index) => {
    existingElements.set(index, element);
  });

  // 批量写入
  const fragment = document.createDocumentFragment();
  const toRemove: HTMLElement[] = [];

  renderItems.forEach(item => {
    const existing = existingElements.get(item.index);

    if (existing) {
      this.updateExistingElement(existing, item);
      existingElements.delete(item.index);
    } else {
      const element = this.createItemElement(item);
      fragment.appendChild(element);
      this.renderedElements.set(item.index, element);
    }
  });

  // 批量添加新元素
  if (fragment.childNodes.length > 0) {
    this.content.appendChild(fragment);
  }

  // 批量移除旧元素
  existingElements.forEach(element => {
    toRemove.push(element);
    this.renderedElements.delete(parseInt(element.dataset.index || '0'));
  });

  toRemove.forEach(element => element.remove());
}
```

**使用 transform 优化**：
```typescript
private updateItemPosition(element: HTMLElement, top: number): void {
  // 使用 transform 替代 top，避免重排
  element.style.transform = `translateY(${top}px)`;
  element.style.top = '0';
}
```

## 动态高度实现

### 1. 高度测量

**使用 ResizeObserver**：
```typescript
class HeightMeasurer {
  private observer: ResizeObserver;
  private callbacks: Map<HTMLElement, (height: number) => void> = new Map();

  constructor() {
    this.observer = new ResizeObserver((entries) => {
      entries.forEach(entry => {
        const callback = this.callbacks.get(entry.target as HTMLElement);
        if (callback) {
          callback(entry.contentRect.height);
        }
      });
    });
  }

  observe(element: HTMLElement, callback: (height: number) => void): void {
    this.callbacks.set(element, callback);
    this.observer.observe(element);
  }

  unobserve(element: HTMLElement): void {
    this.callbacks.delete(element);
    this.observer.unobserve(element);
  }

  disconnect(): void {
    this.observer.disconnect();
    this.callbacks.clear();
  }
}
```

**使用 requestAnimationFrame 测量**：
```typescript
private measureItemHeight(index: number): void {
  const element = this.renderedElements.get(index);
  if (!element) return;

  requestAnimationFrame(() => {
    const height = element.offsetHeight;
    this.heightManager.updateItemHeight(index, height);
  });
}
```

### 2. 高度更新触发

**自动更新流程**：
```
元素渲染完成
    ↓
requestAnimationFrame
    ↓
测量元素高度
    ↓
更新高度管理器
    ↓
标记 dirty
    ↓
下次滚动时重新计算可视范围
```

**代码实现**：
```typescript
private onItemRendered(index: number, element: HTMLElement): void {
  if (!this.options.dynamicHeight) return;

  // 使用 requestAnimationFrame 延迟测量
  requestAnimationFrame(() => {
    // 检查元素是否仍在 DOM 中
    if (!element.parentNode) return;

    const height = element.offsetHeight;
    this.heightManager.updateItemHeight(index, height);

    // 如果高度变化较大，重新计算可视范围
    const currentHeight = this.heightManager.getItemHeight(index);
    if (Math.abs(height - currentHeight) > 10) {
      this.updateVisibleRange();
    }
  });
}
```

### 3. 高度预测

**基于历史数据的预测**：
```typescript
class HeightPredictor {
  private history: Map<number, number[]> = new Map();
  private windowSize: number = 10;

  predict(index: number): number {
    const heights = this.history.get(index);
    if (!heights || heights.length === 0) {
      return this.defaultHeight;
    }

    // 使用移动平均
    const recent = heights.slice(-this.windowSize);
    return recent.reduce((a, b) => a + b, 0) / recent.length;
  }

  update(index: number, height: number): void {
    if (!this.history.has(index)) {
      this.history.set(index, []);
    }

    const heights = this.history.get(index)!;
    heights.push(height);

    // 限制历史记录大小
    if (heights.length > this.windowSize * 2) {
      heights.splice(0, heights.length - this.windowSize);
    }
  }
}
```

## 性能监控实现

### 1. FPS 监控

```typescript
class FPSMonitor {
  private frameCount: number = 0;
  private lastTime: number = 0;
  private fps: number = 60;
  private timer: number | null = null;

  start(): void {
    this.lastTime = performance.now();
    this.frameCount = 0;

    const check = () => {
      this.frameCount++;
      const currentTime = performance.now();
      const elapsed = currentTime - this.lastTime;

      if (elapsed >= 1000) {
        this.fps = Math.round((this.frameCount * 1000) / elapsed);
        this.frameCount = 0;
        this.lastTime = currentTime;
      }

      this.timer = requestAnimationFrame(check);
    };

    this.timer = requestAnimationFrame(check);
  }

  stop(): void {
    if (this.timer !== null) {
      cancelAnimationFrame(this.timer);
      this.timer = null;
    }
  }

  getFPS(): number {
    return this.fps;
  }
}
```

### 2. 渲染时间监控

```typescript
class RenderTimeMonitor {
  private times: number[] = [];
  private maxSize: number = 100;

  record(time: number): void {
    this.times.push(time);

    if (this.times.length > this.maxSize) {
      this.times.shift();
    }
  }

  getAverage(): number {
    if (this.times.length === 0) return 0;
    return this.times.reduce((a, b) => a + b, 0) / this.times.length;
  }

  getP95(): number {
    if (this.times.length === 0) return 0;
    const sorted = [...this.times].sort((a, b) => a - b);
    const index = Math.floor(sorted.length * 0.95);
    return sorted[index];
  }
}
```

### 3. 内存监控

```typescript
class MemoryMonitor {
  getHeapUsed(): number {
    if (typeof process !== 'undefined' && process.memoryUsage) {
      return process.memoryUsage().heapUsed;
    }
    return 0;
  }

  getCacheSize(cache: Map<any, any>): number {
    return cache.size;
  }

  estimateItemSize(item: any): number {
    return JSON.stringify(item).length * 2; // 粗略估算
  }
}
```

## 错误处理实现

### 1. 边界检查

```typescript
private validateIndex(index: number): void {
  if (index < 0 || index >= this.dataSource.length) {
    throw new RangeError(
      `Index ${index} is out of range [0, ${this.dataSource.length - 1}]`
    );
  }
}

private validateOptions(options: Partial<VirtualScrollOptions>): void {
  if (options.containerHeight !== undefined && options.containerHeight <= 0) {
    throw new Error('containerHeight must be positive');
  }

  if (options.itemHeight !== undefined && options.itemHeight <= 0) {
    throw new Error('itemHeight must be positive');
  }

  if (options.bufferCount !== undefined && options.bufferCount < 0) {
    throw new Error('bufferCount must be non-negative');
  }
}
```

### 2. 异常恢复

```typescript
private safeUpdateVisibleRange(): void {
  try {
    this.updateVisibleRange();
  } catch (error) {
    console.error('Error updating visible range:', error);

    // 恢复到安全状态
    this.visibleRange = {
      startIndex: 0,
      endIndex: Math.min(this.dataSource.length - 1, 10),
      offsetY: 0
    };

    this.buildRenderQueue();
  }
}
```

### 3. 资源清理

```typescript
destroy(): void {
  // 清除定时器
  if (this.scrollTimer) {
    clearTimeout(this.scrollTimer);
    this.scrollTimer = null;
  }

  if (this.rafId !== null) {
    cancelAnimationFrame(this.rafId);
    this.rafId = null;
  }

  // 清除缓存
  this.heightManager.clearCache();

  // 清空数据
  this.dataSource = [];
  this.renderQueue = [];

  // 清除 DOM 引用
  this.renderedElements.clear();

  // 触发销毁事件
  this.events.onDestroy?.();

  // 标记为已销毁
  this.destroyed = true;
}
```

## 总结

实现细节的关键点：

1. **算法优化**：使用二分查找、累计高度数组等优化查找性能
2. **缓存管理**：实现 LRU 缓存，控制内存占用
3. **滚动处理**：使用节流和 RAF 优化滚动性能
4. **DOM 操作**：批量读写，最小化重排
5. **动态高度**：延迟测量，高度预测
6. **性能监控**：FPS、渲染时间、内存使用
7. **错误处理**：边界检查，异常恢复，资源清理

这些实现细节确保了虚拟滚动组件在大规模数据场景下的高性能和稳定性。
