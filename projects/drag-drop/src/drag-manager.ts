/**
 * 拖拽管理器
 *
 * 拖拽系统的核心模块，负责管理所有拖拽相关的事件和状态
 * 实现了事件驱动的架构，支持多个拖拽源和拖放目标
 */

import {
  DragEventType,
  DragEventData,
  DragState,
  Position,
  DragOptions,
  DropOptions,
  EventHandler,
  RemoveEventListener,
} from './types';
import {
  getElementRect,
  getDistance,
  setStyles,
  addClass,
  removeClass,
  generateId,
  throttle,
  EventBus,
} from './utils';

/**
 * 拖拽管理器
 *
 * 核心职责：
 * 1. 管理拖拽状态
 * 2. 处理鼠标/触摸事件
 * 3. 协调拖拽源和拖放目标
 * 4. 提供事件订阅机制
 */
export class DragManager {
  /** 拖拽状态 */
  private state: DragState = DragState.IDLE;

  /** 当前拖拽元素 */
  private currentElement: HTMLElement | null = null;

  /** 拖拽预览元素 */
  private previewElement: HTMLElement | null = null;

  /** 拖拽开始位置 */
  private startPosition: Position = { x: 0, y: 0 };

  /** 当前鼠标位置 */
  private currentPosition: Position = { x: 0, y: 0 };

  /** 拖拽偏移量 */
  private offset: Position = { x: 0, y: 0 };

  /** 拖拽配置 */
  private options: DragOptions = {};

  /** 事件总线 */
  private eventBus = new EventBus<Record<string, DragEventData>>();

  /** 已注册的拖放目标 */
  private dropTargets = new Map<HTMLElement, DropOptions>();

  /** 当前悬停的拖放目标 */
  private currentDropTarget: HTMLElement | null = null;

  /** 延迟计时器 */
  private delayTimer: ReturnType<typeof setTimeout> | null = null;

  /** 是否已达到距离阈值 */
  private distanceReached: boolean = false;

  /** 事件处理器绑定 */
  private boundHandlers: {
    onMouseMove: (e: MouseEvent) => void;
    onMouseUp: (e: MouseEvent) => void;
    onTouchMove: (e: TouchEvent) => void;
    onTouchEnd: (e: TouchEvent) => void;
  };

  constructor() {
    // 预绑定事件处理器
    this.boundHandlers = {
      onMouseMove: this.onMouseMove.bind(this),
      onMouseUp: this.onMouseUp.bind(this),
      onTouchMove: this.onTouchMove.bind(this),
      onTouchEnd: this.onTouchEnd.bind(this),
    };
  }

  /**
   * 获取当前拖拽状态
   */
  getState(): DragState {
    return this.state;
  }

  /**
   * 获取当前拖拽元素
   */
  getCurrentElement(): HTMLElement | null {
    return this.currentElement;
  }

  /**
   * 获取当前拖拽位置
   */
  getCurrentPosition(): Position {
    return { ...this.currentPosition };
  }

  /**
   * 使元素可拖拽
   *
   * @param element - 要拖拽的元素
   * @param options - 拖拽配置选项
   * @returns 移除拖拽功能的函数
   */
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

  /**
   * 注册拖放目标
   *
   * @param element - 目标元素
   * @param options - 拖放配置选项
   * @returns 移除注册的函数
   */
  registerDropTarget(element: HTMLElement, options: DropOptions = {}): RemoveEventListener {
    this.dropTargets.set(element, options);

    return () => {
      this.dropTargets.delete(element);
    };
  }

  /**
   * 订阅拖拽事件
   *
   * @param event - 事件类型
   * @param handler - 事件处理器
   * @returns 移除订阅的函数
   */
  on(event: DragEventType, handler: EventHandler<DragEventData>): RemoveEventListener {
    return this.eventBus.on(event, handler);
  }

  /**
   * 取消订阅拖拽事件
   */
  off(event: DragEventType, handler: EventHandler<DragEventData>): void {
    this.eventBus.off(event, handler);
  }

  /**
   * 开始拖拽
   */
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

  /**
   * 初始化拖拽
   */
  private initDrag(): void {
    if (!this.currentElement) return;

    // 创建拖拽预览
    if (this.options.enablePreview !== false) {
      this.createPreview();
    }

    // 触发 dragstart 事件
    const eventData = this.createEventData('dragstart');
    this.eventBus.emit('dragstart', eventData);
    this.options.onDragStart?.(eventData);
  }

  /**
   * 创建拖拽预览
   */
  private createPreview(): void {
    if (!this.currentElement) return;

    if (this.options.createPreview) {
      this.previewElement = this.options.createPreview(this.currentElement);
    } else {
      // 默认克隆元素作为预览
      this.previewElement = this.currentElement.cloneNode(
        this.options.previewCloneDeep !== false
      ) as HTMLElement;
    }

    // 设置预览样式
    setStyles(this.previewElement, {
      position: 'fixed',
      zIndex: '10000',
      pointerEvents: 'none',
      opacity: '0.8',
      transform: 'rotate(2deg)',
      transition: 'none',
    });

    document.body.appendChild(this.previewElement);
    this.updatePreviewPosition();
  }

