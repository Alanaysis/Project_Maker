# 技术设计文档

## 1. 系统架构

### 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                      拖拽系统 (Drag & Drop System)           │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  DragManager │  │  Sortable   │  │  FileUpload │         │
│  │  (拖拽管理)   │  │  (拖拽排序)  │  │  (文件上传)  │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
│         │                │                │                 │
│         └────────────────┼────────────────┘                 │
│                          │                                  │
│                  ┌───────┴───────┐                          │
│                  │   Utils (工具) │                          │
│                  └───────────────┘                          │
│                          │                                  │
│                  ┌───────┴───────┐                          │
│                  │ Types (类型)   │                          │
│                  └───────────────┘                          │
└─────────────────────────────────────────────────────────────┘
```

### 模块职责

| 模块 | 职责 | 依赖 |
|------|------|------|
| DragManager | 管理拖拽状态和事件 | Utils, Types |
| Sortable | 实现拖拽排序功能 | DragManager, Utils, Types |
| FileUpload | 实现文件拖拽上传 | Utils, Types |
| Utils | 提供工具函数 | - |
| Types | 定义类型接口 | - |

## 2. 核心数据结构

### 拖拽状态

```typescript
enum DragState {
  IDLE = 'idle',      // 空闲状态
  PENDING = 'pending', // 等待状态（延迟拖拽）
  DRAGGING = 'dragging' // 拖拽中
}
```

### 拖拽事件数据

```typescript
interface DragEventData {
  element: HTMLElement;   // 拖拽元素
  position: Position;    // 当前位置
  offset: Position;      // 偏移量
  startPosition: Position; // 开始位置
  preview?: HTMLElement;  // 预览元素
  data?: unknown;        // 附加数据
  type: DragEventType;   // 事件类型
}
```

### 排序事件数据

```typescript
interface SortEventData {
  element: HTMLElement;  // 排序元素
  oldIndex: number;     // 旧索引
  newIndex: number;     // 新索引
  container: HTMLElement; // 排序容器
  items: HTMLElement[];  // 排序项列表
}
```

## 3. 事件系统设计

### 事件类型

```typescript
type DragEventType =
  | 'dragstart'   // 拖拽开始
  | 'dragmove'    // 拖拽移动
  | 'dragend'     // 拖拽结束
  | 'dragenter'   // 进入目标区域
  | 'dragleave'   // 离开目标区域
  | 'drop';       // 放下
```

### 事件流程

```
1. mousedown/touchstart
   ↓
2. 检查延迟和距离阈值
   ↓
3. dragstart 事件触发
   ↓
4. 创建拖拽预览
   ↓
5. mousemove/touchmove
   ↓
6. 更新预览位置
   ↓
7. 检查拖放目标
   ↓
8. dragmove 事件触发
   ↓
9. mouseup/touchend
   ↓
10. 检查是否在目标上
    ↓
11. drop 事件触发（如果在目标上）
    ↓
12. dragend 事件触发
    ↓
13. 清理状态
```

## 4. 拖拽排序算法

### 位置计算

```typescript
function calculateIndex(position: Position, items: HTMLElement[]): number {
  for (let i = 0; i < items.length; i++) {
    const rect = getElementRect(items[i]);
    const center = {
      x: rect.x + rect.width / 2,
      y: rect.y + rect.height / 2
    };

    // 根据排序方向判断
    if (direction === 'vertical') {
      if (position.y < center.y) return i;
    } else {
      if (position.x < center.x) return i;
    }
  }
  return items.length - 1;
}
```

### 占位符策略

1. **创建占位符**：拖拽开始时创建与原元素相同尺寸的占位符
2. **插入占位符**：将占位符插入到目标位置
3. **移动占位符**：拖拽过程中根据位置更新占位符
4. **移除占位符**：拖拽结束时移除占位符

### 动画效果

```typescript
// 使用 CSS transition 实现动画
element.style.transition = `transform ${duration}ms ease`;

// 计算移动距离
const dx = newX - oldX;
const dy = newY - oldY;

// 应用变换
element.style.transform = `translate(${dx}px, ${dy}px)`;

// 动画结束后重置
setTimeout(() => {
  element.style.transition = '';
  element.style.transform = '';
}, duration);
```

## 5. 文件上传设计

### 文件验证流程

```
1. 获取拖拽的文件列表
   ↓
2. 检查文件数量限制
   ↓
3. 验证文件类型
   ↓
4. 验证文件大小
   ↓
5. 自定义验证（可选）
   ↓
6. 添加到文件列表
   ↓
7. 创建预览（可选）
   ↓
8. 触发回调
```

### 预览生成

```typescript
async function createFilePreview(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => resolve(e.target.result);
    reader.onerror = () => reject(new Error('Failed to read file'));
    reader.readAsDataURL(file);
  });
}
```

## 6. 性能优化策略

### 节流（Throttle）

```typescript
function throttle(fn: Function, delay: number): Function {
  let lastTime = 0;
  return (...args) => {
    const now = Date.now();
    if (now - lastTime >= delay) {
      lastTime = now;
      fn(...args);
    }
  };
}
```

### 防抖（Debounce）

```typescript
function debounce(fn: Function, delay: number): Function {
  let timer: number;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  };
}
```

### 事件委托

```typescript
// 使用事件委托减少事件监听器数量
container.addEventListener('mousedown', (e) => {
  const target = e.target.closest('[data-draggable]');
  if (target) {
    // 处理拖拽
  }
});
```

### 虚拟滚动

```typescript
// 只渲染可见区域的元素
function getVisibleItems(scrollTop: number, viewportHeight: number): Item[] {
  return items.filter(item => {
    const itemTop = item.index * itemHeight;
    return itemTop + itemHeight > scrollTop && itemTop < scrollTop + viewportHeight;
  });
}
```

## 7. 跨容器拖拽设计

### 分组机制

```typescript
// 使用分组标识支持跨容器拖拽
interface SortableOptions {
  group?: string; // 分组名称
}

// 相同分组的容器之间可以拖拽
const groupContainers = new Map<string, Set<HTMLElement>>();
```

### 跨容器流程

```
1. 拖拽元素从源容器开始
   ↓
2. 检查鼠标位置是否进入其他容器
   ↓
3. 如果进入相同分组的容器
   ↓
4. 计算在目标容器中的位置
   ↓
5. 移动元素到目标容器
   ↓
6. 触发跨容器回调
```

## 8. 接口设计

### DragManager 接口

```typescript
interface IDragManager {
  makeDraggable(element: HTMLElement, options: DragOptions): RemoveEventListener;
  registerDropTarget(element: HTMLElement, options: DropOptions): RemoveEventListener;
  on(event: DragEventType, handler: EventHandler<DragEventData>): RemoveEventListener;
  off(event: DragEventType, handler: EventHandler<DragEventData>): void;
  destroy(): void;
}
```

### Sortable 接口

```typescript
interface ISortable {
  getItems(): HTMLElement[];
  getIndex(element: HTMLElement): number;
  refreshItems(): void;
  disable(): void;
  enable(): void;
  destroy(): void;
}
```

### FileUpload 接口

```typescript
interface IFileUpload {
  getFiles(): File[];
  getFileCount(): number;
  removeFile(file: File): void;
  clearFiles(): void;
  upload(url: string, options?: RequestInit): Promise<UploadResult>;
  destroy(): void;
}
```
