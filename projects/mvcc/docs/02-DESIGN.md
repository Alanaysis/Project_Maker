# 02 - 设计文档：MVCC 并发控制

## 设计目标

1. **正确性**: 保证快照隔离的正确性
2. **性能**: 读写操作尽量不阻塞
3. **可扩展性**: 支持并发事务
4. **可理解性**: 代码清晰，易于学习

## 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                       MVCC Engine                           │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                   Transaction Layer                    │  │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌────────┐  │  │
│  │  │  Txn 1  │  │  Txn 2  │  │  Txn 3  │  │  Txn N │  │  │
│  │  └────┬────┘  └────┬────┘  └────┬────┘  └───┬────┘  │  │
│  │       │            │            │            │        │  │
│  │  ┌────┴────────────┴────────────┴────────────┴────┐  │  │
│  │  │            Transaction Manager                  │  │  │
│  │  │  • 事务生命周期管理                               │  │  │
│  │  │  • 时间戳分配                                    │  │  │
│  │  │  • 活跃事务跟踪                                  │  │  │
│  │  └────────────────────┬───────────────────────────┘  │  │
│  └───────────────────────┼──────────────────────────────┘  │
│                          │                                  │
│  ┌───────────────────────┴──────────────────────────────┐  │
│  │                   Storage Layer                        │  │
│  │  ┌────────────────────────────────────────────────┐  │  │
│  │  │                 Version Store                    │  │  │
│  │  │  ┌──────────────────────────────────────────┐  │  │  │
│  │  │  │ Key: "balance"                           │  │  │  │
│  │  │  │   ┌────────────────────────────────────┐ │  │  │  │
│  │  │  │   │ v1: $1000  txn=1  ts=10            │ │  │  │  │
│  │  │  │   │ v2: $1500  txn=2  ts=15            │ │  │  │  │
│  │  │  │   │ v3: $1200  txn=3  ts=20            │ │  │  │  │
│  │  │  │   └────────────────────────────────────┘ │  │  │  │
│  │  │  └──────────────────────────────────────────┘  │  │  │
│  │  └────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Garbage Collection Layer                  │  │
│  │  • 定期扫描旧版本                                      │  │
│  │  • 基于 SafePoint 回收                                 │  │
│  │  • 后台异步执行                                        │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## 核心组件设计

### 1. Version（版本）

```go
type Version struct {
    Key       string
    Value     []byte
    CreatedBy uint64        // 创建该版本的事务 ID
    CreatedAt uint64        // 创建时间戳
    DeletedBy uint64        // 删除该版本的事务 ID（0 表示未删除）
    DeletedAt uint64        // 删除时间戳（0 表示未删除）
    Status    VersionStatus // Active, Deleted, Garbage
}
```

**设计决策**:
- 使用事务 ID + 时间戳的混合方案
- 支持逻辑删除（tombstone）
- 版本状态追踪便于 GC

### 2. Store（存储）

```go
type Store struct {
    mu       sync.RWMutex
    versions map[string][]*Version
}
```

**核心操作**:
- `Put(key, value, txnID, timestamp)`: 写入新版本
- `Get(key, readTimestamp)`: 读取指定时间戳的版本
- `Delete(key, txnID, timestamp)`: 标记删除
- `HasConflict(key, readTimestamp, txnID)`: 检测写写冲突
- `RemoveVersions(minTimestamp)`: GC 清理旧版本

**并发控制**:
- 使用 `sync.RWMutex` 保护并发访问
- 读操作使用读锁，写操作使用写锁

### 3. Transaction（事务）

```go
type Transaction struct {
    ID              uint64
    StartTimestamp  uint64
    CommitTimestamp uint64
    Status          TxnStatus
    ReadSet         map[string]uint64
    WriteSet        map[string]WriteRecord
}
```

**设计决策**:
- 维护 ReadSet 和 WriteSet 用于冲突检测
- 写操作先缓冲，提交时才应用到 Store
- 支持读己之写（Read-Your-Own-Writes）

### 4. TransactionManager（事务管理器）

```go
type TransactionManager struct {
    clock         uint64
    activeTxns    map[uint64]*Transaction
    committedTxns map[uint64]*Transaction
    minActiveTS   uint64
}
```

