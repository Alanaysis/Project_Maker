# 03 - 实现细节

## 文件结构

```
internal/
├── mvcc.go                    # MVCC 引擎主入口
├── store/
│   ├── version.go            # 版本存储实现
│   └── version_test.go       # 存储层测试
├── transaction/
│   ├── transaction.go        # 事务管理实现
│   └── transaction_test.go   # 事务层测试
└── gc/
    ├── garbage_collector.go  # 垃圾回收实现
    └── garbage_collector_test.go  # GC 测试
```

## 核心实现

### 1. Version 存储层 (`store/version.go`)

#### 数据结构

```go
type Version struct {
    Key       string
    Value     []byte
    CreatedBy uint64        // 创建事务 ID
    CreatedAt uint64        // 创建时间戳
    DeletedBy uint64        // 删除事务 ID
    DeletedAt uint64        // 删除时间戳
    Status    VersionStatus // Active, Deleted, Garbage
}

type Store struct {
    mu       sync.RWMutex
    versions map[string][]*Version  // key -> 版本链
}
```

#### 可见性判断

```go
func (v *Version) IsVisible(readTimestamp uint64) bool {
    // 1. 版本状态不能是 Garbage
    if v.Status == VersionGarbage {
        return false
    }
    // 2. 版本必须在读时间戳之前创建
    if v.CreatedAt > readTimestamp {
        return false
    }
    // 3. 如果已删除，删除时间必须在读时间戳之后
    if v.DeletedAt > 0 && v.DeletedAt <= readTimestamp {
        return false
    }
    return true
}
```

#### 读取操作

```go
func (s *Store) Get(key string, readTimestamp uint64) ([]byte, bool) {
    s.mu.RLock()
    defer s.mu.RUnlock()

    versions := s.versions[key]
    // 从最新版本向旧版本搜索
    for i := len(versions) - 1; i >= 0; i-- {
        v := versions[i]
        if v.IsVisible(readTimestamp) && v.Status == VersionActive {
            return v.Value, true
        }
    }
    return nil, false
}
```

**优化点**: 从最新版本开始搜索，通常能快速找到可见版本。

#### 冲突检测

```go
func (s *Store) HasConflict(key string, readTimestamp uint64, txnID uint64) bool {
    s.mu.RLock()
    defer s.mu.RUnlock()

    versions := s.versions[key]
    for _, v := range versions {
        // 其他事务在本事务开始后写入了该 key
        if v.CreatedBy != txnID && v.CreatedAt > readTimestamp && v.Status == VersionActive {
            return true
        }
    }
    return false
}
```

### 2. 事务管理器 (`transaction/transaction.go`)

#### 事务结构

```go
type Transaction struct {
    ID              uint64
    StartTimestamp  uint64
    CommitTimestamp uint64
    Status          TxnStatus
    ReadSet         map[string]uint64      // key -> 读时间戳
    WriteSet        map[string]WriteRecord  // key -> 写记录
}
```

#### 时间戳分配

```go
type TransactionManager struct {
    clock         uint64  // 原子递增的逻辑时钟
    activeTxns    map[uint64]*Transaction
    committedTxns map[uint64]*Transaction
    minActiveTS   uint64
}

func (tm *TransactionManager) AllocateTimestamp() uint64 {
    return atomic.AddUint64(&tm.clock, 1)
}
```

#### 事务生命周期

```go
// 开始事务
func (tm *TransactionManager) Begin() *Transaction {
    ts := tm.AllocateTimestamp()
    txn := NewTransaction(ts, ts)
    tm.activeTxns[txn.ID] = txn
    tm.updateMinActiveTS()
    return txn
}

// 提交事务
func (tm *TransactionManager) Commit(txnID uint64) (uint64, error) {
    txn := tm.activeTxns[txnID]
    commitTS := tm.AllocateTimestamp()
    txn.CommitTimestamp = commitTS
    txn.Status = TxnCommitted
    delete(tm.activeTxns, txnID)
    tm.committedTxns[txnID] = txn
    tm.updateMinActiveTS()
    return commitTS, nil
}

// 中止事务
func (tm *TransactionManager) Abort(txnID uint64) error {
    txn := tm.activeTxns[txnID]
    txn.Status = TxnAborted
    delete(tm.activeTxns, txnID)
    tm.updateMinActiveTS()
    return nil
}
```

#### SafePoint 计算

```go
func (tm *TransactionManager) updateMinActiveTS() {
    if len(tm.activeTxns) == 0 {
        tm.minActiveTS = tm.CurrentTimestamp()
        return
    }
    minTS := uint64(^uint64(0))
    for _, txn := range tm.activeTxns {
        if txn.StartTimestamp < minTS {
            minTS = txn.StartTimestamp
        }
    }
    tm.minActiveTS = minTS
}
```

### 3. 垃圾回收器 (`gc/garbage_collector.go`)

#### GC 流程

