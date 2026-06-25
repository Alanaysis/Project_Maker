/**
 * 拖拽排序模块
 *
 * 实现拖拽排序功能，支持：
 * - 垂直/水平排序
 * - 跨容器排序
 * - 动画效果
 * - 拖拽占位符
 */

import {
  SortableOptions,
  SortEventData,
  GroupSortEventData,
  DragEventData,
  DragState,
  Position,
  RemoveEventListener,
} from './types';
import {
  getElementRect,
  getElementCenter,
  getOverlapArea,
  setStyles,
  addClass,
  removeClass,
  generateId,
  throttle,
} from './utils';
import { DragManager } from './drag-manager';

/**
 * 拖拽排序器
 *
 * 使用示例：
 * ```typescript
 * const sortable = new Sortable({
 *   container: document.getElementById('list')!,
 *   itemSelector: '.item',
 *   animation: 150,
 *   onSortEnd: (data) => {
 *     console.log('排序完成', data.oldIndex, data.newIndex);
 *   },
 * });
 * ```
 */
export class Sortable {
  /** 排序容器 */
  private container: HTMLElement;

  /** 排序项选择器 */
  private itemSelector: string;

  /** 拖拽管理器 */
  private dragManager: DragManager;

  /** 配置选项 */
  private options: SortableOptions;

  /** 排序项列表 */
  private items: HTMLElement[] = [];

  /** 当前拖拽元素 */
  private dragElement: HTMLElement | null = null;

  /** 占位符元素 */
  private placeholder: HTMLElement | null = null;

  /** 拖拽开始时的索引 */
  private startIndex: number = -1;

  /** 当前索引 */
  private currentIndex: number = -1;

  /** 移除事件监听的函数数组 */
  private removeListeners: RemoveEventListener[] = [];

  /** 动画帧 ID */
  private animFrameId: number | null = null;

  /** 跨容器排序组 */
  private static groups = new Map<string, Set<Sortable>>();

  constructor(options: SortableOptions) {
    this.container = options.container;
    this.itemSelector = options.itemSelector;
    this.options = options;
    this.dragManager = new DragManager();

    this.init();
  }

  /**
   * 初始化排序器
   */
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

  /**
   * 刷新排序项列表
   */
  refreshItems(): void {
    this.items = Array.from(
      this.container.querySelectorAll(this.itemSelector)
    ) as HTMLElement[];
  }

  /**
   * 设置排序项拖拽
   */
  private setupItems(): void {
    // 移除之前的事件监听
    this.removeListeners.forEach((remove) => remove());
    this.removeListeners = [];

    this.items.forEach((item, index) => {
      // 检查是否禁用
      if (this.isDisabled(item)) return;

      const remove = this.dragManager.makeDraggable(item, {
        handle: this.options.handle,
        enablePreview: true,
        delay: this.options.delay,
        distance: this.options.distance,
        onDragStart: (e) => this.onDragStart(e, index),
        onDragMove: (e) => this.onDragMove(e),
        onDragEnd: (e) => this.onDragEnd(e),
      });

      this.removeListeners.push(remove);
    });
  }

  /**
   * 检查排序项是否禁用
   */
  private isDisabled(item: HTMLElement): boolean {
    if (this.options.disabled) return true;
    if (this.options.disabledSelector) {
      return item.matches(this.options.disabledSelector);
    }
    return false;
  }

  /**
   * 拖拽开始事件处理器
   */
  private onDragStart(event: DragEventData, index: number): void {
    if (this.options.disabled) return;

    this.dragElement = event.element;
    this.startIndex = index;
    this.currentIndex = index;

    // 创建占位符
    this.createPlaceholder();

    // 设置拖拽元素样式
    addClass(this.dragElement, 'sortable-drag');
    setStyles(this.dragElement, {
      zIndex: '10000',
    });

    // 隐藏原始元素（使用预览代替）
    setStyles(this.dragElement, {
      opacity: '0',
    });
  }

  /**
   * 创建占位符
   */
  private createPlaceholder(): void {
    if (!this.dragElement) return;

    if (this.options.placeholder) {
      this.placeholder = this.options.placeholder;
    } else {
      this.placeholder = document.createElement('div');
      const rect = getElementRect(this.dragElement);
      setStyles(this.placeholder, {
        width: `${rect.width}px`,
        height: `${rect.height}px`,
        boxSizing: 'border-box',
      });
    }

    if (this.options.placeholderClass) {
      addClass(this.placeholder, this.options.placeholderClass);
    } else {
      addClass(this.placeholder, 'sortable-placeholder');
      setStyles(this.placeholder, {
        backgroundColor: 'rgba(0, 120, 215, 0.1)',
        border: '2px dashed rgba(0, 120, 215, 0.4)',
        borderRadius: '4px',
      });
    }

    // 插入占位符到拖拽元素位置
    this.dragElement.parentNode?.insertBefore(this.placeholder, this.dragElement);
  }

