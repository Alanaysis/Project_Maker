/**
 * Computed - 计算属性
 *
 * 基于 Watcher 的惰性求值实现。
 * 计算属性会缓存结果，只有依赖变化时才重新求值。
 *
 * 关键设计：computed 既是"消费者"（依赖其他响应式数据），
 * 又是"生产者"（被其他 watcher/computed 依赖）。
 * 因此需要自己的 Dep 来管理下游依赖关系。
 */

import { Watcher } from './watcher';
import { Dep, pushTarget, popTarget } from './dep';

export interface ComputedRef<T> {
  readonly value: T;
}

/**
 * 创建计算属性
 *
 * @param getter - 求值函数
 * @returns 只读的计算属性引用
 *
 * @example
 * ```ts
 * const state = reactive({ firstName: '张', lastName: '三' });
 * const fullName = computed(() => state.firstName + state.lastName);
 * console.log(fullName.value); // "张三"
 * ```
 */
export function computed<T>(getter: () => T): ComputedRef<T> {
  // computed 自身的 Dep：管理"谁依赖了这个 computed"
  const computedDep = new Dep();

  // 创建惰性 watcher：只在访问时求值
  const watcher = new Watcher(getter, null, {
    lazy: true,
    // 当 watcher 的依赖变化时，不仅标记 dirty，还要通知 computed 的订阅者
    computedCallback: () => {
      computedDep.notify();
    },
  });

  const ref: ComputedRef<T> = {
    get value(): T {
      // 如果有活跃的 Watcher 在求值，让它订阅 computed 的 Dep
      // 这样 computed 变化时，订阅它的 watcher 也会被通知
      if (Dep.target) {
        computedDep.depend();
      }

      if (watcher.dirty) {
        // 重新求值，收集依赖
        watcher.evaluate();
      }

      return watcher.value;
    },
  };

  return ref;
}
