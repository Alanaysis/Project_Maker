# 响应式框架

实现一个基于 Proxy 的响应式数据绑定框架，深入理解 Vue 3 响应式系统的核心原理。

## 学习目标

- 理解响应式原理
- 掌握依赖收集机制
- 学会数据劫持（Proxy）

## 核心循环

```
数据变更 → 依赖通知 → 视图更新
```

## 技术栈

- TypeScript
- Proxy（ES2015+）
- 无外部框架依赖

## 项目结构

```
src/
├── index.ts            # 入口，导出所有 API
├── dep.ts              # 依赖管理器（Dep）
├── watcher.ts          # 观察者（Watcher）
├── reactive.ts         # 响应式核心（Proxy 拦截）
├── computed.ts         # 计算属性
└── watch.ts            # 侦听器
```

## 核心 API

### reactive(target)

将对象转为响应式代理。属性读取时自动收集依赖，修改时自动通知更新。

```typescript
const state = reactive({ count: 0 });
state.count = 1; // 自动触发更新
```

### computed(getter)

创建计算属性。惰性求值，依赖不变时返回缓存结果。

```typescript
const sum = computed(() => state.a + state.b);
console.log(sum.value); // 求值并缓存
```

### watch(source, callback)

侦听响应式数据变化，返回取消函数。

```typescript
const unwatch = watch(
  () => state.count,
  (newVal, oldVal) => console.log(`${oldVal} -> ${newVal}`)
);
state.count = 1; // 输出: 0 -> 1
unwatch(); // 取消侦听
```

### ref(value)

将基本类型包装为响应式对象。

```typescript
const count = ref(0);
count.value = 1; // 触发更新
```

## 快速开始

```bash
# 安装依赖
npm install

# 运行测试
npm test

# 运行示例
npm run example:basic
npm run example:computed
npm run example:watch
npm run example:todo
```

## 原理概述

### 数据劫持

使用 `Proxy` 拦截对象的 `get`/`set`/`delete` 操作：

- **get**：读取属性时，将当前活跃的 Watcher 收集到该属性的依赖列表
- **set**：设置属性时，通知所有依赖该属性的 Watcher 执行更新

### 依赖收集

```
Watcher 求值 → pushTarget → 读取属性 → dep.depend() → 加入依赖列表 → popTarget
```

### 更新通知

```
修改属性 → dep.notify() → 遍历依赖列表 → watcher.update() → 重新求值/回调
```

## 文档

- [01 - 市场调研](docs/01-RESEARCH.md)
- [02 - 架构设计](docs/02-DESIGN.md)
- [03 - 实现细节](docs/03-IMPLEMENTATION.md)
- [04 - 测试策略](docs/04-TESTING.md)
- [05 - 开发指南](docs/05-DEVELOPMENT.md)
- [学习笔记](LEARNING_NOTES.md)
