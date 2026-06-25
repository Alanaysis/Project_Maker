# 02 - 架构设计

## 系统架构概览

```
┌─────────────────────────────────────────────────────────────────┐
│                      Virtual Scroll 系统                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   虚拟滚动    │    │   高度管理    │    │   DOM 适配    │      │
│  │    核心      │◄──►│     器       │◄──►│     器        │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│         │                   │                   │               │
│         ▼                   ▼                   ▼               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │  可视范围    │    │   高度缓存    │    │   DOM 操作    │      │
│  │    计算      │    │    管理      │    │    渲染       │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 核心模块设计

### 1. VirtualScroll 核心类

**职责**：
- 管理虚拟滚动状态
- 计算可视范围
- 处理滚动事件
- 生成渲染队列

**类图**：
```
┌─────────────────────────────────────┐
│           VirtualScroll             │
├─────────────────────────────────────┤
│ - options: VirtualScrollOptions     │
│ - events: VirtualScrollEvents       │
│ - heightManager: HeightManager      │
│ - dataSource: ItemConfig[]          │
│ - scrollPosition: ScrollPosition    │
│ - visibleRange: VisibleRange        │
│ - renderQueue: RenderItem[]         │
├─────────────────────────────────────┤
│ + setDataSource(items)              │
│ + handleScroll(scrollTop)           │
│ + scrollToIndex(index, align)       │
│ + getRenderItems(): RenderItem[]    │
│ + getVisibleRange(): VisibleRange   │
│ + updateItemHeight(index, height)   │
│ + destroy()                         │
└─────────────────────────────────────┘
```

**状态管理**：
```typescript
interface State {
  // 数据状态
  dataSource: ItemConfig[];
  totalCount: number;

  // 滚动状态
  scrollTop: number;
  scrollLeft: number;

  // 渲染状态
  visibleRange: VisibleRange;
  renderQueue: RenderItem[];

  // 性能状态
  metrics: PerformanceMetrics;
}
```

### 2. HeightManager 高度管理器

**职责**：
- 管理项目高度缓存
- 计算项目偏移量
- 查找起始索引
- 优化高度计算

**数据结构**：
```
┌─────────────────────────────────────────────────────────┐
│                    高度缓存结构                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  index  │  height  │  offsetTop  │  cached             │
│─────────┼──────────┼─────────────┼─────────────        │
│    0    │    50    │      0      │    true             │
│    1    │    60    │     50      │    true             │
│    2    │    55    │    110      │    false (估算)     │
│    3    │    70    │    165      │    true             │
│   ...   │   ...    │    ...      │    ...              │
│   N-1   │    50    │   50000     │    true             │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**算法设计**：