  /**
   * 拖拽移动事件处理器
   */
  private onDragMove(event: DragEventData): void {
    if (!this.dragElement || !this.placeholder) return;

    // 计算当前位置
    const newIndex = this.calculateIndex(event.position);

    if (newIndex !== this.currentIndex && newIndex >= 0) {
      // 移动占位符
      this.movePlaceholder(newIndex);
      this.currentIndex = newIndex;

      // 触发排序变化回调
      const sortData: SortEventData = {
        element: this.dragElement,
        oldIndex: this.startIndex,
        newIndex: this.currentIndex,
        container: this.container,
        items: this.items,
      };
      this.options.onSortChange?.(sortData);
    }

    // 检查跨容器排序
    if (this.options.group) {
      this.checkGroupDrop(event);
    }
  }

  /**
   * 计算新索引
   */
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

  /**
   * 移动占位符
   */
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

  /**
   * 动画效果
   */
  private animateItems(): void {
    if (this.animFrameId) {
      cancelAnimationFrame(this.animFrameId);
    }

    this.animFrameId = requestAnimationFrame(() => {
      this.items.forEach((item) => {
        if (item === this.dragElement) return;

        const rect = getElementRect(item);
        setStyles(item, {
          transition: `transform ${this.options.animation}ms ease`,
        });

        // 重置动画
        setTimeout(() => {
          setStyles(item, {
            transition: '',
          });
        }, this.options.animation);
      });
    });
  }

  /**
   * 检查跨容器排序
   */
  private checkGroupDrop(event: DragEventData): void {
    if (!this.options.group || !this.dragElement) return;

    const group = Sortable.groups.get(this.options.group);
    if (!group) return;

    group.forEach((other) => {
      if (other === this) return;

      const otherRect = getElementRect(other.container);
      const isInside =
        event.position.x >= otherRect.x &&
        event.position.x <= otherRect.x + otherRect.width &&
        event.position.y >= otherRect.y &&
        event.position.y <= otherRect.y + otherRect.height;

      if (isInside) {
        // 移动元素到另一个容器
        this.moveToContainer(other, event.position);
      }
    });
  }

  /**
   * 移动元素到另一个容器
   */
  private moveToContainer(target: Sortable, position: Position): void {
    if (!this.dragElement || !this.placeholder) return;

    // 计算目标位置
    const targetIndex = target.calculateIndex(position);

    // 移动元素
    target.container.insertBefore(this.dragElement, target.items[targetIndex] || null);

    // 更新列表
    this.refreshItems();
    target.refreshItems();

    // 触发跨容器排序回调
    const groupData: GroupSortEventData = {
      element: this.dragElement,
      oldIndex: this.startIndex,
      newIndex: targetIndex,
      container: target.container,
      items: target.items,
      fromContainer: this.container,
      toContainer: target.container,
    };

    this.options.onGroupChange?.(groupData);
    target.options.onGroupChange?.(groupData);
  }

  /**
   * 拖拽结束事件处理器
   */
  private onDragEnd(event: DragEventData): void {
    if (!this.dragElement) return;

    // 移除占位符
    if (this.placeholder) {
      this.placeholder.remove();
      this.placeholder = null;
    }

    // 恢复拖拽元素样式
    removeClass(this.dragElement, 'sortable-drag');
    setStyles(this.dragElement, {
      zIndex: '',
      opacity: '',
    });

    // 如果位置发生变化，触发动画
    if (this.startIndex !== this.currentIndex && this.options.animation) {
      const rect = getElementRect(this.dragElement);
      setStyles(this.dragElement, {
        transition: `transform ${this.options.animation}ms ease`,
      });

      setTimeout(() => {
        setStyles(this.dragElement!, {
          transition: '',
        });
      }, this.options.animation);
    }

    // 触发排序结束回调
    if (this.startIndex !== this.currentIndex) {
      const sortData: SortEventData = {
        element: this.dragElement,
        oldIndex: this.startIndex,
        newIndex: this.currentIndex,
        container: this.container,
        items: this.items,
      };
      this.options.onSortEnd?.(sortData);
    }

    // 重置状态
    this.dragElement = null;
    this.startIndex = -1;
    this.currentIndex = -1;
  }

  /**
   * 获取当前排序项索引
   */
  getIndex(element: HTMLElement): number {
    return this.items.indexOf(element);
  }

  /**
   * 获取排序项列表
   */
  getItems(): HTMLElement[] {
    return [...this.items];
  }

  /**
   * 禁用排序
   */
  disable(): void {
    this.options.disabled = true;
  }

  /**
   * 启用排序
   */
  enable(): void {
    this.options.disabled = false;
  }

  /**
   * 销毁排序器
   */
  destroy(): void {
    // 移除事件监听
    this.removeListeners.forEach((remove) => remove());
    this.removeListeners = [];

    // 移除占位符
    if (this.placeholder) {
      this.placeholder.remove();
    }

    // 从组中移除
    if (this.options.group) {
      const group = Sortable.groups.get(this.options.group);
      group?.delete(this);
      if (group?.size === 0) {
        Sortable.groups.delete(this.options.group);
      }
    }

    // 销毁拖拽管理器
    this.dragManager.destroy();
  }
}
