# 学习笔记：MVCC 并发控制

## 核心概念

### 什么是 MVCC？

MVCC（Multi-Version Concurrency Control）是一种并发控制方法，通过维护数据的多个版本来实现事务隔离。

**核心思想**:
- 每个写操作创建一个新版本，而不是覆盖旧版本
- 读操作根据时间戳读取特定版本
- 读写操作互不阻塞

### 为什么需要 MVCC？

**传统锁机制的问题**:
```
Writer 持有写锁 → Reader 必须等待
Reader 持有读锁 → Writer 必须等待
→ 系统吞吐量下降
```

**MVCC 的优势**:
```
Writer 写入新版本 → Reader 读取旧版本
→ 读写不阻塞 → 高并发
```

## 关键概念

### 1. 版本（Version）

每个数据项有多个版本：

```
Key: "balance"
  Version 1: $1000  (txn=1, ts=10)
  Version 2: $1500  (txn=2, ts=15)
  Version 3: $1200  (txn=3, ts=20)
```

### 2. 时间戳（Timestamp）

每个事务有两个时间戳：
- **Start Timestamp**: 事务开始时的快照时间戳
- **Commit Timestamp**: 事务提交时获得的时间戳

### 3. 快照（Snapshot）

事务在开始时获取一个一致性快照：
- 看到所有在 Start Timestamp 之前提交的事务的修改
- 看不到在 Start Timestamp 之后提交的事务的修改
- 看不到未提交事务的修改

### 4. 可见性（Visibility）

版本 V 对事务 T 可见的条件：
1. V.CreatedAt <= T.StartTimestamp
2. V 未被删除，或 V.DeletedAt > T.StartTimestamp
3. V.CreatedBy 已提交

### 5. 冲突（Conflict）

写写冲突：两个事务同时修改同一个 key

```
T1 (read_ts=1): Read(key) → v1
T2 (read_ts=2): Read(key) → v2
T1: Write(key, new_val) → Commit OK
T2: Write(key, another_val) → Commit FAIL (conflict)
```

## 实现细节

### 1. 版本存储

使用 `map[string][]*Version` 存储：

```go
type Store struct {
    versions map[string][]*Version  // key -> 版本链
}
```

**版本链按创建时间排序**，便于查找。

### 2. 读取操作

```go
func (s *Store) Get(key string, readTimestamp uint64) ([]byte, bool) {
    versions := s.versions[key]
    // 从最新版本向旧版本搜索
    for i := len(versions) - 1; i >= 0; i-- {
        v := versions[i]
        if v.IsVisible(readTimestamp) {
            return v.Value, true
        }
    }
    return nil, false
}
```

**优化**: 从最新版本开始搜索，通常能快速找到可见版本。

### 3. 写入操作

```go
func (s *Store) Put(key string, value []byte, txnID uint64, timestamp uint64) {
    version := &Version{
        Key:       key,
        Value:     value,
        CreatedBy: txnID,
        CreatedAt: timestamp,
        Status:    VersionActive,
    }
    s.versions[key] = append(s.versions[key], version)
}
```

**注意**: 写入操作创建新版本，不覆盖旧版本。

### 4. 删除操作

使用 tombstone（墓碑）标记删除：

```go
func (s *Store) Delete(key string, txnID uint64, timestamp uint64) bool {
    for i := len(versions) - 1; i >= 0; i-- {
        v := versions[i]
        if v.Status == VersionActive && v.CreatedAt <= timestamp {
            v.DeletedBy = txnID
            v.DeletedAt = timestamp
            v.Status = VersionDeleted
            return true
        }
    }
    return false
}
```

**注意**: 删除操作不直接删除版本，而是标记为已删除。

### 5. 冲突检测

```go
func (s *Store) HasConflict(key string, readTimestamp uint64, txnID uint64) bool {
    for _, v := range s.versions[key] {
        // 其他事务在本事务开始后写入了该 key
        if v.CreatedBy != txnID && v.CreatedAt > readTimestamp {
            return true
        }
    }
    return false
}
```

**时机**: 冲突检测在提交时进行。

### 6. 垃圾回收

```go
func (s *Store) RemoveVersions(minActiveTimestamp uint64) int {
    for key, versions := range s.versions {
        var remaining []*Version
        for _, v := range versions {
            if v.CreatedAt >= minActiveTimestamp || v.Status == VersionActive {
                remaining = append(remaining, v)
            } else {
                removed++
            }
        }
        s.versions[key] = remaining
    }
    return removed
}
```

**SafePoint**: min(所有活跃事务的 StartTimestamp)

## 隔离级别

### Read Uncommitted

最低隔离级别，允许读取未提交的数据。

### Read Committed

只读取已提交的数据。每个 SQL 语句使用新的快照。

### Repeatable Read

在整个事务期间使用相同的快照。可能出现幻读。

### Snapshot Isolation

MVCC 最常用的隔离级别：

**优点**:
- 读写不阻塞
- 一致性快照
- 避免脏读、不可重复读

**缺点**:
- 可能出现写偏斜（Write Skew）

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

## 常见问题

### Q: MVCC 的性能如何？

**A**: MVCC 的性能取决于：
- 版本链长度（越短越好）
- 冲突频率（越低越好）
- GC 频率（适中最好）

### Q: MVCC 的存储开销如何？

**A**: MVCC 需要存储多个版本，存储开销较大。但通过 GC 可以清理旧版本。

### Q: MVCC 适合什么场景？

**A**: MVCC 适合：
- 读多写少的场景
- 需要高并发的场景
- 需要一致性快照的场景

### Q: MVCC 不适合什么场景？

**A**: MVCC 不适合：
- 写多读少的场景（冲突频繁）
- 需要严格可序列化的场景
- 存储空间受限的场景

## 学习资源

### 论文

1. **"A Critique of ANSI SQL Isolation Levels"** - Berenson et al.
2. **"Serializable Isolation for Snapshot Databases"** - Fekete et al.

### 书籍

1. **"Designing Data-Intensive Applications"** - Martin Kleppmann
2. **"Database Internals"** - Alex Petrov

### 在线资源

- [PostgreSQL MVCC Documentation](https://www.postgresql.org/docs/current/mvcc.html)
- [CMU 15-445: Concurrency Control](https://15445.courses.cs.cmu.edu/)

## 总结

MVCC 是现代数据库系统的核心技术，通过：

1. **多版本存储**: 维护数据的历史版本
2. **快照隔离**: 每个事务看到一致的数据快照
3. **时间戳机制**: 使用时间戳确定版本可见性
4. **垃圾回收**: 定期清理不再需要的旧版本

实现了读写不阻塞的高并发访问，是构建高性能数据库系统的关键技术。
