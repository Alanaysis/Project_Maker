# 实现细节文档

## 1. 核心模块实现

### DragManager 实现

#### 初始化

```typescript
class DragManager {
  private state: DragState = DragState.IDLE;
  private currentElement: HTMLElement | null = null;
  private previewElement: HTMLElement | null = null;
  private startPosition: Position = { x: 0, y: 0 };
  private currentPosition: Position = { x: 0, y: 0 };
  private offset: Position = { x: 0, y: 0 };
  private options: DragOptions = {};
  private eventBus = new EventBus<Record<string, DragEventData>>();
  private dropTargets = new Map<HTMLElement, DropOptions>();
  private currentDropTarget: HTMLElement | null = null;

  constructor() {
    // 预绑定事件处理器，避免重复创建
    this.boundHandlers = {
      onMouseMove: this.onMouseMove.bind(this),
      onMouseUp: this.onMouseUp.bind(this),
      onTouchMove: this.onTouchMove.bind(this),
      onTouchEnd: this.onTouchEnd.bind(this),
    };
  }
}
```

#### 使元素可拖拽

```typescript
makeDraggable(element: HTMLElement, options: DragOptions = {}): RemoveEventListener {
  const dragOptions = { ...options };

  // 鼠标按下事件处理器
  const onMouseDown = (e: MouseEvent) => {
    if (e.button !== 0) return; // 只处理左键
    this.startDrag(element, { x: e.clientX, y: e.clientY }, dragOptions);
  };

  // 触摸开始事件处理器
  const onTouchStart = (e: TouchEvent) => {
    if (e.touches.length !== 1) return;
    const touch = e.touches[0];
    this.startDrag(element, { x: touch.clientX, y: touch.clientY }, dragOptions);
  };

  // 检查是否使用拖拽手柄
  if (dragOptions.handle) {
    const handle = element.querySelector(dragOptions.handle) as HTMLElement;
    if (handle) {
      handle.addEventListener('mousedown', onMouseDown);
      handle.addEventListener('touchstart', onTouchStart, { passive: true });

      return () => {
        handle.removeEventListener('mousedown', onMouseDown);
        handle.removeEventListener('touchstart', onTouchStart);
      };
    }
  }

  element.addEventListener('mousedown', onMouseDown);
  element.addEventListener('touchstart', onTouchStart, { passive: true });

  return () => {
    element.removeEventListener('mousedown', onMouseDown);
    element.removeEventListener('touchstart', onTouchStart);
  };
}
```

#### 开始拖拽

```typescript
private startDrag(
  element: HTMLElement,
  position: Position,
  options: DragOptions
): void {
  // 如果正在拖拽，忽略
  if (this.state !== DragState.IDLE) return;

  this.currentElement = element;
  this.options = options;
  this.startPosition = { ...position };
  this.currentPosition = { ...position };
  this.distanceReached = false;

  // 计算偏移量
  const rect = getElementRect(element);
  this.offset = {
    x: position.x - rect.x,
    y: position.y - rect.y,
  };

  // 检查是否需要延迟
  if (options.delay && options.delay > 0) {
    this.state = DragState.PENDING;
    this.delayTimer = setTimeout(() => {
      if (this.state === DragState.PENDING) {
        this.state = DragState.DRAGGING;
        this.initDrag();
      }
    }, options.delay);
  } else {
    this.state = DragState.DRAGGING;
    this.initDrag();
  }

  // 添加全局事件监听
  document.addEventListener('mousemove', this.boundHandlers.onMouseMove);
  document.addEventListener('mouseup', this.boundHandlers.onMouseUp);
  document.addEventListener('touchmove', this.boundHandlers.onTouchMove, {
    passive: false,
  });
  document.addEventListener('touchend', this.boundHandlers.onTouchEnd);
}
```

#### 处理移动

```typescript
private handleMove(position: Position): void {
  this.currentPosition = position;

  // 检查距离阈值
  if (!this.distanceReached && this.options.distance) {
    const distance = getDistance(this.startPosition, position);
    if (distance < this.options.distance) {
      return;
    }
    this.distanceReached = true;
  }

  // 如果还在等待延迟
  if (this.state === DragState.PENDING) {
    if (this.delayTimer) {
      clearTimeout(this.delayTimer);
      this.delayTimer = null;
    }
    this.state = DragState.DRAGGING;
    this.initDrag();
  }

  if (this.state !== DragState.DRAGGING) return;

  // 更新预览位置
  this.updatePreviewPosition();

  // 触发 dragmove 事件
  const eventData = this.createEventData('dragmove');
  this.eventBus.emit('dragmove', eventData);
  this.options.onDragMove?.(eventData);

  // 检查拖放目标
  this.checkDropTargets(position);
}
```

### Sortable 实现

#### 初始化

