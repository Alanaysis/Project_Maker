# 05 - 开发日志

## 开发计划

### 阶段 1: 核心存储层
- [x] 实现 Version 数据结构
- [x] 实现 Store 基本读写
- [x] 实现多版本管理
- [x] 实现删除（tombstone）
- [x] 实现可见性判断
- [x] 实现冲突检测

### 阶段 2: 事务管理
- [x] 实现 Transaction 结构
- [x] 实现 TransactionManager
- [x] 实现时间戳分配
- [x] 实现事务生命周期（Begin/Commit/Abort）
- [x] 实现 ReadSet/WriteSet
- [x] 实现 SafePoint 计算

### 阶段 3: 垃圾回收
- [x] 实现 GarbageCollector
- [x] 实现基于 SafePoint 的回收
- [x] 实现统计信息
- [x] 实现后台运行

### 阶段 4: MVCC 引擎
- [x] 实现 MVSSEngine
- [x] 封装事务操作
- [x] 实现读己之写
- [x] 实现提交验证

### 阶段 5: 测试与文档
- [x] 编写单元测试
- [x] 编写集成测试
- [x] 编写文档
- [x] 编写示例程序

## 开发记录

### 2026-06-22: 项目初始化

创建项目结构：
- 创建目录结构
- 初始化 Go 模块
- 创建基础文件

### 2026-06-22: 实现存储层

实现 `internal/store/version.go`:

**Version 结构体**:
```go
type Version struct {
    Key       string
    Value     []byte
    CreatedBy uint64
    CreatedAt uint64
    DeletedBy uint64
    DeletedAt uint64
    Status    VersionStatus
}
```

**关键实现**:
- `IsVisible(readTimestamp)`: 可见性判断
- `Put(key, value, txnID, timestamp)`: 写入新版本
- `Get(key, readTimestamp)`: 读取指定版本
- `Delete(key, txnID, timestamp)`: 逻辑删除
- `HasConflict(key, readTimestamp, txnID)`: 冲突检测
- `RemoveVersions(minTimestamp)`: GC 清理

**设计决策**:
- 使用 `sync.RWMutex` 保护并发访问
- 版本链按创建时间排序
- 从最新版本向旧版本搜索

### 2026-06-22: 实现事务管理

实现 `internal/transaction/transaction.go`:

**Transaction 结构体**:
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

**关键实现**:
- `Begin()`: 创建新事务
- `Commit(txnID)`: 提交事务
- `Abort(txnID)`: 中止事务
- `AllocateTimestamp()`: 时间戳分配
- `updateMinActiveTS()`: SafePoint 计算

**设计决策**:
- 使用原子操作分配时间戳
- 维护活跃事务和已提交事务列表
- SafePoint = min(活跃事务的 StartTimestamp)

### 2026-06-22: 实现垃圾回收

实现 `internal/gc/garbage_collector.go`:

**GarbageCollector 结构体**:
```go
type GarbageCollector struct {
    store    *Store
    txMgr    *TransactionManager
    interval time.Duration
    stats    GCStats
}
```

**关键实现**:
- `Start()`: 启动后台 GC
- `Stop()`: 停止 GC
- `Run()`: 执行一次 GC
- `Stats()`: 获取统计信息

**回收策略**:
```
SafePoint = min(活跃事务的 StartTimestamp)

对于每个版本 V:
  if V.CreatedAt < SafePoint 且 V.Status != Active:
    删除 V
```

### 2026-06-22: 实现 MVCC 引擎

实现 `internal/mvcc.go`:

**MVSSEngine 结构体**:
```go
type MVSSEngine struct {
    store *store.Store
    txMgr *transaction.TransactionManager
    gc    *gc.GarbageCollector
}
```

**关键实现**:
- `Begin()`: 开始事务
- `Read(key)`: 读取数据
- `Write(key, value)`: 写入数据
- `Delete(key)`: 删除数据
- `Commit()`: 提交事务
- `Abort()`: 中止事务

**设计决策**:
- 写操作先缓冲到 WriteSet
- 读操作先检查 WriteSet（读己之写）
- 提交时验证冲突

