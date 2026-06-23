# 01 - 研究笔记：MVCC 并发控制

## 什么是 MVCC？

MVCC（Multi-Version Concurrency Control，多版本并发控制）是一种数据库并发控制方法，通过维护数据的多个版本来实现事务隔离，使得读操作不需要等待写操作完成，写操作也不需要等待读操作完成。

## 历史背景

### 传统并发控制的问题

在传统的基于锁的并发控制中：

```
Writer 持有写锁期间：
  - 所有 Reader 必须等待
  - 其他 Writer 也必须等待
  - 导致系统吞吐量下降
```

### MVCC 的诞生

1978 年，David Reed 在其博士论文中提出了多版本并发控制的概念。随后被广泛应用于现代数据库系统：

- **PostgreSQL**: 完整的 MVCC 实现
- **MySQL (InnoDB)**: 基于 undo log 的 MVCC
- **Oracle**: 基于 undo 表空间的 MVCC
- **SQL Server**: 基于 tempdb 的快照隔离

## 核心原理

### 版本存储

每个数据项维护一个版本链：

```
Key: "account_balance"
┌──────────────────────────────────────────────┐
│ Version 1: $1000  │ txn_id=1  │ ts=100      │
│ Version 2: $1500  │ txn_id=2  │ ts=105      │
│ Version 3: $1200  │ txn_id=3  │ ts=110      │
└──────────────────────────────────────────────┘
```

### 时间戳机制

每个事务有两个时间戳：
- **Start Timestamp**: 事务开始时的快照时间戳
- **Commit Timestamp**: 事务提交时获得的时间戳

### 可见性规则

版本 V 对事务 T 可见的条件：
1. V.CreatedAt <= T.StartTimestamp（版本在事务开始前创建）
2. V 未被删除，或 V.DeletedAt > T.StartTimestamp（删除在事务开始后发生）
3. V.CreatedBy 已提交（创建该版本的事务已提交）

## 隔离级别

### Read Uncommitted

最低隔离级别，允许读取未提交的数据。MVCC 通常不实现此级别。

### Read Committed

只读取已提交的数据。每个 SQL 语句使用新的快照。

### Repeatable Read

在整个事务期间使用相同的快照。可能出现幻读。

### Snapshot Isolation

MVCC 最常用的隔离级别：

```
优点：
- 读写不阻塞
- 一致性快照
- 避免脏读、不可重复读

缺点：
- 可能出现写偏斜（Write Skew）
- 不是真正的可序列化
```

### Serializable

最高隔离级别，完全避免所有并发异常。

## 写偏斜问题

### 什么是写偏斜？

```
初始状态: account_A = 1000, account_B = 1000
约束: A + B >= 0

T1: 读取 A=1000, B=1000; 写入 A = A - 1500 = -500
T2: 读取 A=1000, B=1000; 写入 B = B - 1500 = -500

两个事务都成功，但 A + B = -1000，违反约束！
```

### 解决方案

1. **S2PL (Strict Two-Phase Locking)**: 使用锁防止写偏斜
2. **Serializable Snapshot Isolation (SSI)**: PostgreSQL 的实现
3. **Application-level locks**: 应用层加锁

## MVCC 实现方案

### 方案一：时间戳排序

使用物理时间戳或逻辑时间戳：

```go
type Version struct {
    Value     []byte
    Timestamp uint64
    TxnID     uint64
}
```

### 方案二：事务 ID

使用事务 ID 作为版本标识：

```go
type Version struct {
    Value    []byte
    CreateTx uint64  // 创建该版本的事务 ID
    DeleteTx uint64  // 删除该版本的事务 ID（0 表示未删除）
}
```

### 方案三：混合方案

结合时间戳和事务 ID：

```go
type Version struct {
    Value      []byte
    CreatedBy  uint64  // 创建事务 ID
    CreatedAt  uint64  // 创建时间戳
    DeletedBy  uint64  // 删除事务 ID
    DeletedAt  uint64  // 删除时间戳
}
```

## 存储方案

### 方案一：追加写入（Append-Only）

新版本追加到版本链末尾：

```
优点：写入性能好
缺点：读取需要遍历版本链
```

### 方案二：原地更新（In-Place Update）

旧版本移到 undo log，原位置写入新版本：

```
优点：读取性能好
缺点：需要额外的 undo log 管理
```

### 方案三：混合方案

热数据原地更新，冷数据追加写入。

## 垃圾回收

### 为什么需要 GC？

随着事务不断提交，旧版本会累积，占用存储空间。

### GC 策略

1. **基于时间戳的 GC**: 删除所有早于某个时间戳的版本
2. **基于活跃事务的 GC**: 删除不被任何活跃事务可见的版本
3. **惰性 GC**: 在读取时顺便清理
4. **后台 GC**: 定期运行的后台任务

### 安全回收点

```
SafePoint = min(所有活跃事务的 StartTimestamp)

所有 CreatedAt < SafePoint 的旧版本可以安全回收
```

## 实际应用

### PostgreSQL MVCC

```sql
-- 每行有 xmin 和 xmax
-- xmin: 创建该行的事务 ID
-- xmax: 删除该行的事务 ID（0 表示未删除）

SELECT xmin, xmax, * FROM users;
```

### MySQL InnoDB MVCC

```
-- 基于 undo log 实现
-- 每行有隐藏列: DB_TRX_ID, DB_ROLL_PTR
-- 读取时根据 undo log 构建历史版本
```

## 学习资源

### 论文

1. **"A Critique of ANSI SQL Isolation Levels"** - Berenson et al.
2. **"Serializable Isolation for Snapshot Databases"** - Fekete et al.
3. **"High-Performance Concurrency Control Mechanisms for Main-Memory Databases"** - PLV85

### 书籍

1. **"Designing Data-Intensive Applications"** - Martin Kleppmann, Chapter 7
2. **"Database Internals"** - Alex Petrov, Chapter 6
3. **"Transaction Processing: Concepts and Techniques"** - Gray & Reuter

### 在线资源

- [PostgreSQL MVCC Documentation](https://www.postgresql.org/docs/current/mvcc.html)
- [CMU 15-445: Concurrency Control](https://15445.courses.cs.cmu.edu/)
- [Jepsen: Consistency Models](https://jepsen.io/consistency)

## 总结

MVCC 是现代数据库系统的核心技术之一，通过：

1. **多版本存储**: 维护数据的历史版本
2. **快照隔离**: 每个事务看到一致的数据快照
3. **时间戳机制**: 使用时间戳确定版本可见性
4. **垃圾回收**: 定期清理不再需要的旧版本

实现了读写不阻塞的高并发访问，是构建高性能数据库系统的关键技术。
