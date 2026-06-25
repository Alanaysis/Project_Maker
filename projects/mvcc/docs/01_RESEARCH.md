# 01 - 技术调研: MVCC 并发控制

## 1. 什么是 MVCC

MVCC (Multi-Version Concurrency Control, 多版本并发控制) 是一种数据库并发控制方法。
它通过维护数据的多个版本来实现事务隔离，允许读操作和写操作并发执行而不互相阻塞。

### 核心思想

```
传统锁机制:  读写互斥，写写互斥
MVCC:        读写不互斥，写写通过冲突检测处理

┌─────────────────────────────────────────────────┐
│                  MVCC 核心思想                    │
│                                                   │
│   事务 A (读)          事务 B (写)               │
│   ┌──────────┐        ┌──────────┐              │
│   │ 快照 ts=5 │        │ 写缓冲    │              │
│   │          │        │          │              │
│   │ 读取 v3  │        │ 写入 v4  │              │
│   │ (不阻塞) │        │ (不阻塞) │              │
│   └──────────┘        └──────────┘              │
│         │                    │                    │
│         ▼                    ▼                    │
│   看到 ts=5 时刻         提交时检测冲突           │
│   的一致视图                                      │
└─────────────────────────────────────────────────┘
```

## 2. 重要论文和里程碑

| 年份 | 论文/系统 | 贡献 |
|------|----------|------|
| 1978 | Reed, "Naming and Synchronization" | 首次提出多版本概念 |
| 1981 | Bernstein & Goodman, "Multiversion Concurrency Control" | MVCC 理论基础 |
| 1987 | O'Neil, "The Escrow Transactional Method" | 乐观并发控制 |
| 1992 | Berenson et al., "A Critique of ANSI SQL Isolation Levels" | 快照隔离分析 |
| 1995 | PostgreSQL 6.0 | 首个使用 MVCC 的开源数据库 |
| 2006 | Oracle 9i+ | 商业 MVCC 实现 |
| 2015 | Hekaton (SQL Server) | 内存 MVCC 实现 |

## 3. 真实数据库中的 MVCC

### PostgreSQL

```
PostgreSQL MVCC 架构:
┌─────────────────────────────────────────┐
│              PostgreSQL                  │
│                                          │
│  Heap Tuple:                            │
│  ┌─────────────────────────────────┐    │
│  │ xmin (创建事务) | xmax (删除事务) │    │
│  │ data ...                        │    │
│  └─────────────────────────────────┘    │
│                                          │
│  读取时: xmin <= 当前快照 < xmax         │
│  旧版本通过 VACUUM 清理                   │
└─────────────────────────────────────────┘
```

### MySQL InnoDB

```
InnoDB MVCC 架构:
┌─────────────────────────────────────────┐
│              InnoDB                      │
│                                          │
│  Undo Log:                              │
│  ┌─────────────────────────────────┐    │
│  │ 当前版本 ──→ Undo Log 版本链    │    │
│  │ (聚簇索引)    (回滚段)           │    │
│  └─────────────────────────────────┘    │
│                                          │
│  Read View: 事务开始时创建                │
│  通过 Read View 判断版本可见性            │
└─────────────────────────────────────────┘
```

## 4. MVCC vs 其他并发控制

| 特性 | MVCC | 2PL (两阶段锁) | OCC (乐观并发控制) |
|------|------|----------------|-------------------|
| 读写冲突 | 无阻塞 | 读阻塞写 | 无阻塞 |
| 写写冲突 | 提交时检测 | 加锁阻塞 | 验证时检测 |
| 死锁 | 无 | 可能 | 无 |
| 实现复杂度 | 高 | 中 | 中 |
| 存储开销 | 高(多版本) | 低 | 中 |
| 适用场景 | 读多写少 | 通用 | 冲突少 |

## 5. 快照隔离 (Snapshot Isolation)

快照隔离是 MVCC 最常用的隔离级别:

```
快照隔离规则:
┌─────────────────────────────────────────────────┐
│ 1. 每个事务在开始时获取数据库快照                  │
│ 2. 所有读操作基于快照进行（一致性视图）             │
│ 3. 写入先缓存在写缓冲中                          │
│ 4. 提交时检测冲突（写写冲突、读写冲突）            │
│ 5. 无冲突则提交，有冲突则中止                     │
└─────────────────────────────────────────────────┘
```

### 可见性规则

```
版本 V 对事务 T 可见，当且仅当:
  1. V.create_txn 已提交
  2. V.create_ts <= T.snapshot_ts
  3. V.create_txn 不在 T.snapshot.active_txns 中
  4. V 未被删除，或删除操作在快照之后
```

## 6. 冲突检测策略

### 写写冲突 (Write-Write Conflict)

```
时间线:
  T1: BEGIN ──WRITE(K)──COMMIT──────────→
  T2: BEGIN ──WRITE(K)──────COMMIT(冲突!)→

检测: T2 提交时发现 K 已被 T1 在 T2 开始后修改
策略: First-Writer-Wins (先提交者获胜)
```

### 读写冲突 (Write Skew)

```
时间线:
  T1: READ(A) READ(B) ──WRITE(A)──COMMIT──→
  T2: READ(A) READ(B) ──WRITE(B)──COMMIT(冲突!)→

检测: T2 读取的 A 被 T1 修改
经典案例: 两个医生同时请假，导致无人值班
```

## 7. 垃圾回收

旧版本需要清理以释放空间:

```
GC 策略:
┌─────────────────────────────────────────┐
│ 安全点 = min(活跃事务的开始时间戳)        │
│                                          │
│ 清理条件:                                │
│   版本.create_ts < 安全点                 │
│   且 版本已被删除                         │
│   且 删除事务已提交                       │
│                                          │
│ 保留: 至少保留最新版本                    │
└─────────────────────────────────────────┘
```

## 8. 参考资料

- Berenson, H., et al. (1995). "A Critique of ANSI SQL Isolation Levels."
- Mohan, C., et al. (1992). "ARIES: A Transaction Recovery Method."
- PostgreSQL Documentation: "MVCC (Multi-Version Concurrency Control)"
- MySQL Documentation: "InnoDB Multi-Versioning"
- Wu, Y., et al. (2017). "An Empirical Evaluation of In-Memory Multi-Version Concurrency Control."