### 2026-06-22: 编写测试

编写测试文件：

**Store 层测试** (`store/version_test.go`):
- 基本读写测试
- 多版本测试
- 删除测试
- 冲突检测测试
- 版本可见性测试

**Transaction 层测试** (`transaction/transaction_test.go`):
- 事务生命周期测试
- 并发安全测试
- 时间戳测试

**GC 层测试** (`gc/garbage_collector_test.go`):
- 回收逻辑测试
- 统计信息测试
- 启停测试

**集成测试** (`test/mvcc_test.go`):
- 快照隔离测试
- 写写冲突测试
- 并发事务测试
- 读写偏斜测试

### 2026-06-22: 编写文档

创建文档文件：

- `docs/01-RESEARCH.md`: 研究笔记
- `docs/02-DESIGN.md`: 设计文档
- `docs/03-IMPLEMENTATION.md`: 实现细节
- `docs/04-TESTING.md`: 测试文档
- `docs/05-DEVELOPMENT.md`: 开发日志
- `LEARNING_NOTES.md`: 学习笔记

### 2026-06-22: 编写示例程序

创建 `cmd/main.go`，包含 5 个演示：

1. **基本操作演示**: 读写、更新、删除
2. **快照隔离演示**: 事务看到一致的快照
3. **写写冲突演示**: 冲突检测和处理
4. **并发事务演示**: 多事务并发执行
5. **垃圾回收演示**: GC 清理旧版本

## 技术难点

### 1. 可见性判断

**问题**: 如何判断一个版本对某个事务是否可见？

**解决方案**:
```go
func (v *Version) IsVisible(readTimestamp uint64) bool {
    // 1. 版本状态不能是 Garbage
    // 2. 版本必须在读时间戳之前创建
    // 3. 如果已删除，删除时间必须在读时间戳之后
}
```

### 2. 冲突检测

**问题**: 如何检测写写冲突？

**解决方案**:
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

### 3. SafePoint 计算

**问题**: 如何确定可以安全回收的版本？

**解决方案**:
```go
SafePoint = min(所有活跃事务的 StartTimestamp)

// 所有 CreatedAt < SafePoint 的旧版本可以安全回收
```

### 4. 读己之写

**问题**: 事务如何读取自己写入的数据？

**解决方案**:
```go
func (t *Transaction) Read(key string) ([]byte, bool) {
    // 1. 先检查 WriteSet
    if wr, ok := t.txn.GetWrite(key); ok {
        return wr.Value, true
    }
    // 2. 再从 Store 读取
    return t.engine.store.Get(key, t.txn.StartTimestamp)
}
```

## 性能优化

### 已实现的优化

1. **读写锁**: 使用 `sync.RWMutex` 允许并发读
2. **原子时间戳**: 使用 `atomic.AddUint64` 分配时间戳
3. **版本链遍历优化**: 从最新版本开始搜索

### 可以进一步优化

1. **版本链压缩**: 合并不必要的中间版本
2. **分段锁**: 按 key 范围分段加锁
3. **批量提交**: 合并多个小事务
4. **持久化存储**: 使用 B+ 树或 LSM 树

## 代码统计

```
文件                          行数
─────────────────────────────────
internal/store/version.go        ~300
internal/transaction/transaction.go  ~200
internal/gc/garbage_collector.go    ~100
internal/mvcc.go                   ~150
cmd/main.go                        ~200
store/version_test.go              ~200
transaction/transaction_test.go    ~200
gc/garbage_collector_test.go       ~100
test/mvcc_test.go                  ~300
─────────────────────────────────
总计                              ~1750
```

## 经验总结

### 1. 设计先行

在开始编码之前，先完成详细的设计文档，明确：
- 数据结构
- 核心算法
- 并发控制策略
- 错误处理

### 2. 测试驱动

先写测试，再写实现：
- 明确期望行为
- 发现设计问题
- 保证代码质量

### 3. 渐进式开发

分阶段实现：
1. 先实现核心功能
2. 再添加边界情况
3. 最后优化性能

### 4. 文档同步

边开发边写文档：
- 记录设计决策
- 记录技术难点
- 记录经验教训