  /**
   * 更新预览位置
   */
  private updatePreviewPosition(): void {
    if (!this.previewElement) return;

    setStyles(this.previewElement, {
      left: `${this.currentPosition.x - this.offset.x}px`,
      top: `${this.currentPosition.y - this.offset.y}px`,
    });
  }

  /**
   * 鼠标移动事件处理器
   */
  private onMouseMove(e: MouseEvent): void {
    this.handleMove({ x: e.clientX, y: e.clientY });
  }

  /**
   * 触摸移动事件处理器
   */
  private onTouchMove(e: TouchEvent): void {
    if (e.touches.length !== 1) return;
    e.preventDefault(); // 防止页面滚动
    const touch = e.touches[0];
    this.handleMove({ x: touch.clientX, y: touch.clientY });
  }

  /**
   * 处理移动
   */
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

  /**
   * 检查拖放目标
   */
  private checkDropTargets(position: Position): void {
    let foundTarget: HTMLElement | null = null;

    this.dropTargets.forEach((options, target) => {
      const rect = getElementRect(target);
      const isInside =
        position.x >= rect.x &&
        position.x <= rect.x + rect.width &&
        position.y >= rect.y &&
        position.y <= rect.y + rect.height;

      if (isInside) {
        // 检查是否接受当前拖拽元素
        if (this.isAccepted(target, options)) {
          foundTarget = target;
        }
      }
    });

    // 处理目标变化
    if (foundTarget !== this.currentDropTarget) {
      // 离开之前的 target
      if (this.currentDropTarget) {
        const prevOptions = this.dropTargets.get(this.currentDropTarget);
        if (prevOptions?.activeClass) {
          removeClass(this.currentDropTarget, prevOptions.activeClass);
        }
        const eventData = this.createEventData('dragleave');
        this.eventBus.emit('dragleave', eventData);
        prevOptions?.onDragLeave?.(eventData);
      }

      // 进入新的 target
      if (foundTarget) {
        const newOptions = this.dropTargets.get(foundTarget);
        if (newOptions?.activeClass) {
          addClass(foundTarget, newOptions.activeClass);
        }
        const eventData = this.createEventData('dragenter');
        this.eventBus.emit('dragenter', eventData);
        newOptions?.onDragEnter?.(eventData);
      }

      this.currentDropTarget = foundTarget;
    }

    // 如果在目标上，触发 dragover
    if (this.currentDropTarget) {
      const options = this.dropTargets.get(this.currentDropTarget);
      const eventData = this.createEventData('dragmove');
      options?.onDragOver?.(eventData);
    }
  }

  /**
   * 检查是否接受拖拽元素
   */
  private isAccepted(target: HTMLElement, options: DropOptions): boolean {
    if (!this.currentElement) return false;

    // 检查选择器
    if (options.acceptSelector) {
      if (!this.currentElement.matches(options.acceptSelector)) {
        return false;
      }
    }

    return true;
  }

  /**
   * 鼠标抬起事件处理器
   */
  private onMouseUp(e: MouseEvent): void {
    this.endDrag({ x: e.clientX, y: e.clientY });
  }

  /**
   * 触摸结束事件处理器
   */
  private onTouchEnd(e: TouchEvent): void {
    this.endDrag(this.currentPosition);
  }

  /**
   * 结束拖拽
   */
  private endDrag(position: Position): void {
    // 清除延迟计时器
    if (this.delayTimer) {
      clearTimeout(this.delayTimer);
      this.delayTimer = null;
    }

    // 如果正在拖拽
    if (this.state === DragState.DRAGGING) {
      // 检查是否在拖放目标上
      if (this.currentDropTarget) {
        const options = this.dropTargets.get(this.currentDropTarget);
        if (options?.activeClass) {
          removeClass(this.currentDropTarget, options.activeClass);
        }

        // 触发 drop 事件
        const eventData = this.createEventData('drop');
        this.eventBus.emit('drop', eventData);
        options?.onDrop?.(eventData);
      }

      // 触发 dragend 事件
      const eventData = this.createEventData('dragend');
      this.eventBus.emit('dragend', eventData);
      this.options.onDragEnd?.(eventData);
    }

    // 清理
    this.cleanup();
  }

  /**
   * 清理拖拽状态
   */
  private cleanup(): void {
    // 移除预览元素
    if (this.previewElement) {
      this.previewElement.remove();
      this.previewElement = null;
    }

    // 重置状态
    this.state = DragState.IDLE;
    this.currentElement = null;
    this.currentDropTarget = null;
    this.options = {};
    this.distanceReached = false;

    // 移除全局事件监听
    document.removeEventListener('mousemove', this.boundHandlers.onMouseMove);
    document.removeEventListener('mouseup', this.boundHandlers.onMouseUp);
    document.removeEventListener('touchmove', this.boundHandlers.onTouchMove);
    document.removeEventListener('touchend', this.boundHandlers.onTouchEnd);
  }

  /**
   * 创建事件数据
   */
  private createEventData(type: DragEventType): DragEventData {
    return {
      element: this.currentElement!,
      position: { ...this.currentPosition },
      offset: { ...this.offset },
      startPosition: { ...this.startPosition },
      preview: this.previewElement || undefined,
      data: this.options.data,
      type,
    };
  }

  /**
   * 销毁管理器
   */
  destroy(): void {
    this.cleanup();
    this.eventBus.clear();
    this.dropTargets.clear();
  }
}
