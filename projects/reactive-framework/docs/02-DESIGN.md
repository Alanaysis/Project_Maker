# 02 - 项目架构设计

## 1. 整体架构

```
┌─────────────────────────────────────────────────────┐
│                    用户 API 层                        │
│   reactive()  │  computed()  │  watch()  │  ref()    │
├─────────────────────────────────────────────────────┤
│                  核心响应式层                          │
│                                                     │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐      │
│  │  Proxy   │    │ Watcher  │    │   Dep    │      │
│  │ (数据劫持) │◄──►│ (观察者)  │◄──►│(依赖管理) │      │
│  └──────────┘    └──────────┘    └──────────┘      │
│       │               │               │             │
│       ▼               ▼               ▼             │
│  get/set 拦截    求值/回调执行    依赖收集/通知       │
└─────────────────────────────────────────────────────┘
```

## 2. 模块划分

### 2.1 dep.ts - 依赖管理器

```
职责：
  - 管理属性的订阅者列表
  - 提供 depend() 供收集依赖
  - 提供 notify() 供通知更新

关键设计：
  - Dep.target: 全局唯一，指向当前正在求值的 Watcher
  - pushTarget/popTarget: 支持嵌套 Watcher 的栈管理

数据结构：
  class Dep {
    static target: Watcher | null    // 当前活跃的 Watcher
    subs: Set<Watcher>               // 订阅者集合
  }
```

### 2.2 watcher.ts - 观察者

```
职责：
  - 执行求值函数（触发 getter，收集依赖）
  - 在依赖变化时执行回调
  - 支持惰性求值（computed 模式）

关键设计：
  - getter: 求值函数，返回要观察的值
  - callback: 变化回调
  - lazy: 是否惰性求值
  - dirty: 是否需要重新求值（computed 用）

生命周期：
  new Watcher(getter, callback)
    → get() [首次求值，收集依赖]
    → [等待依赖变化]
    → update() [依赖变化时调用]
    → run() [重新求值，执行回调]
    → teardown() [销毁]
```

### 2.3 reactive.ts - 响应式核心

```
职责：
  - 使用 Proxy 拦截对象操作
  - 在 get 中调用 dep.depend() 收集依赖
  - 在 set 中调用 dep.notify() 通知更新
  - 递归代理嵌套对象

关键设计：
  - proxyMap: 原始对象 → 代理对象（避免重复代理）
  - rawMap: 代理对象 → 原始对象（toRaw 用）
  - depsMap: 对象 → 属性 → Dep 实例
  - 惰性代理：嵌套对象在访问时才代理
```

### 2.4 computed.ts - 计算属性

```
职责：
  - 创建惰性求值的 Watcher
  - 提供缓存机制（dirty 标记）
  - 支持依赖传递

关键设计：
  - 使用 lazy Watcher
  - 访问时检查 dirty，决定是否重新求值
  - 依赖传递：让依赖 computed 的 Watcher 也收集 computed 的依赖
```

### 2.5 watch.ts - 侦听器

```
职责：
  - 创建 Watcher 并绑定回调
  - 提供 immediate 选项
  - 返回 unwatch 函数
```

## 3. 数据流

### 3.1 依赖收集流程

```
组件渲染 / computed 求值 / watch 执行
         │
         ▼
    pushTarget(watcher)
         │
         ▼
    执行 getter 函数
         │
         ▼
    读取响应式属性 (proxy.get)
         │
         ▼
    dep.depend() ← 将 watcher 加入 dep.subs
         │
         ▼
    popTarget()
```

### 3.2 更新通知流程

```
修改响应式属性 (proxy.set)
         │
         ▼
    dep.notify()
         │
         ▼
    遍历 dep.subs
         │
    ┌────┼────┐
    ▼    ▼    ▼
  w1   w2   w3  (各个 watcher.update())
    │    │    │
    ▼    ▼    ▼
  执行各自的回调/重新求值
```

## 4. 关键数据结构

```
WeakMap<object, Map<string, Dep>>   // depsMap
  ┌─────────┐    ┌─────────────┐
  │ {a:1,b:2}│───►│ "a" → Dep   │
  └─────────┘    │ "b" → Dep   │
                 └─────────────┘

WeakMap<object, object>   // proxyMap (raw → proxy)
WeakMap<object, object>   // rawMap  (proxy → raw)
```

## 5. 与 Vue 3 的对比

| 特性 | 本项目 | Vue 3 |
|------|--------|-------|
| Proxy | 是 | 是 |
| 依赖收集 | Dep + Watcher | effect + track/trigger |
| 计算属性 | lazy Watcher | computed effect |
| 侦听器 | watch() API | watch() API |
| 调度器 | 简化版 | 完整 scheduler |
| 嵌套支持 | 栈管理 | 栈管理 |
| WeakMap 缓存 | 是 | 是 |