1. **二分查找优化**
```typescript
// 查找起始索引的时间复杂度：O(log n)
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

2. **累计高度数组**
```typescript
// 预计算累计高度，避免重复计算
rebuildCumulativeHeights(): void {
  this.cumulativeHeights = new Array(this.totalCount);
  let cumulative = 0;

  for (let i = 0; i < this.totalCount; i++) {
    this.cumulativeHeights[i] = cumulative;
    cumulative += this.getItemHeight(i);
  }

  this.dirty = false;
}
```

3. **高度估算策略**
```typescript
// 使用最近缓存项进行估算
estimateOffset(index: number): number {
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
```

### 3. DOMAdapter DOM 适配器

**职责**：
- 管理 DOM 结构
- 处理浏览器事件
- 渲染可视区域
- 测量元素高度

**DOM 结构**：
```html
<div class="virtual-scroll-container">
  <!-- 视口：负责滚动 -->
  <div class="virtual-scroll-viewport" style="overflow-y: auto; height: 500px;">
    <!-- 内容：设置总高度 -->
    <div class="virtual-scroll-content" style="position: relative; height: 50000px;">
      <!-- 可见项：绝对定位 -->
      <div class="virtual-scroll-item" style="position: absolute; top: 0px; height: 50px;">
        Item 1
      </div>
      <div class="virtual-scroll-item" style="position: absolute; top: 50px; height: 50px;">
        Item 2
      </div>
      <!-- ... -->
    </div>
  </div>
</div>
```

**渲染流程**：
```
滚动事件
    ↓
requestAnimationFrame
    ↓
计算可视范围
    ↓
比对已有元素
    ↓
┌─────────────────────────────────────┐
│  创建新元素  │  更新位置  │  删除旧元素  │
└─────────────────────────────────────┘
    ↓
更新总高度
    ↓
完成渲染
```

## 数据流设计

### 1. 初始化流程

```
用户代码
    ↓
new VirtualScroll(options, events)
    ↓
初始化 HeightManager
    ↓
setDataSource(items)
    ↓
设置总数
    ↓
计算初始可视范围
    ↓
生成渲染队列
    ↓
触发 onVisibleChange 回调
    ↓
完成初始化
```

### 2. 滚动处理流程

```
浏览器滚动事件
    ↓
DOMAdapter.handleScroll()
    ↓
VirtualScroll.handleScroll()
    ↓
节流处理（16ms）
    ↓
更新 scrollPosition
    ↓
调用 updateVisibleRange()
    ↓
┌─────────────────────────────────────┐
│  HeightManager.findStartIndex()    │
│         ↓                          │
│  计算 endIndex                     │
│         ↓                          │
│  添加缓冲区                        │
│         ↓                          │
│  计算 offsetY                      │
└─────────────────────────────────────┘
    ↓
生成渲染队列
    ↓
触发 onVisibleChange 回调
    ↓
DOMAdapter.renderVisibleItems()
    ↓
更新 DOM
```

### 3. 动态高度更新流程

```
元素渲染完成
    ↓
requestAnimationFrame
    ↓
测量元素高度
    ↓
updateItemHeight(index, height)
    ↓
HeightManager.updateItemHeight()
    ↓
更新缓存
    ↓
更新后续偏移量
    ↓
标记 dirty
    ↓
下次滚动时重新计算
```

## 性能优化设计

### 1. 节流策略

**方案对比**：

| 方案 | 延迟 | 平滑度 | 实现复杂度 |
|------|------|--------|------------|
| setTimeout | 可配置 | 一般 | 简单 |
| requestAnimationFrame | 16ms | 优秀 | 简单 |
| 双重节流 | 可配置 | 优秀 | 复杂 |

**推荐方案**：requestAnimationFrame + 超时保护

```typescript
handleScroll(scrollTop: number): void {
  if (this.scrollTimer) return;

  this.scrollTimer = requestAnimationFrame(() => {
    this.updateVisibleRange();
    this.scrollTimer = null;
  }) as any;
}
```

### 2. 缓存策略

**LRU 缓存**：
```typescript
class LRUCache<K, V> {
  private cache = new Map<K, V>();
  private maxSize: number;

  constructor(maxSize: number) {
    this.maxSize = maxSize;
  }

  get(key: K): V | undefined {
    const value = this.cache.get(key);
    if (value !== undefined) {
      // 移动到最新
      this.cache.delete(key);
      this.cache.set(key, value);
    }
    return value;
  }

  set(key: K, value: V): void {
    if (this.cache.has(key)) {
      this.cache.delete(key);
    } else if (this.cache.size >= this.maxSize) {
      // 删除最旧的
      const firstKey = this.cache.keys().next().value;
      this.cache.delete(firstKey);
    }
    this.cache.set(key, value);
  }
}
```

**缓存淘汰策略**：
- 缓存大小限制：1000 个项目
- 淘汰算法：LRU（最近最少使用）
- 预热策略：可视区域 + 缓冲区

### 3. DOM 操作优化

**批量更新**：
```typescript
// 使用 DocumentFragment 批量插入
const fragment = document.createDocumentFragment();
items.forEach(item => {
  fragment.appendChild(createElement(item));
});
container.appendChild(fragment);
```

**最小化重排**：
```typescript
// 使用 transform 替代 top/left
element.style.transform = `translateY(${offset}px)`;

// 批量读取，批量写入
const heights = items.map(item => item.offsetHeight);
items.forEach((item, i) => {
  item.style.height = `${heights[i]}px`;
});
```

### 4. 内存优化

**对象池**：
```typescript
class ObjectPool<T> {
  private pool: T[] = [];
  private factory: () => T;

  constructor(factory: () => T, initialSize: number = 10) {
    this.factory = factory;
    for (let i = 0; i < initialSize; i++) {
      this.pool.push(factory());
    }
  }

  acquire(): T {
    return this.pool.pop() || this.factory();
  }

  release(obj: T): void {
    this.pool.push(obj);
  }
}
```

## 接口设计

### 1. 配置接口

```typescript
interface VirtualScrollOptions {
  /** 容器高度（像素） */
  containerHeight: number;

  /** 项目高度（固定高度模式） */
  itemHeight?: number;

  /** 缓冲区项目数量 */
  bufferCount?: number;

  /** 是否使用动态高度 */
  dynamicHeight?: boolean;

  /** 预估高度（动态高度模式） */
  estimatedHeight?: number;

  /** 滚动节流间隔（毫秒） */
  throttleInterval?: number;

  /** 是否启用平滑滚动 */
  smoothScroll?: boolean;
}
```

### 2. 事件接口

```typescript
interface VirtualScrollEvents {
  /** 滚动事件 */
  onScroll?: (position: ScrollPosition) => void;

  /** 可视范围变化 */
  onVisibleChange?: (range: VisibleRange) => void;

  /** 项目渲染 */
  onItemRender?: (index: number, item: ItemConfig) => void;

  /** 项目销毁 */
  onItemDestroy?: (index: number) => void;
}
```

### 3. 数据接口

```typescript
interface ItemConfig {
  /** 唯一标识符 */
  id: string | number;

  /** 高度（可选） */
  height?: number;

  /** 数据 */
  data: any;
}

interface RenderItem {
  /** 项目索引 */
  index: number;

  /** 项目数据 */
  data: any;

  /** 样式 */
  style: {
    position: 'absolute';
    top: number;
    left: number;
    width: string;
    height: number | 'auto';
  };
}
```

## 扩展性设计

### 1. 插件机制

```typescript
interface VirtualScrollPlugin {
  name: string;
  install(scroll: VirtualScroll): void;
  destroy(): void;
}

// 使用示例
class LazyLoadPlugin implements VirtualScrollPlugin {
  name = 'lazyLoad';

  install(scroll: VirtualScroll) {
    scroll.on('visibleChange', (range) => {
      this.loadImages(range);
    });
  }

  private loadImages(range: VisibleRange) {
    // 实现图片懒加载
  }

  destroy() {
    // 清理
  }
}
```

### 2. 自定义渲染器

```typescript
interface ItemRenderer {
  createElement(item: RenderItem): HTMLElement;
  updateElement(element: HTMLElement, item: RenderItem): void;
  destroyElement(element: HTMLElement): void;
}

// 使用示例
class CustomRenderer implements ItemRenderer {
  createElement(item: RenderItem): HTMLElement {
    const div = document.createElement('div');
    div.className = 'custom-item';
    div.innerHTML = `<span>${item.data.title}</span>`;
    return div;
  }

  updateElement(element: HTMLElement, item: RenderItem): void {
    element.querySelector('span')!.textContent = item.data.title;
  }

  destroyElement(element: HTMLElement): void {
    element.remove();
  }
}
```

### 3. 布局策略

```typescript
interface LayoutStrategy {
  calculateTotalHeight(items: ItemConfig[]): number;
  calculateItemOffset(items: ItemConfig[], index: number): number;
  findStartIndex(items: ItemConfig[], scrollTop: number): number;
}

// 固定高度布局
class FixedHeightLayout implements LayoutStrategy {
  constructor(private itemHeight: number) {}

  calculateTotalHeight(items: ItemConfig[]): number {
    return items.length * this.itemHeight;
  }

  calculateItemOffset(items: ItemConfig[], index: number): number {
    return index * this.itemHeight;
  }

  findStartIndex(items: ItemConfig[], scrollTop: number): number {
    return Math.floor(scrollTop / this.itemHeight);
  }
}

// 动态高度布局
class DynamicHeightLayout implements LayoutStrategy {
  private heightManager: HeightManager;

  constructor(estimatedHeight: number) {
    this.heightManager = new HeightManager(estimatedHeight);
  }

  // ... 实现
}
```

## 错误处理设计

### 1. 边界检查

```typescript
validateIndex(index: number): void {
  if (index < 0 || index >= this.totalCount) {
    throw new Error(`Index out of range: ${index}`);
  }
}

validateOptions(options: VirtualScrollOptions): void {
  if (options.containerHeight <= 0) {
    throw new Error('containerHeight must be positive');
  }
  if (options.itemHeight !== undefined && options.itemHeight <= 0) {
    throw new Error('itemHeight must be positive');
  }
}
```

### 2. 异常恢复

```typescript
try {
  this.updateVisibleRange();
} catch (error) {
  console.error('Error updating visible range:', error);
  // 恢复到安全状态
  this.visibleRange = {
    startIndex: 0,
    endIndex: Math.min(this.totalCount - 1, 10),
    offsetY: 0
  };
}
```

### 3. 资源清理

```typescript
destroy(): void {
  // 清除定时器
  if (this.scrollTimer) {
    cancelAnimationFrame(this.scrollTimer);
    this.scrollTimer = null;
  }

  // 清除缓存
  this.heightManager.clearCache();

  // 清空数据
  this.dataSource = [];
  this.renderQueue = [];

  // 触发销毁事件
  this.events.onDestroy?.();
}
```

## 测试策略

### 1. 单元测试

**测试覆盖**：
- HeightManager：高度计算、缓存管理、索引查找
- VirtualScroll：滚动处理、可视范围计算、数据操作
- DOMAdapter：DOM 渲染、事件处理、样式更新

**测试工具**：
- Jest：测试框架
- jsdom：DOM 环境模拟

### 2. 性能测试

**测试指标**：
- 滚动 FPS
- 渲染时间
- 内存占用
- 缓存命中率

**测试场景**：
- 10 万项列表
- 100 万项列表
- 快速滚动
- 动态高度

### 3. 集成测试

**测试场景**：
- 浏览器兼容性
- 移动端触摸滚动
- 键盘导航
- 无障碍访问

## 总结

本架构设计遵循以下原则：

1. **单一职责**：每个模块只负责一个功能
2. **开闭原则**：易于扩展，无需修改核心代码
3. **依赖倒置**：高层模块不依赖低层模块
4. **接口隔离**：提供细粒度的接口

通过合理的架构设计，我们实现了一个高性能、易扩展、易维护的虚拟滚动组件。
