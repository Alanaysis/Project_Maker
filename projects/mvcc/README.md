# MVCC 并发控制

## 项目概述

这是一个学习多版本并发控制（Multi-Version Concurrency Control, MVCC）的项目。MVCC 是现代数据库系统中最常用的并发控制机制之一，通过维护数据的多个版本来实现事务隔离，避免读写冲突。

## 学习目标

- 理解 MVCC 的核心原理和设计思想
- 掌握快照隔离（Snapshot Isolation）的实现方式
- 学会版本管理和垃圾回收机制
- 了解乐观并发控制（OCC）与写写冲突检测

## 技术栈

- **语言**: Go 1.21+
- **框架**: 无（纯标准库实现）
- **测试**: Go 标准测试框架

## 项目结构

```
mvcc/
├── README.md
├── docs/                        # 学习文档
│   ├── 01-RESEARCH.md          # 研究笔记
│   ├── 02-DESIGN.md            # 设计文档
│   ├── 03-IMPLEMENTATION.md    # 实现细节
│   ├── 04-TESTING.md           # 测试文档
│   └── 05-DEVELOPMENT.md       # 开发日志
├── LEARNING_NOTES.md            # 学习笔记
├── cmd/                         # 示例程序
│   └── main.go
├── internal/                    # 内部实现
│   ├── mvcc.go                 # MVCC 引擎
│   ├── store/                   # 版本存储
│   │   ├── version.go
│   │   └── version_test.go
│   ├── transaction/             # 事务管理
│   │   ├── transaction.go
│   │   └── transaction_test.go
│   └── gc/                      # 垃圾回收
│       ├── garbage_collector.go
│       └── garbage_collector_test.go
└── test/                        # 集成测试
    └── mvcc_test.go
```

## 核心概念

### MVCC 工作原理

MVCC 的核心思想是：**读操作不阻塞写操作，写操作不阻塞读操作**。

```
传统锁机制:          MVCC:
Writer -----> Block  Writer -----> Write v2
Reader -----> Wait   Reader -----> Read v1 (snapshot)
```

### 快照隔离（Snapshot Isolation）

每个事务在开始时获取一个**快照时间戳**，之后的所有读操作都基于这个快照：

```
T1 (snapshot=5):     T2 (snapshot=8):
  Read(key) → v5       Read(key) → v8
  即使 T2 在 T1       T2 看不到 T1 之后
  期间提交了新版本      的修改
```

### 版本链

每个 key 维护一个版本链，按创建时间排序：

```
key: "balance"
  ┌─────────────────────────────────────┐
  │ v1: 1000  (txn=1, ts=1)            │
  │ v2: 1500  (txn=2, ts=3)            │
  │ v3: 1200  (txn=3, ts=5) ← current │
  └─────────────────────────────────────┘
```

### 写写冲突检测

使用乐观并发控制（OCC）检测写写冲突：

```
T1 (read_ts=1):      T2 (read_ts=2):
  Read(key) → v1       Read(key) → v2
  Write(key, newVal)
  Commit OK!
                       Write(key, another)
                       Commit FAIL! (conflict)
```

## 快速开始

### 运行示例

```bash
cd projects/mvcc
go run cmd/main.go
```

### 运行测试

```bash
# 运行所有测试
go test ./...

# 运行特定包的测试
go test ./internal/store/...
go test ./internal/transaction/...
go test ./internal/gc/...
go test ./test/...

# 运行测试并显示详细信息
go test -v ./...
```

## API 示例

### 基本用法

```go
package main

import (
    "fmt"
    "mvcc/internal"
)

func main() {
    // 创建 MVCC 引擎
    engine := internal.NewMVSSEngine()

    // 开始事务并写入数据
    txn1 := engine.Begin()
    txn1.Write("name", []byte("Alice"))
    txn1.Write("age", []byte("30"))
    txn1.Commit()

    // 新事务读取数据
    txn2 := engine.Begin()
    name, _ := txn2.Read("name")
    age, _ := txn2.Read("age")
    fmt.Printf("name=%s, age=%s\n", string(name), string(age))
    txn2.Commit()
}
```

### 快照隔离示例

```go
// T1 开始（快照时间戳 = 5）
t1 := engine.Begin()

// T2 修改数据并提交
t2 := engine.Begin()
t2.Write("x", []byte("new_value"))
t2.Commit()

// T1 仍然看到旧值（快照隔离）
val, _ := t1.Read("x")  // 返回旧值
t1.Commit()
```

### 写写冲突检测

```go
// 两个事务同时读取同一个 key
t1 := engine.Begin()
t2 := engine.Begin()

t1.Read("account")
t2.Read("account")

// T1 先写入并提交
t1.Write("account", []byte("1100"))
t1.Commit() // 成功

// T2 后写入并提交 - 检测到冲突
t2.Write("account", []byte("900"))
err := t2.Commit() // 返回冲突错误
```

### 删除操作

```go
txn := engine.Begin()
txn.Delete("key_to_remove")
txn.Commit()

// 新事务读取 - 返回未找到
newTxn := engine.Begin()
_, ok := newTxn.Read("key_to_remove") // ok = false
newTxn.Commit()
```

### 并发事务

```go
var wg sync.WaitGroup
for i := 0; i < 100; i++ {
    wg.Add(1)
    go func(id int) {
        defer wg.Done()
        txn := engine.Begin()
        txn.Write(fmt.Sprintf("key_%d", id), []byte("value"))
        txn.Commit()
    }(i)
}
wg.Wait()
```

## 架构设计

```
┌─────────────────────────────────────────────────┐
│                  MVCC Engine                     │
│  ┌─────────────┐  ┌──────────┐  ┌──────────┐  │
│  │    Store     │  │   Txn    │  │    GC    │  │
│  │  (Versions)  │  │ Manager  │  │ Collector│  │
│  └──────┬──────┘  └────┬─────┘  └────┬─────┘  │
│         │              │              │         │
│  ┌──────┴──────────────┴──────────────┴──────┐ │
│  │              Transaction Context           │ │
│  │  Begin → Read → Write → Commit/Abort      │ │
│  └───────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

### 组件说明

| 组件 | 职责 |
|------|------|
| **Store** | 管理 key-value 的多版本存储 |
| **Transaction Manager** | 分配时间戳，管理事务生命周期 |
| **GC** | 回收不再被任何活跃事务可见的旧版本 |
| **Transaction** | 封装事务操作，提供读写接口 |

## 核心循环

```
事务开始 → 读取快照 → 写入 → 提交 → 版本回收
   │          │        │       │        │
   │          │        │       │        └── GC 清理旧版本
   │          │        │       └────────── 冲突检测 + 时间戳分配
   │          │        └────────────────── 缓冲写入
   │          └─────────────────────────── 基于快照时间戳读取
   └────────────────────────────────────── 获取唯一事务 ID 和快照时间戳
```

## 参考资源

- [A Critique of ANSI SQL Isolation Levels](https://arxiv.org/abs/cs/0701157)
- [Serializable Isolation for Snapshot Databases](https://www.cs.cmu.edu/~natassa/courses/15-721/papers/p2100-Fekete.pdf)
- [PostgreSQL MVCC Documentation](https://www.postgresql.org/docs/current/mvcc.html)
- [Designing Data-Intensive Applications - Chapter 7](https://dataintensive.net/)

## 许可证

MIT License

---

[返回主目录](../../README.md)
