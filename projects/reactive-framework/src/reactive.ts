/**
 * Reactive - 响应式核心
 *
 * 使用 Proxy 实现数据劫持，拦截属性的读取和设置操作。
 *
 * 原理：
 * - get 拦截：读取属性时进行依赖收集（调用 dep.depend()）
 * - set 拦截：设置属性时通知依赖更新（调用 dep.notify()）
 * - 递归处理：嵌套对象也转为响应式
 */

import { Dep } from './dep';
import { Watcher } from './watcher';

/** 存储每个对象属性对应的 Dep 实例 */
const depsMap: WeakMap<object, Map<string | symbol, Dep>> = new WeakMap();

/** 存储原始对象到代理的映射（避免重复代理） */
const proxyMap: WeakMap<object, object> = new WeakMap();

/** 存储代理到原始对象的映射 */
const rawMap: WeakMap<object, object> = new WeakMap();

/**
 * 获取或创建属性的 Dep 实例
 */
function getDep(target: object, key: string | symbol): Dep {
  let targetDeps = depsMap.get(target);
  if (!targetDeps) {
    targetDeps = new Map();
    depsMap.set(target, targetDeps);
  }

  let dep = targetDeps.get(key);
  if (!dep) {
    dep = new Dep();
    targetDeps.set(key, dep);
  }

  return dep;
}

/**
 * 判断是否为需要递归代理的对象
 */
function isPlainObject(value: any): value is object {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}

/**
 * 数组变异方法列表
 * 这些方法会修改数组本身，需要手动触发依赖通知
 * 因为原生方法可能绕过 Proxy 的 set 陷阱
 */
const ARRAY_MUTABLE_METHODS = new Set([
  'push', 'pop', 'shift', 'unshift', 'splice', 'sort', 'reverse', 'fill',
]);

/**
 * 为数组变异方法创建包装函数
 * 在执行原生方法后，手动触发 length 和新增元素的通知
 */
function createArrayMethodProxy(
  target: any[],
  methodName: string,
  originalMethod: Function
): Function {
  switch (methodName) {
    case 'push':
      return function (...args: any[]) {
        const startIndex = target.length;
        const result = originalMethod.apply(target, args);
        // 通知新增元素
        for (let i = startIndex; i < target.length; i++) {
          getDep(target, i.toString()).notify();
        }
        // 通知 length 变化
        getDep(target, 'length').notify();
        return result;
      };
    case 'pop':
      return function () {
        const oldLength = target.length;
        const result = originalMethod.call(target);
        // 通知被删除的元素
        if (oldLength > 0) {
          getDep(target, (oldLength - 1).toString()).notify();
        }
        // 通知 length 变化
        getDep(target, 'length').notify();
        return result;
      };
    case 'shift':
      return function () {
        const oldLength = target.length;
        const result = originalMethod.call(target);
        // 通知 length 变化
        getDep(target, 'length').notify();
        // 通知索引变化（所有元素前移）
        for (let i = 0; i < oldLength - 1; i++) {
          getDep(target, i.toString()).notify();
        }
        return result;
      };
    case 'unshift':
      return function (...args: any[]) {
        const oldLength = target.length;
        const result = originalMethod.apply(target, args);
        // 通知 length 变化
        getDep(target, 'length').notify();
        // 通知所有索引变化
        for (let i = 0; i < target.length; i++) {
          getDep(target, i.toString()).notify();
        }
        return result;
      };
    case 'splice':
      return function (...args: any[]) {
        const result = originalMethod.apply(target, args);
        // 通知 length 变化
        getDep(target, 'length').notify();
        // 通知所有可能受影响的索引
        for (let i = 0; i < target.length; i++) {
          getDep(target, i.toString()).notify();
        }
        return result;
      };
    default:
      // sort, reverse, fill 等
      return function (...args: any[]) {
        const result = originalMethod.apply(target, args);
        // 通知所有元素可能变化
        for (let i = 0; i < target.length; i++) {
          getDep(target, i.toString()).notify();
        }
        return result;
      };
  }
}

