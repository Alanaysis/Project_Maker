# 04 - 测试策略

## 1. 测试概述

本项目采用手动测试运行器，无需外部测试框架依赖。测试文件位于 `tests/` 目录。

## 2. 测试文件结构

```
tests/
├── run.ts                  # 测试运行入口
├── test_reactive.ts        # reactive() 核心功能测试
├── test_computed.ts        # computed() 计算属性测试
├── test_watch.ts           # watch() 侦听器测试
└── test_edge_cases.ts      # 边界情况测试
```

## 3. 测试用例设计

### 3.1 reactive() 测试

| 测试项 | 描述 |
|--------|------|
| 基本响应式 | 创建代理，读取/修改值 |
| 嵌套对象代理 | 深层嵌套对象自动代理 |
| 新增属性 | 动态添加属性可响应 |
| 删除属性 | 删除属性触发更新 |
| isReactive | 检测代理状态 |
| toRaw | 获取原始对象 |
| 不重复代理 | 同一对象只代理一次 |
| ref | 基本类型包装 |
| 数组操作 | push/pop/索引更新 |
| 依赖收集 | Watcher 正确收集依赖 |
| 多 Watcher | 多个 Watcher 订阅同一属性 |

### 3.2 computed() 测试

| 测试项 | 描述 |
|--------|------|
| 基本计算 | 计算结果正确 |
| 惰性求值 | 只在访问时求值 |
| 缓存 | 依赖不变时不重复求值 |
| 链式计算 | computed 依赖 computed |
| 与 watch 联动 | computed 变化触发 watch |

### 3.3 watch() 测试

| 测试项 | 描述 |
|--------|------|
| 基本侦听 | 值变化触发回调 |
| 新旧值 | 回调接收正确的新旧值 |
| immediate | 立即执行回调 |
| 取消侦听 | unwatch() 停止侦听 |
| 嵌套属性 | 侦听深层属性变化 |
| 多依赖 | 侦听多个值的计算结果 |

### 3.4 边界情况测试

| 测试项 | 描述 |
|--------|------|
| 数组内嵌 | 对象包含数组 |
| null 值 | 处理 null 属性 |
| 多层嵌套 | 3+ 层嵌套对象 |
| Symbol 属性 | Symbol 键的支持 |
| computed 嵌套 | computed A 依赖 computed B |
| 同值不触发 | 设置相同值不触发回调 |
| 循环引用 | 对象引用自身 |
| ref + computed | ref 作为 computed 依赖 |
| teardown | 销毁后不再触发 |
| Dep.target 清理 | 无泄漏的活跃 Watcher |

## 4. 运行测试

```bash
# 安装依赖
npm install

# 运行所有测试
npm test

# 或直接使用 ts-node
npx ts-node tests/run.ts
```

## 5. 测试输出格式

```
=== Reactive Framework Tests ===

--- reactive() tests ---
  PASS: Initial value is correct
  PASS: Value updates correctly
  ...

--- computed() tests ---
  PASS: Computed value is correct
  PASS: First access returns correct value
  ...

--- watch() tests ---
  PASS: Two changes recorded
  ...

--- edge cases tests ---
  PASS: Array push triggers watcher
  ...

=== Test Summary ===
All test suites completed.
```

## 6. 测试覆盖的目标

- 核心 API 的正确性
- 依赖收集的准确性
- 更新通知的及时性
- 缓存机制的有效性
- 边界情况的健壮性
- 内存管理的安全性
