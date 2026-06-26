# MVCC 并发控制 / MVCC Concurrency Control

> 实现多版本并发控制，学习快照隔离、冲突检测和垃圾回收

> Implement Multi-Version Concurrency Control, learn snapshot isolation, conflict detection, and garbage collection

---

## 目录 / Contents

- [概述 / Overview](#概述--overview)
- [学习目标 / Learning Objectives](#学习目标--learning-objectives)
- [架构 / Architecture](#架构--architecture)
- [快速开始 / Quick Start](#快速开始--quick-start)
- [示例 / Examples](#示例--examples)
- [MVCC 理论基础 / MVCC Theory](#mvcc-理论基础--mvcc-theory)
- [运行测试 / Running Tests](#运行测试--running-tests)

---

## 概述 / Overview

本项目是一个教育性的 MVCC（多版本并发控制）实现，展示了数据库如何使用多版本机制来提高并发性能。

This project is an educational implementation of MVCC (Multi-Version Concurrency Control) that demonstrates how databases use multiple versions to improve concurrency performance.

### 核心概念 / Core Concepts

| 概念 | 描述 |
|------|------|
| **多版本** | 每个数据项有多个带时间戳的版本 |
| **快照隔离** | 事务读取启动时的一致性视图 |
| **冲突检测** | 检测写-写和读-写冲突 |
| **垃圾回收** | 清理不再需要的旧版本 |
| **SSI** | 可串行化快照隔离，防止可串行化异常 |

---

## 学习目标 / Learning Objectives

### 理解 MVCC / Understand MVCC
- 多版本存储结构
- 时间戳管理
- 版本链的维护

### 掌握快照隔离 / Master Snapshot Isolation
- 一致性读的实现
- 快照创建与管理
- 与两阶段锁定的对比

### 学会垃圾回收 / Learn Garbage Collection
- 基于活跃快照的 GC 策略
- 版本链清理
- 内存回收的安全保证

### 额外目标 / Additional Goals
- 冲突检测（写-写、读-写）
- 死锁检测（等待图）
- 可串行化快照隔离（SSI）

---

## 架构 / Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Transaction Manager                 │
│  (协调快照管理器和冲突检测器)                           │
├─────────────┬───────────────────────────────────────┤
│  Snapshot    │     Conflict Detector                 │
│  Manager     │     (写-写/读-写检测, 死锁检测)         │
│  ┌────────┐  │     ┌───────────┐ ┌──────────────┐  │
│  │事务生命周期│  │     │冲突检测   │ │ 等待图/死锁  │  │
│  │快照创建  │  │     │SSI检查   │ │ 环检测      │  │
│  │生命周期  │  │     └───────────┘ └──────────────┘  │
│  └────────┘  │                                       │
├─────────────┴───────────────────────────────────────┤
│                  MVCC Storage                        │
│  ┌──────────────────────────────────────────────┐   │
│  │  key1 → [v3 → v2 → v1]  (版本链, 按时间戳排序)│   │
│  │  key2 → [v1]                                  │   │
│  │  key3 → [v2 → v1]                             │   │
│  └──────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────┤
│                  Garbage Collector                   │
│  (基于活跃快照清理旧版本)                              │
└─────────────────────────────────────────────────────┘
```

### 核心组件 / Core Components

| 组件 | 文件 | 功能 |
|------|------|------|
| MVCCStorage | `src/mvcc.go` | 多版本存储，版本链管理 |
| Transaction | `src/mvcc.go` | 事务，读写集跟踪 |
| SnapshotManager | `src/mvcc.go` | 快照创建和事务生命周期 |
| ConflictDetector | `src/mvcc.go` | 冲突检测，死锁检测 |
| GarbageCollector | `src/mvcc.go` | 旧版本清理 |
| TransactionManager | `src/mvcc.go` | 高层 API |

---

## 快速开始 / Quick Start

### 环境要求 / Requirements
- Go 1.21+

### 运行所有示例 / Run All Demos

```bash
cd projects/mvcc
go run src/demos.go
```

### 单独运行示例 / Run Individual Examples

```bash
# 基本 MVCC 操作
go run examples/basic_mvcc.go

# 快照隔离演示
go run examples/snapshot_isolation.go

# 冲突检测演示
go run examples/conflict_detection.go

# 垃圾回收演示
go run examples/garbage_collection.go
```

---

## 示例 / Examples

### 1. 基本 MVCC 操作 / Basic MVCC Operations

展示 MVCC 的基本操作：
- 创建事务
- 快照读
- 写入和提交
- 版本链观察

```bash
go run examples/basic_mvcc.go
```

### 2. 快照隔离演示 / Snapshot Isolation Demo

展示快照隔离如何：
- 给每个事务一致的数据库视图
- 允许并发读取不阻塞
- 防止脏读
- 防止不可重复读

```bash
go run examples/snapshot_isolation.go
```

### 3. 冲突检测演示 / Conflict Detection Demo

展示冲突检测：
- 写-写冲突（两个事务写同一键）
- 读-写冲突（一个事务读取另一个写入的键）
- 冲突解决策略

```bash
go run examples/conflict_detection.go
```

### 4. 垃圾回收演示 / Garbage Collection Demo

展示垃圾回收：
- 版本链如何增长
- 如何回收旧版本
- GC 的安全性保证

```bash
go run examples/garbage_collection.go
```

---

## MVCC 理论基础 / MVCC Theory

### 什么是 MVCC？ / What is MVCC?

MVCC（Multi-Version Concurrency Control）是一种并发控制方法，它通过为每个数据项维护多个版本来允许不冲突的事务同时访问相同的数据。

MVCC is a concurrency control method that allows non-conflicting transactions to access the same data simultaneously by maintaining multiple versions of each data item.

### 核心机制 / Core Mechanisms

#### 1. 版本链 / Version Chains

每个数据项维护一个版本链：

```
key1 → [v3(ts=3) → v2(ts=2) → v1(ts=1)]
         ↑ 最新版本
```

- 版本按写入时间戳降序排列
- 每个版本包含：值、写入时间戳、读取时间戳、写入者事务ID、提交状态

#### 2. 快照读 / Snapshot Read

事务启动时创建快照：

```
事务 T 在 ts=5 开始
读取 key1: 遍历版本链，找到第一个 WriteTS <= 5 且已提交的版本
结果: v2(ts=2) ← 事务 T 看到的 consistent view
```

#### 3. 快照隔离 / Snapshot Isolation

快照隔离提供以下保证：
- **无脏读**：只能读取已提交的数据
- **无不可重复读**：事务内多次读取同一键得到相同结果
- **允许幻读**：快照隔离允许幻读（SSI 解决此问题）

#### 4. 冲突检测 / Conflict Detection

**写-写冲突**：两个事务写入同一键
```
T1 写 key1 → T2 写 key1 → 冲突！
解决：中止较年轻的事务
```

**读-写冲突**：一个事务读取另一个写入的键
```
T1 读 key1 → T2 写 key1 → T1 读到了旧值
解决：SSI 检测并中止 T1
```

**SSI 规则**：防止可串行化异常
- 写偏斜（Write Skew）：两个事务读取重叠数据，各自写入不交子集
- 写环（Write Cycle）：事务通过读写依赖形成环

#### 5. 垃圾回收 / Garbage Collection

```
1. 找到最老的活跃快照时间戳 (minSnapshotTS)
2. 对每个键，移除 WriteTS < minSnapshotTS 的版本
3. 保留至少一个可见版本
4. 如果都不可见，完全移除

安全性：活跃事务都从 minSnapshotTS 或之后开始
        比 minSnapshotTS 旧版本对任何活跃事务都不可见
```

### 事务生命周期 / Transaction Lifecycle

```
事务开始 → 读取快照 → 写入(写集) → 提交 → 版本回收
    │          │           │           │         │
    │          │           │           │         └→ 标记版本为已提交
    │          │           │           └→ 冲突检测
    │          │           └→ 写入缓冲在写集中
    │          └→ 一致性视图
    └→ 分配时间戳
```

### 与两阶段锁定的对比 / Comparison with 2PL

| 特性 | MVCC | 两阶段锁定 (2PL) |
|------|------|-----------------|
| 读阻塞 | 从不阻塞 | 可能阻塞写 |
| 写阻塞 | 从不阻塞读 | 可能阻塞读 |
| 并发度 | 高 | 中 |
| 死锁 | 可能（需检测） | 常见 |
| 实现复杂度 | 中 | 中 |
| 垃圾回收 | 需要 | 不需要 |

---

## 运行测试 / Running Tests

```bash
# 运行所有测试
go test ./tests/...

# 运行特定测试
go test ./tests/ -run TestMVCCStorageWriteRead

# 运行测试并显示覆盖率
go test ./tests/ -cover

# 运行基准测试
go test ./tests/ -bench=.
```

### 测试覆盖 / Test Coverage

| 测试文件 | 覆盖内容 |
|----------|----------|
| `mvcc_test.go` | 事务生命周期、版本链、时间戳 |
| `conflict_test.go` | 冲突检测、等待图、死锁检测 |
| `gc_test.go` | 垃圾回收、快照注册 |
| `snapshot_test.go` | 快照管理器、事务管理 API |

---

## 核心循环 / Core Loop

```
事务开始 → 读取快照 → 写入 → 提交 → 版本回收
    │          │           │        │         │
    │          │           │        │         └→ 清理无用的旧版本
    │          │           │        └→ 检测冲突
    │          │           └→ 记录写集
    │          └→ 一致性视图
    └→ 分配唯一时间戳
```

---

## 参考 / References

- **《数据库系统概念》** - Abraham Silberschatz, Henry F. Korth, S. Sudarshan
- **MVCC: Multi-Version Concurrency Control** - PostgreSQL Documentation
- **Serializable Snapshot Isolation** - Byagavarthi et al., 2012
- **Snapshot Isation** - Terry, Hayes, and Lyon, 1995

---

## License

本项目仅用于学习目的 / This project is for educational purposes only.