```go
func (gc *GarbageCollector) Run() int {
    // 1. 获取 SafePoint
    minActiveTS := gc.txMgr.MinActiveTimestamp()

    // 2. 清理旧版本
    removed := gc.store.RemoveVersions(minActiveTS)

    // 3. 更新统计信息
    gc.stats.TotalRuns++
    gc.stats.TotalRemoved += uint64(removed)

    return removed
}
```

#### 版本清理逻辑

```go
func (s *Store) RemoveVersions(minActiveTimestamp uint64) int {
    removed := 0
    for key, versions := range s.versions {
        var remaining []*Version
        for _, v := range versions {
            // 保留可能仍被活跃事务需要的版本
            if v.CreatedAt >= minActiveTimestamp || v.Status == VersionActive {
                remaining = append(remaining, v)
            } else {
                removed++
            }
        }
        if len(remaining) == 0 {
            delete(s.versions, key)
        } else {
            s.versions[key] = remaining
        }
    }
    return removed
}
```

### 4. MVCC 引擎 (`mvcc.go`)

#### 引擎结构

```go
type MVSSEngine struct {
    store *store.Store
    txMgr *transaction.TransactionManager
    gc    *gc.GarbageCollector
}
```

#### 事务操作封装

```go
// 读操作：先检查 WriteSet，再读 Store
func (t *Transaction) Read(key string) ([]byte, bool) {
    // 1. 检查写集（读己之写）
    if wr, ok := t.txn.GetWrite(key); ok {
        if wr.IsDelete {
            return nil, false
        }
        return wr.Value, true
    }
    // 2. 从 Store 读取快照
    value, found := t.engine.store.Get(key, t.txn.StartTimestamp)
    if found {
        t.txn.AddRead(key, t.txn.StartTimestamp)
    }
    return value, found
}

// 提交操作：验证 + 应用
func (t *Transaction) Commit() error {
    // 1. 冲突检测
    for key := range t.txn.WriteSet {
        if t.engine.store.HasConflict(key, t.txn.StartTimestamp, t.txn.ID) {
            t.engine.txMgr.Abort(t.txn.ID)
            return fmt.Errorf("write-write conflict on key %q", key)
        }
    }
    // 2. 获取提交时间戳
    commitTS, _ := t.engine.txMgr.Commit(t.txn.ID)
    // 3. 应用写入
    for key, wr := range t.txn.WriteSet {
        if wr.IsDelete {
            t.engine.store.Delete(key, t.txn.ID, commitTS)
        } else {
            t.engine.store.Put(key, wr.Value, t.txn.ID, commitTS)
        }
    }
    return nil
}
```

## 关键实现细节

### 1. 读己之写（Read-Your-Own-Writes）

在事务内部，写操作先缓冲到 WriteSet，读操作需要先检查 WriteSet：

```go
// 在 WriteSet 中的值优先于 Store 中的值
if wr, ok := t.txn.GetWrite(key); ok {
    return wr.Value, true
}
```

### 2. 冲突检测时机

冲突检测在**提交时**进行，而不是写入时：

```go
func (t *Transaction) Commit() error {
    for key := range t.txn.WriteSet {
        if t.engine.store.HasConflict(key, t.txn.StartTimestamp, t.txn.ID) {
            // 冲突：其他事务在我们开始后修改了该 key
            return error
        }
    }
    // 无冲突，应用写入
}
```

### 3. 逻辑删除（Tombstone）

删除操作不直接删除版本，而是标记为已删除：

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

### 4. 并发安全

使用 `sync.RWMutex` 保护共享数据：

```go
type Store struct {
    mu       sync.RWMutex
    versions map[string][]*Version
}

// 读操作使用读锁
func (s *Store) Get(...) {
    s.mu.RLock()
    defer s.mu.RUnlock()
    // ...
}

// 写操作使用写锁
func (s *Store) Put(...) {
    s.mu.Lock()
    defer s.mu.Unlock()
    // ...
}
```

## 性能考虑

### 当前实现的局限

1. **内存存储**: 所有数据存储在内存中，重启丢失
2. **全表扫描**: 版本搜索是 O(n) 复杂度
3. **全局锁**: Store 使用全局读写锁

### 优化方向

1. **持久化存储**: 使用 B+ 树或 LSM 树
2. **索引优化**: 为版本链建立索引
3. **分段锁**: 按 key 范围分段加锁
4. **版本压缩**: 合并不必要的中间版本

## 测试策略

### 单元测试

- Store 层：测试读写、可见性、冲突检测
- Transaction 层：测试事务生命周期、并发安全
- GC 层：测试回收逻辑、统计信息

### 集成测试

- MVCC 引擎：测试完整的事务流程
- 并发测试：多事务并发读写
- 隔离级别测试：验证快照隔离

### 边界测试

- 空 Store 读取
- 同一 key 的多次写入
- 事务中止后的可见性
- GC 清理后的版本链
