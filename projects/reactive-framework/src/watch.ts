/**
 * Watch - 侦听器 API
 *
 * 提供 watch() 函数用于侦听响应式数据的变化。
 */

import { Watcher } from './watcher';

export interface WatchOptions {
  /** 是否立即执行一次回调 */
  immediate?: boolean;
  /** 是否同步执行 */
  sync?: boolean;
}

/**
 * 侦听响应式数据变化
 *
 * @param source - 数据源（返回要监听值的函数）
 * @param callback - 变化回调
 * @param options - 选项
 * @returns 取消侦听的函数
 *
 * @example
 * ```ts
 * const state = reactive({ count: 0 });
 *
 * // 侦听特定属性
 * watch(
 *   () => state.count,
 *   (newVal, oldVal) => {
 *     console.log(`count: ${oldVal} -> ${newVal}`);
 *   }
 * );
 *
 * state.count = 1; // 输出: count: 0 -> 1
 * ```
 */
export function watch<T>(
  source: () => T,
  callback: (newValue: T, oldValue: T) => void,
  options: WatchOptions = {}
): () => void {
  const watcher = new Watcher(source, callback, options);

  // 返回取消侦听函数
  return () => {
    watcher.teardown();
  };
}