```typescript
class Sortable {
  private container: HTMLElement;
  private itemSelector: string;
  private dragManager: DragManager;
  private options: SortableOptions;
  private items: HTMLElement[] = [];
  private dragElement: HTMLElement | null = null;
  private placeholder: HTMLElement | null = null;
  private startIndex: number = -1;
  private currentIndex: number = -1;

  constructor(options: SortableOptions) {
    this.container = options.container;
    this.itemSelector = options.itemSelector;
    this.options = options;
    this.dragManager = new DragManager();

    this.init();
  }

  private init(): void {
    // 刷新排序项列表
    this.refreshItems();

    // 注册跨容器排序组
    if (this.options.group) {
      if (!Sortable.groups.has(this.options.group)) {
        Sortable.groups.set(this.options.group, new Set());
      }
      Sortable.groups.get(this.options.group)!.add(this);
    }

    // 为每个排序项设置拖拽
    this.setupItems();
  }
}
```

#### 计算新索引

```typescript
private calculateIndex(position: Position): number {
  const direction = this.options.direction || 'auto';

  for (let i = 0; i < this.items.length; i++) {
    const item = this.items[i];

    // 跳过当前拖拽元素
    if (item === this.dragElement) continue;

    const rect = getElementRect(item);
    const center = getElementCenter(item);

    if (direction === 'vertical' || direction === 'auto') {
      // 垂直排序：检查是否在元素上方
      if (position.y < center.y) {
        return i;
      }
    }

    if (direction === 'horizontal' || direction === 'auto') {
      // 水平排序：检查是否在元素左侧
      if (position.x < center.x) {
        return i;
      }
    }
  }

  // 如果没找到，返回最后位置
  return this.items.length - 1;
}
```

#### 移动占位符

```typescript
private movePlaceholder(newIndex: number): void {
  if (!this.placeholder || !this.dragElement) return;

  const targetItem = this.items[newIndex];
  if (!targetItem || targetItem === this.dragElement) return;

  // 计算移动方向
  if (newIndex > this.currentIndex) {
    // 向后移动
    targetItem.parentNode?.insertBefore(this.placeholder, targetItem.nextSibling);
  } else {
    // 向前移动
    targetItem.parentNode?.insertBefore(this.placeholder, targetItem);
  }

  // 添加动画效果
  if (this.options.animation) {
    this.animateItems();
  }
}
```

### FileUpload 实现

#### 初始化

```typescript
class FileUpload {
  private dropZone: HTMLElement;
  private options: FileUploadOptions;
  private files: File[] = [];
  private previewElements = new Map<File, HTMLElement>();
  private dragEnterCounter: number = 0;

  constructor(options: FileUploadOptions) {
    this.dropZone = options.dropZone;
    this.options = {
      activeClass: 'drag-active',
      multiple: true,
      autoPreview: true,
      ...options,
    };

    this.init();
  }

  private init(): void {
    // 绑定事件处理器
    this.bindEvents();

    // 如果有预览容器，初始化预览区域
    if (this.options.previewContainer) {
      this.initPreviewContainer();
    }
  }
}
```

#### 处理文件

```typescript
private handleFiles(fileList: File[]): void {
  const startTime = Date.now();
  const successFiles: File[] = [];
  const failedFiles: UploadError[] = [];

  for (const file of fileList) {
    // 检查文件数量限制
    if (this.options.maxFiles && this.files.length >= this.options.maxFiles) {
      failedFiles.push({
        file,
        message: `文件数量超过限制 (${this.options.maxFiles})`,
        code: ErrorCode.TOO_MANY_FILES,
      });
      continue;
    }

    // 验证文件
    const validationError = this.validateFile(file);
    if (validationError) {
      failedFiles.push(validationError);
      continue;
    }

    // 添加文件
    this.files.push(file);
    successFiles.push(file);

    // 触发文件添加回调
    this.options.onFileAdd?.(file);

    // 创建文件预览
    if (this.options.autoPreview) {
      this.createPreview(file);
    }
  }

  // 触发完成回调
  if (successFiles.length > 0 || failedFiles.length > 0) {
    const result: UploadResult = {
      success: successFiles,
      failed: failedFiles,
      duration: Date.now() - startTime,
    };

    this.options.onComplete?.(result);
  }
}
```

#### 验证文件

```typescript
private validateFile(file: File): UploadError | null {
  // 自定义验证
  if (this.options.onValidate) {
    const result = this.options.onValidate(file);
    if (result !== true) {
      return {
        file,
        message: typeof result === 'string' ? result : '文件验证失败',
        code: ErrorCode.VALIDATION_FAILED,
      };
    }
  }

  // 验证文件类型
  if (this.options.accept && this.options.accept.length > 0) {
    if (!validateFileType(file, this.options.accept)) {
      return {
        file,
        message: `不支持的文件类型: ${file.type || '未知'}`,
        code: ErrorCode.FILE_TYPE_NOT_ACCEPTED,
      };
    }
  }

  // 验证文件大小
  if (this.options.maxSize) {
    if (!validateFileSize(file, this.options.maxSize)) {
      return {
        file,
        message: `文件大小超过限制: ${formatFileSize(file.size)} > ${formatFileSize(this.options.maxSize)}`,
        code: ErrorCode.FILE_TOO_LARGE,
      };
    }
  }

  return null;
}
```

## 2. 工具函数实现

### 获取元素位置