**核心职责**:
- 分配唯一事务 ID 和时间戳
- 管理事务生命周期（Begin, Commit, Abort）
- 维护活跃事务列表
- 计算 SafePoint 用于 GC

### 5. GarbageCollector（垃圾回收器）

```go
type GarbageCollector struct {
    store    *Store
    txMgr    *TransactionManager
    interval time.Duration
    stats    GCStats
}
```

**回收策略**:
```
SafePoint = min(所有活跃事务的 StartTimestamp)

对于每个版本 V:
  if V.CreatedAt < SafePoint 且 V.Status != Active:
    删除 V
```

## 关键流程设计

### 读操作流程

```
Read(key, readTimestamp)
    │
    ├─ 1. 检查 WriteSet（读己之写）
    │     └─ 如果找到，返回 WriteSet 中的值
    │
    └─ 2. 从 Store 读取
          └─ 遍历版本链，找到满足以下条件的版本：
              • CreatedAt <= readTimestamp
              • Status == Active
              • (DeletedAt == 0 或 DeletedAt > readTimestamp)
```

### 写操作流程

```
Write(key, value)
    │
    └─ 缓冲到 WriteSet
       （不直接修改 Store）
```

### 提交流程

```
Commit()
    │
    ├─ 1. 冲突检测
    │     └─ 对 WriteSet 中的每个 key:
    │         └─ 检查是否有其他事务在 [StartTS, +∞) 写入了该 key
    │
    ├─ 2. 获取 CommitTimestamp
    │
    └─ 3. 应用写入
          └─ 对 WriteSet 中的每个 key:
              ├─ 如果是 Delete: Store.Delete(key, txnID, commitTS)
              └─ 如果是 Put: Store.Put(key, value, txnID, commitTS)
```

## 时间戳设计

### 逻辑时钟 vs 物理时钟

本实现使用**逻辑时钟**（原子递增计数器）：

```go
func (tm *TransactionManager) AllocateTimestamp() uint64 {
    return atomic.AddUint64(&tm.clock, 1)
}
```

**优点**:
- 严格递增，保证因果序
- 无需 NTP 同步
- 实现简单

**缺点**:
- 不反映真实时间
- 单点瓶颈（生产环境需要分布式时钟）

### 时间戳分配策略

| 操作 | 时间戳 |
|------|--------|
| Begin | 新分配一个时间戳作为 StartTimestamp |
| Commit | 新分配一个时间戳作为 CommitTimestamp |

## 冲突检测设计

### 乐观并发控制 (OCC)

```
读阶段: 读取数据并记录到 ReadSet
验证阶段: 检查 ReadSet 中的数据是否被其他事务修改
写阶段: 如果验证通过，应用写入
```

### 写写冲突检测

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

## 并发安全设计

### 锁策略

```
Store:
  - 读操作: RLock (允许并发读)
  - 写操作: Lock (独占写)

TransactionManager:
  - Begin/Commit/Abort: Lock
  - 查询操作: RLock

Transaction:
  - 读操作: RLock
  - 写操作: Lock
```

### 死锁预防

- 锁的获取顺序固定：Transaction → Store
- 不在持锁时等待其他资源
- 使用超时机制（可选）

## 扩展性考虑

### 分布式扩展

在分布式环境中，需要考虑：
1. **分布式时间戳**: 使用 TrueTime (Google) 或 HLC (Hybrid Logical Clock)
2. **分布式事务**: 2PC 或 Paxos
3. **数据分片**: 按 key 范围或 hash 分片

### 性能优化

1. **版本链压缩**: 合并不必要的中间版本
2. **索引优化**: 使用 B+ 树或 LSM 树存储版本
3. **批量提交**: 合并多个小事务
4. **读写分离**: 主从复制

## 设计权衡

| 决策 | 选择 | 理由 |
|------|------|------|
| 时间戳类型 | 逻辑时钟 | 简单可靠，适合学习 |
| 存储结构 | 内存 map | 简化实现，聚焦 MVCC 逻辑 |
| 冲突检测 | 乐观并发控制 | 读多写少场景性能好 |
| GC 策略 | 后台定期回收 | 平衡性能和空间 |
| 版本存储 | 追加写入 | 简单，写入性能好 |
