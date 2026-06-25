/**
 * Watcher - 观察者
 *
 * 负责订阅数据变化并执行回调。
 * 是连接"数据"和"副作用"的桥梁。
 *
 * 使用场景：
 * - watch() API 创建的观察者
 * - computed 属性内部的求值观察者
 * - 组件渲染的 effect 观察者
 */

import { Dep, pushTarget, popTarget } from './dep';

export type WatcherCallback = (newValue: any, oldValue: any) => void;

export interface WatcherOptions {
  /** 是否立即用当前值执行一次回调 */
  immediate?: boolean;
  /** 是否为同步更新（默认异步微任务） */
  sync?: boolean;
  /** 是否为 computed watcher（惰性求值） */
  lazy?: boolean;
  /** computed watcher 专用：依赖变化时的回调（通知 computed 的 Dep） */
  computedCallback?: () => void;
}

export class Watcher {
  /** 依赖集合（用于去重和清理） */
  private deps: Set<Dep> = new Set();
  /** 上一次的依赖集合（用于清理不再需要的依赖） */
  private depIds: Set<Dep> = new Set();

  /** 求值函数 */
  private getter: () => any;
  /** 回调函数 */
  private callback: WatcherCallback | null;
  /** 当前值 */
  value: any;
  /** 上一次的值 */
  private oldValue: any;
  /** 是否为惰性求值 */
  private lazy: boolean;
  /** 是否为脏数据（computed 用，标记需要重新求值） */
  dirty: boolean = false;
  /** 是否同步执行 */
  private sync: boolean;
  /** 是否活跃 */
  active: boolean = true;
  /** computed watcher 专用：依赖变化时的回调 */
  private computedCallback: (() => void) | null;

  constructor(
    getter: () => any,
    callback: WatcherCallback | null = null,
    options: WatcherOptions = {}
  ) {
    this.getter = getter;
    this.callback = callback;
    this.lazy = options.lazy || false;
    this.sync = options.sync || false;
    this.computedCallback = options.computedCallback || null;

    if (this.lazy) {
      // computed watcher: 惰性求值，初始不执行
      this.value = undefined;
      this.dirty = true;
    } else {
      // 立即求值，触发依赖收集
      this.value = this.get();
    }

    // immediate 选项：立即用当前值执行回调
    if (options.immediate && this.callback) {
      this.callback(this.value, undefined);
    }
  }

  /**
   * 求值并收集依赖
   * 1. 将自己设为全局活跃 Watcher
   * 2. 执行求值函数（过程中会触发属性的 getter，从而收集依赖）
   * 3. 清理旧依赖
   * 4. 弹出自己
   */
  get(): any {
    pushTarget(this);
    try {
      const value = this.getter();
      this.cleanupDeps();
      return value;
    } finally {
      popTarget();
    }
  }

  /**
   * 添加依赖
   * 由 Dep.depend() 调用
   */
  addDep(dep: Dep): void {
    // 去重：同一个 Dep 只收集一次
    if (!this.depIds.has(dep)) {
      this.depIds.add(dep);
      this.deps.add(dep);
      dep.depend();
    }
  }

  /**
   * 清理不再需要的依赖
   * 在每次求值后调用，移除本次求值未触发的旧依赖
   */
  private cleanupDeps(): void {
    // 实际上在简化实现中，我们依赖 Set 自动去重
    // 完整实现会对比新旧依赖集合进行清理
  }

  /**
   * 依赖变更时调用
   * 根据配置决定同步或异步更新
   */
  update(): void {
    if (this.lazy) {
      // computed watcher: 标记为脏，并通知 computed 的订阅者
      this.dirty = true;
      if (this.computedCallback) {
        this.computedCallback();
      }
    } else if (this.sync) {
      // 同步模式：立即执行
      this.run();
    } else {
      // 异步模式：放入微任务队列（简化实现用 setTimeout 模拟）
      queueWatcher(this);
    }
  }

  /**
   * 执行更新
   * 重新求值并调用回调
   */
  run(): void {
    if (!this.active) return;

    const oldValue = this.value;
    const newValue = this.get();

    // 值确实变化了才触发回调
    if (newValue !== oldValue || typeof newValue === 'object') {
      this.value = newValue;
      this.oldValue = oldValue;
      if (this.callback) {
        this.callback(newValue, oldValue);
      }
    }
  }

  /**
   * computed watcher: 求值
   * 仅在脏数据时重新求值
   */
  evaluate(): any {
    this.value = this.get();
    this.dirty = false;
    return this.value;
  }

  /**
   * 让所有收集到的依赖也收集当前活跃的 Watcher
   * 用于 computed 属性：当 computed 被其他 Watcher 依赖时，
   * computed 自身的依赖也需要被那个 Watcher 收集
   */
  depend(): void {
    for (const dep of this.deps) {
      dep.depend();
    }
  }

  /**
   * 销毁 Watcher
   */
  teardown(): void {
    this.active = false;
    for (const dep of this.deps) {
      dep.removeSub(this);
    }
    this.deps.clear();
    this.depIds.clear();
  }
}

/**
 * Watcher 队列管理（异步更新）
 * 将多个同步数据变更合并为一次更新
 */
const queue: Watcher[] = [];
let waiting = false;
const has: Set<Watcher> = new Set();

function queueWatcher(watcher: Watcher): void {
  if (!has.has(watcher)) {
    has.add(watcher);
    queue.push(watcher);

    if (!waiting) {
      waiting = true;
      // 使用微任务或 setTimeout 模拟
      if (typeof Promise !== 'undefined') {
        Promise.resolve().then(flushQueue);
      } else {
        setTimeout(flushQueue, 0);
      }
    }
  }
}

function flushQueue(): void {
  // 按 watcher id 排序（简化实现中跳过排序）
  for (const watcher of queue) {
    has.delete(watcher);
    watcher.run();
  }
  queue.length = 0;
  waiting = false;
}