```typescript
function getElementRect(element: HTMLElement): Rect {
  const rect = element.getBoundingClientRect();
  return {
    x: rect.left + window.scrollX,
    y: rect.top + window.scrollY,
    width: rect.width,
    height: rect.height,
  };
}
```

### 计算距离

```typescript
function getDistance(p1: Position, p2: Position): number {
  const dx = p2.x - p1.x;
  const dy = p2.y - p1.y;
  return Math.sqrt(dx * dx + dy * dy);
}
```

### 节流函数

```typescript
function throttle<T extends (...args: unknown[]) => unknown>(
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
```

### 事件总线

```typescript
class EventBus<T extends Record<string, unknown>> {
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
```

## 3. 关键算法

### 位置计算算法

```typescript
// 计算鼠标在元素上的相对位置
function calculateOffset(
  mousePosition: Position,
  elementRect: Rect
): Position {
  return {
    x: mousePosition.x - elementRect.x,
    y: mousePosition.y - elementRect.y,
  };
}

// 更新预览位置
function updatePreviewPosition(
  preview: HTMLElement,
  mousePosition: Position,
  offset: Position
): void {
  const x = mousePosition.x - offset.x;
  const y = mousePosition.y - offset.y;

  preview.style.left = `${x}px`;
  preview.style.top = `${y}px`;
}
```

### 排序算法

```typescript
// 计算新索引（垂直排序）
function calculateVerticalIndex(
  mouseY: number,
  items: HTMLElement[],
  dragElement: HTMLElement
): number {
  for (let i = 0; i < items.length; i++) {
    const item = items[i];
    if (item === dragElement) continue;

    const rect = item.getBoundingClientRect();
    const centerY = rect.top + rect.height / 2;

    if (mouseY < centerY) {
      return i;
    }
  }
  return items.length - 1;
}

// 计算新索引（水平排序）
function calculateHorizontalIndex(
  mouseX: number,
  items: HTMLElement[],
  dragElement: HTMLElement
): number {
  for (let i = 0; i < items.length; i++) {
    const item = items[i];
    if (item === dragElement) continue;

    const rect = item.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;

    if (mouseX < centerX) {
      return i;
    }
  }
  return items.length - 1;
}
```

### 文件验证算法

```typescript
// 验证文件类型
function validateFileType(file: File, accept: string[]): boolean {
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

// 验证文件大小
function validateFileSize(file: File, maxSize: number): boolean {
  return file.size <= maxSize;
}
```

## 4. 性能优化实现

### 节流优化

```typescript
// 在拖拽移动时使用节流
const throttledHandleMove = throttle((position: Position) => {
  this.handleMove(position);
}, 16); // 约 60fps

// 在事件处理器中使用
private onMouseMove(e: MouseEvent): void {
  throttledHandleMove({ x: e.clientX, y: e.clientY });
}
```

### 批量 DOM 更新

```typescript
// 使用 requestAnimationFrame 批量更新 DOM
private animateItems(): void {
  if (this.animFrameId) {
    cancelAnimationFrame(this.animFrameId);
  }

  this.animFrameId = requestAnimationFrame(() => {
    // 批量更新所有元素的位置
    this.items.forEach((item) => {
      if (item === this.dragElement) return;
      // 更新位置
    });
  });
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

## 5. 错误处理

### 验证错误

```typescript
function validateFile(file: File): UploadError | null {
  // 验证文件类型
  if (!validateFileType(file, accept)) {
    return {
      file,
      message: `不支持的文件类型: ${file.type}`,
      code: ErrorCode.FILE_TYPE_NOT_ACCEPTED,
    };
  }

  // 验证文件大小
  if (!validateFileSize(file, maxSize)) {
    return {
      file,
      message: `文件大小超过限制: ${formatFileSize(file.size)}`,
      code: ErrorCode.FILE_TOO_LARGE,
    };
  }

  return null;
}
```

### 状态错误

```typescript
private startDrag(element: HTMLElement, position: Position, options: DragOptions): void {
  // 如果正在拖拽，忽略
  if (this.state !== DragState.IDLE) {
    console.warn('Drag already in progress');
    return;
  }

  // 开始拖拽
  // ...
}
```

## 6. 测试策略

### 单元测试

```typescript
describe('DragManager', () => {
  it('should start in IDLE state', () => {
    const manager = new DragManager();
    expect(manager.getState()).toBe(DragState.IDLE);
  });

  it('should make element draggable', () => {
    const manager = new DragManager();
    const element = document.createElement('div');
    const remove = manager.makeDraggable(element);
    expect(typeof remove).toBe('function');
  });
});
```

### 集成测试

```typescript
describe('Sortable', () => {
  it('should sort items', () => {
    const container = document.createElement('div');
    // 添加排序项
    const sortable = new Sortable({
      container,
      itemSelector: '.item',
    });

    expect(sortable.getItems().length).toBe(5);
  });
});
```

### 边界测试

```typescript
describe('FileUpload', () => {
  it('should reject files exceeding size limit', () => {
    const uploader = new FileUpload({
      dropZone: document.createElement('div'),
      maxSize: 1024,
    });

    const file = new File([new ArrayBuffer(2048)], 'test');
    // 验证文件被拒绝
  });
});
```
