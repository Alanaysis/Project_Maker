# 05 - 开发指南

## 1. 环境准备

### 前置条件
- Node.js >= 16
- npm >= 8

### 安装依赖

```bash
cd projects/reactive-framework
npm install
```

## 2. 项目结构

```
reactive-framework/
├── src/                    # 源代码
│   ├── index.ts            # 入口文件，导出所有 API
│   ├── dep.ts              # 依赖管理器
│   ├── watcher.ts          # 观察者
│   ├── reactive.ts         # 响应式核心（Proxy）
│   ├── computed.ts         # 计算属性
│   └── watch.ts            # 侦听器
├── tests/                  # 测试文件
│   ├── run.ts              # 测试运行器
│   ├── test_reactive.ts
│   ├── test_computed.ts
│   ├── test_watch.ts
│   └── test_edge_cases.ts
├── examples/               # 示例代码
│   ├── basic.ts            # 基本用法
│   ├── computed.ts         # 计算属性
│   ├── watch.ts            # 侦听器
│   └── todo-app.ts         # Todo 应用
├── docs/                   # 文档
│   ├── 01-RESEARCH.md      # 市场调研
│   ├── 02-DESIGN.md        # 架构设计
│   ├── 03-IMPLEMENTATION.md # 实现细节
│   ├── 04-TESTING.md       # 测试策略
│   └── 05-DEVELOPMENT.md   # 开发指南
├── package.json
├── tsconfig.json
├── README.md
└── LEARNING_NOTES.md
```

## 3. 常用命令

```bash
# 编译 TypeScript
npm run build

# 运行测试
npm test

# 运行示例
npm run example:basic
npm run example:computed
npm run example:watch
npm run example:todo
```

## 4. 核心 API

### reactive(target)

将对象转为响应式代理。

```typescript
import { reactive } from './src';

const state = reactive({ count: 0 });
state.count = 1; // 自动触发更新
```

### computed(getter)

创建计算属性，惰性求值并缓存结果。

```typescript
import { reactive, computed } from './src';

const state = reactive({ a: 1, b: 2 });
const sum = computed(() => state.a + state.b);
console.log(sum.value); // 3
```

### watch(source, callback, options)

侦听响应式数据变化。

```typescript
import { reactive, watch } from './src';

const state = reactive({ count: 0 });
const unwatch = watch(
  () => state.count,
  (newVal, oldVal) => console.log(`${oldVal} -> ${newVal}`)
);

state.count = 1; // 输出: 0 -> 1
unwatch(); // 取消侦听
```

### ref(value)

将基本类型值包装为响应式对象。

```typescript
import { ref } from './src';

const count = ref(0);
count.value = 1; // 触发更新
```

## 5. 开发流程

1. 修改源代码 (`src/`)
2. 运行测试验证 (`npm test`)
3. 运行示例确认行为 (`npm run example:basic`)
4. 更新文档（如有必要）

## 6. 调试技巧

- 在 `Dep.target` 上打断点，观察依赖收集过程
- 在 `dep.notify()` 中打断点，观察更新通知
- 使用 `toRaw()` 获取原始对象进行对比
- 检查 `depsMap` 的内容查看依赖关系

## 7. 扩展方向

- 添加 `watchEffect()` API
- 实现 `shallowReactive()` 浅层响应式
- 支持 `Map` 和 `Set` 的响应式
- 添加调试工具（依赖图可视化）
- 实现批量更新的调度器
- 添加 `readonly()` 只读代理