/**
 * 将对象转换为响应式对象
 *
 * @param target - 要代理的原始对象
 * @returns 响应式代理对象
 *
 * @example
 * ```ts
 * const state = reactive({ count: 0, nested: { value: 1 } });
 * // 读取时自动收集依赖
 * console.log(state.count); // 0
 * // 修改时自动通知更新
 * state.count = 1;
 * ```
 */
export function reactive<T extends object>(target: T): T {
  // 已经是代理则直接返回
  if (proxyMap.has(target)) {
    return proxyMap.get(target) as T;
  }

  // 防止对已经是代理的对象重复代理
  if (rawMap.has(target as object)) {
    return target;
  }

  const handler: ProxyHandler<T> = {
    get(target, key, receiver) {
      const value = Reflect.get(target, key, receiver);

      // 依赖收集：如果有活跃的 Watcher，则收集依赖
      if (Dep.target) {
        const dep = getDep(target, key);
        dep.depend();
      }

      // 数组变异方法拦截：原生方法可能绕过 Proxy 的 set 陷阱
      // 手动包装这些方法，确保触发依赖通知
      if (Array.isArray(target) && typeof key === 'string' && ARRAY_MUTABLE_METHODS.has(key)) {
        return createArrayMethodProxy(target as any[], key, value as Function);
      }

      // 递归代理嵌套对象和数组
      if (value !== null && typeof value === 'object') {
        return reactive(value);
      }

      return value;
    },

    set(target, key, value, receiver) {
      const oldValue = (target as any)[key];

      // 设置新值
      const result = Reflect.set(target, key, value, receiver);

      // 值确实变化了才通知
      if (oldValue !== value) {
        const dep = getDep(target, key);
        dep.notify();
      }

      return result;
    },

    deleteProperty(target, key) {
      const hadKey = key in target;
      const result = Reflect.deleteProperty(target, key);

      // 删除成功且确实存在该属性时通知
      if (hadKey && result) {
        const dep = getDep(target, key);
        dep.notify();
      }

      return result;
    },

    has(target, key) {
      // 依赖收集（for...in, in 操作符）
      if (Dep.target) {
        const dep = getDep(target, key);
        dep.depend();
      }
      return Reflect.has(target, key);
    },
  };

  const proxy = new Proxy(target, handler);

  proxyMap.set(target, proxy);
  rawMap.set(proxy, target);

  return proxy as T;
}

/**
 * 检查对象是否为响应式代理
 */
export function isReactive(value: any): boolean {
  return rawMap.has(value);
}

/**
 * 获取响应式代理的原始对象
 */
export function toRaw<T>(value: T): T {
  return rawMap.get(value as any) as T || value;
}

/**
 * 创建 ref 包装
 * 将基本类型值包装为响应式对象
 *
 * @param value - 初始值
 * @returns 包含 .value 属性的响应式对象
 *
 * @example
 * ```ts
 * const count = ref(0);
 * console.log(count.value); // 0
 * count.value = 1; // 触发更新
 * ```
 */
export function ref<T>(value: T): { value: T } {
  return reactive({ value }) as { value: T };
}

/**
 * 创建响应式数据并返回用于创建 Watcher 的工具函数
 * 这是对外暴露的主要 API 入口
 */
export function createReactive<T extends object>(target: T) {
  const state = reactive(target);

  /**
   * 创建计算属性
   */
  function computed<T>(getter: () => T): { readonly value: T } {
    const watcher = new Watcher(getter, null, { lazy: true });

    const computedRef = {
      get value(): T {
        if (watcher.dirty) {
          watcher.evaluate();
        }
        // 让依赖 computed 的 Watcher 也收集 computed 自身的依赖
        if (Dep.target) {
          watcher.depend();
        }
        return watcher.value;
      },
    };

    return computedRef;
  }

  /**
   * 侦听数据变化
   */
  function watch<T>(
    getter: () => T,
    callback: (newValue: T, oldValue: T) => void,
    options: { immediate?: boolean; sync?: boolean } = {}
  ): () => void {
    const watcher = new Watcher(getter, callback, options);

    // 返回取消侦听函数
    return () => {
      watcher.teardown();
    };
  }

  return { state, computed, watch };
}
