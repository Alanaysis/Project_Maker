/**
 * Dep - 依赖管理器
 *
 * 负责收集和通知订阅者（Watcher）。
 * 每个响应式属性都关联一个 Dep 实例。
 *
 * 核心原理：
 * 1. 当读取属性时，将当前 Watcher 收集到依赖列表中
 * 2. 当属性变更时，通知所有收集到的 Watcher 执行更新
 */

import { Watcher } from './watcher';

export class Dep {
  /** 当前正在求值的 Watcher（全局唯一） */
  static target: Watcher | null = null;

  /** 存储该属性的所有订阅者 */
  private subs: Set<Watcher> = new Set();

  /**
   * 添加订阅者
   * 在属性被读取时调用，将当前活跃的 Watcher 加入依赖
   */
  depend(): void {
    if (Dep.target) {
      this.subs.add(Dep.target);
    }
  }

  /**
   * 通知所有订阅者更新
   * 在属性值变更时调用
   */
  notify(): void {
    for (const sub of this.subs) {
      sub.update();
    }
  }

  /**
   * 移除订阅者
   */
  removeSub(sub: Watcher): void {
    this.subs.delete(sub);
  }

  /** 获取当前订阅者数量（调试用） */
  get subCount(): number {
    return this.subs.size;
  }
}

/**
 * 用于管理 Watcher 的入栈/出栈
 * 支持嵌套的 Watcher 求值（如 computed 依赖另一个 computed）
 */
const targetStack: Watcher[] = [];

export function pushTarget(target: Watcher): void {
  targetStack.push(target);
  Dep.target = target;
}

export function popTarget(): void {
  targetStack.pop();
  Dep.target = targetStack[targetStack.length - 1] || null;
}
