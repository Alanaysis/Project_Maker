# 学习笔记 - 响应式框架

## 1. 核心概念理解

### 1.1 什么是响应式？

响应式系统的核心思想是：当数据变化时，依赖该数据的所有地方自动更新。

```
传统方式：
  手动调用 update() 函数

响应式方式：
  修改数据 → 自动触发更新（无需手动干预）
```

这就像 Excel 公式：当 A1 变化时，`=A1*2` 的单元格自动更新。

### 1.2 Proxy vs Object.defineProperty

```
Object.defineProperty (Vue 2):
  - 只能拦截 get/set
  - 需要遍历所有属性
  - 无法检测新增/删除属性
  - 数组需要特殊处理

Proxy (Vue 3, 本项目):
  - 拦截 13 种操作
  - 惰性代理（按需代理嵌套对象）
  - 完美支持数组
  - 支持 Map/Set
```

**关键区别**：defineProperty 是"属性级别"的拦截，Proxy 是"对象级别"的拦截。

## 2. 实现过程中的关键理解

### 2.1 依赖收集的本质

依赖收集回答的问题是："谁在用这个数据？"

```
执行上下文（Watcher）
  │
  ▼
读取 state.count  ──────►  记录：Watcher 依赖了 count
  │
  ▼
读取 state.name   ──────►  记录：Watcher 依赖了 name
  │
  ▼
求值完成
```

关键设计：`Dep.target` 是一个全局变量，指向"当前正在求值的 Watcher"。
在 getter 中检查 `Dep.target`，如果有值就收集依赖。

### 2.2 为什么要用栈管理 Watcher？

```
computed A = state.x + computed B
computed B = state.y * 2

求值 A 时：
  1. pushTarget(A)    → Dep.target = A
  2. 读取 state.x     → A 依赖 state.x
  3. 读取 computed B   → 触发 B 的 getter
     4. pushTarget(B)  → Dep.target = B
     5. 读取 state.y   → B 依赖 state.y
     6. popTarget()    → Dep.target = A  ← 关键：恢复到 A
  7. popTarget()       → Dep.target = null
```

### 2.3 computed 的惰性求值

computed 不是每次访问都重新求值，而是：
1. 首次访问时求值，标记 `dirty = false`
2. 依赖变化时，标记 `dirty = true`（不立即求值）
3. 下次访问时，发现 `dirty = true`，重新求值

```
computed sum = a + b

访问 sum.value  →  求值，dirty = false，返回 3
访问 sum.value  →  dirty = false，直接返回缓存 3
修改 a = 2      →  dirty = true（不求值）
访问 sum.value  →  dirty = true，重新求值，返回 4
```

### 2.4 依赖传递

问题：watcher X 依赖 computed A，computed A 依赖 state.x。
当 state.x 变化时，如何通知 watcher X？

```
解决方案：computed 的 getter 中调用 watcher.depend()
  → 将 computed 的所有依赖（state.x）也收集到 watcher X 中

结果：
  state.x 的 Dep.subs = [computed A 的 watcher, watcher X]
  state.x 变化时，两个都会被通知
```

## 3. Proxy 实战经验

### 3.1 Reflect 的重要性

```typescript
// 正确：使用 Reflect
const value = Reflect.get(target, key, receiver);

// 错误：直接访问
const value = target[key]; // 可能丢失 this 上下文
```

`receiver` 参数确保 getter 中的 `this` 指向代理对象而非原始对象。

### 3.2 避免重复代理

```typescript
const proxyMap: WeakMap<object, object> = new WeakMap();

function reactive(target) {
  if (proxyMap.has(target)) {
    return proxyMap.get(target); // 已代理则直接返回
  }
  // ...
}
```

### 3.3 循环引用处理

```typescript
const state = reactive({});
state.self = state; // 循环引用

// get 拦截器中：访问 state.self 时
// 由于 proxyMap 已有记录，直接返回已有的 proxy，不会无限递归
```

## 4. 设计模式的应用

### 4.1 发布-订阅模式

```
Dep（调度中心）
  ├── subs: Set<Watcher>  // 订阅者列表
  ├── depend()            // 订阅
  └── notify()            // 发布

Watcher（订阅者）
  ├── update()            // 接收通知
  └── callback()          // 执行回调
```

### 4.2 观察者模式

响应式数据是被观察者（Subject），Watcher 是观察者（Observer）。
数据变化时，自动通知所有观察者。

## 5. 性能考量

### 5.1 WeakMap 的选择

使用 WeakMap 而非 Map 存储依赖映射：
- 当原始对象被垃圾回收时，对应的 Dep 也会被回收
- 避免内存泄漏
- 不需要手动清理

### 5.2 Set 去重

使用 Set 存储订阅者，自动避免重复订阅。

### 5.3 异步更新队列

将多次同步更新合并为一次异步更新：
```
state.a = 1;  // 排队
state.b = 2;  // 排队（同一个 watcher）
state.c = 3;  // 排队
// 微任务执行：watcher 只更新一次
```

## 6. 与 Vue 3 的对比

| 概念 | 本项目 | Vue 3 |
|------|--------|-------|
| 依赖管理 | Dep 类 | track/trigger 函数 |
| 观察者 | Watcher 类 | ReactiveEffect 类 |
| 求值 | watcher.get() | effect.run() |
| 调度 | 简化队列 | 完整 Scheduler |
| 计算属性 | lazy watcher | computed effect |

核心思想完全一致，Vue 3 只是做了更多优化和边界处理。

## 7. 常见误区

1. **不是所有属性读取都会收集依赖**：只有在 Watcher 求值过程中（Dep.target 不为 null）才会收集
2. **相同值不会触发更新**：set 拦截器中会比较新旧值
3. **嵌套对象是惰性代理的**：只有访问时才代理，不是初始化时递归
4. **computed 有缓存**：依赖不变时不重新求值

## 8. 进一步学习

- Vue 3 源码 `packages/reactivity/` 目录
- Proxy 的 13 种拦截操作
- WeakRef 和 FinalizationRegistry（更高级的内存管理）
- 响应式框架的调试工具实现
