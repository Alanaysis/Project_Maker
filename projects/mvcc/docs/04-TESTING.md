# 04 - 测试文档

## 测试策略

### 测试层次

```
┌─────────────────────────────────────┐
│         集成测试 (test/)             │
│    MVCC 引擎完整流程测试            │
├─────────────────────────────────────┤
│       组件测试 (internal/*/)        │
│  Store / Transaction / GC 测试     │
├─────────────────────────────────────┤
│         单元测试                     │
│    版本可见性 / 冲突检测等          │
└─────────────────────────────────────┘
```

### 测试覆盖

| 组件 | 测试文件 | 测试数量 | 覆盖范围 |
|------|----------|----------|----------|
| Store | store/version_test.go | 12 | 读写、删除、可见性、冲突检测、GC |
| Transaction | transaction/transaction_test.go | 12 | 生命周期、并发安全、时间戳 |
| GC | gc/garbage_collector_test.go | 4 | 回收逻辑、统计、启停 |
| MVCC Engine | test/mvcc_test.go | 12 | 完整流程、隔离级别、并发 |

## 运行测试

### 运行所有测试

```bash
cd projects/mvcc
go test ./...
```

### 运行特定包的测试

```bash
# Store 层测试
go test ./internal/store/... -v

# Transaction 层测试
go test ./internal/transaction/... -v

# GC 层测试
go test ./internal/gc/... -v

# 集成测试
go test ./test/... -v
```

### 运行特定测试

```bash
go test ./test/... -run TestMVSSEngineSnapshotIsolation -v
```

### 显示测试覆盖率

```bash
go test ./... -coverprofile=coverage.out
go tool cover -html=coverage.out
```

## 单元测试详情

### Store 层测试

#### 基本读写测试

```go
func TestStorePutAndGet(t *testing.T) {
    s := NewStore()
    s.Put("key1", []byte("value1"), 1, 1)

    val, ok := s.Get("key1", 1)
    if !ok || string(val) != "value1" {
        t.Fatalf("expected 'value1', got '%s'", string(val))
    }
}
```

**测试点**:
- Put 写入成功
- Get 读取正确值
- 未找到的 key 返回 ok=false

#### 多版本测试

```go
func TestStoreMultipleVersions(t *testing.T) {
    s := NewStore()
    s.Put("key1", []byte("v1"), 1, 1)
    s.Put("key1", []byte("v2"), 2, 2)
    s.Put("key1", []byte("v3"), 3, 3)

    // 不同时间戳读取不同版本
    val, _ := s.Get("key1", 1)  // v1
    val, _ = s.Get("key1", 2)   // v2
    val, _ = s.Get("key1", 3)   // v3
    val, _ = s.Get("key1", 100) // v3 (最新)
}
```

**测试点**:
- 同一 key 可以有多个版本
- 不同时间戳读取正确的版本
- 未来时间戳读取最新版本

#### 删除测试

```go
func TestStoreDelete(t *testing.T) {
    s := NewStore()
    s.Put("key1", []byte("value1"), 1, 1)
    s.Delete("key1", 2, 2)

    // 删除前的时间戳仍可见
    val, ok := s.Get("key1", 1)  // 可见

    // 删除后的时间戳不可见
    _, ok = s.Get("key1", 2)     // 不可见
    _, ok = s.Get("key1", 3)     // 不可见
}
```

**测试点**:
- 删除操作创建 tombstone
- 删除前的快照仍可见
- 删除后的快照不可见

#### 冲突检测测试

```go
func TestStoreHasConflict(t *testing.T) {
    s := NewStore()
    s.Put("key1", []byte("value1"), 1, 2)

    // 事务 2 在事务 1 写入之前开始，有冲突
    hasConflict := s.HasConflict("key1", 1, 2)  // true

    // 事务 3 在事务 1 写入之后开始，无冲突
    hasConflict = s.HasConflict("key1", 2, 3)   // false
}
```

**测试点**:
- 检测到写写冲突
- 自己的写入不视为冲突
- 时间戳相等不视为冲突

#### 版本可见性测试

```go
func TestVersionIsVisible(t *testing.T) {
    tests := []struct {
        name           string
        createdAt      uint64
        deletedAt      uint64
        status         VersionStatus
        readTimestamp  uint64
        expectedVisible bool
    }{
        {"visible - created before read", 1, 0, VersionActive, 2, true},
        {"visible - created at read time", 2, 0, VersionActive, 2, true},
        {"not visible - created after read", 3, 0, VersionActive, 2, false},
        {"not visible - deleted before read", 1, 2, VersionDeleted, 3, false},
        {"visible - deleted after read", 1, 3, VersionDeleted, 2, true},
        {"not visible - garbage status", 1, 0, VersionGarbage, 10, false},
    }
}
```

**测试点**:
- 创建时间戳 <= 读时间戳才可见
- 删除时间戳 > 读时间戳才可见
- Garbage 状态不可见

### Transaction 层测试

#### 事务生命周期测试

```go
func TestTransactionManagerBegin(t *testing.T) {
    tm := NewTransactionManager()
    txn := tm.Begin()

    if txn.Status != TxnActive {
        t.Fatal("expected status Active")
    }
}

func TestTransactionManagerCommit(t *testing.T) {
    tm := NewTransactionManager()
    txn := tm.Begin()

    commitTS, err := tm.Commit(txn.ID)
    if err != nil {
        t.Fatal("unexpected error")
    }
    if commitTS <= txn.StartTimestamp {
        t.Fatal("commitTS should be > startTS")
    }
}
```

**测试点**:
- Begin 创建活跃事务
- Commit 分配提交时间戳
- Abort 标记事务为中止

#### 并发安全测试

```go
func TestTransactionConcurrentAccess(t *testing.T) {
    tm := NewTransactionManager()

    var wg sync.WaitGroup
    for i := 0; i < 100; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            txn := tm.Begin()
            txn.AddRead("key", 1)
            txn.AddWrite("key", []byte("value"))
            tm.Commit(txn.ID)
        }()
    }
    wg.Wait()

    if tm.ActiveCount() != 0 {
        t.Fatal("expected 0 active transactions")
    }
}
```

**测试点**:
- 100 个 goroutine 并发操作
- 无数据竞争
- 最终状态正确

### GC 层测试

#### 基本回收测试

```go
func TestGarbageCollectorRun(t *testing.T) {
    s := store.NewStore()
    txMgr := transaction.NewTransactionManager()
    gc := NewGarbageCollector(s, txMgr, time.Hour)

    // 创建版本
    s.Put("key1", []byte("v1"), 1, 1)
    s.Put("key1", []byte("v2"), 2, 2)
    s.Put("key1", []byte("v3"), 3, 3)

    // 开始一个事务（设置 SafePoint）
    txMgr.Begin() // StartTS=4

    // 运行 GC
    removed := gc.Run()  // 应该移除 v1 和 v2

    if removed != 2 {
        t.Fatalf("expected 2 removed, got %d", removed)
    }
}
```

**测试点**:
- GC 正确识别可回收版本
- 统计信息正确更新
- SafePoint 计算正确

#### 启停测试

```go
func TestGarbageCollectorStartStop(t *testing.T) {
    gc := NewGarbageCollector(s, txMgr, 10*time.Millisecond)

    gc.Start()
    time.Sleep(50 * time.Millisecond)
    gc.Stop()

    if gc.Stats().TotalRuns == 0 {
        t.Fatal("expected at least 1 run")
    }
}
```

**测试点**:
- 启动后定期运行
- 停止后不再运行
- 无 goroutine 泄漏

## 集成测试详情

### 快照隔离测试

```go
func TestMVSSEngineSnapshotIsolation(t *testing.T) {
    engine := internal.NewMVSSEngine()

    // T1 写入并提交
    txn1 := engine.Begin()
    txn1.Write("key1", []byte("value1"))
    txn1.Commit()

    // T2 开始（快照时间点）
    txn2 := engine.Begin()

    // T3 写入新值并提交
    txn3 := engine.Begin()
    txn3.Write("key1", []byte("value2"))
    txn3.Commit()

    // T2 读取 - 应该看到旧值（快照隔离）
    val, _ := txn2.Read("key1")
    if string(val) != "value1" {
        t.Fatal("snapshot isolation violation")
    }
}
```

**测试点**:
- 事务看到一致的快照
- 后续提交不影响已有快照
- 新事务能看到最新提交

### 写写冲突测试

```go
func TestMVSSEngineWriteWriteConflict(t *testing.T) {
    engine := internal.NewMVSSEngine()

    // 初始数据
    txn1 := engine.Begin()
    txn1.Write("key1", []byte("value1"))
    txn1.Commit()

    // T2 和 T3 并发读取
    txn2 := engine.Begin()
    txn3 := engine.Begin()
    txn2.Read("key1")
    txn3.Read("key1")

    // T2 先提交
    txn2.Write("key1", []byte("value2"))
    txn2.Commit()

    // T3 后提交 - 冲突
    txn3.Write("key1", []byte("value3"))
    err := txn3.Commit()
    if err == nil {
        t.Fatal("expected conflict error")
    }
}
```

**测试点**:
- 检测到写写冲突
- 冲突事务被中止
- 第一个提交的事务成功

### 并发事务测试

```go
func TestMVSSEngineConcurrentTransactions(t *testing.T) {
    engine := internal.NewMVSSEngine()

    var wg sync.WaitGroup
    for i := 0; i < 50; i++ {
        wg.Add(1)
        go func(id int) {
            defer wg.Done()
            txn := engine.Begin()
            txn.Write(fmt.Sprintf("key_%d", id), []byte("value"))
            txn.Commit()
        }(i)
    }
    wg.Wait()

    // 验证所有写入
    txn := engine.Begin()
    for i := 0; i < 50; i++ {
        _, ok := txn.Read(fmt.Sprintf("key_%d", i))
        if !ok {
            t.Fatal("expected key to exist")
        }
    }
    txn.Commit()
}
```

**测试点**:
- 50 个并发事务
- 无数据竞争
- 所有写入正确提交

### 读写偏斜测试

```go
func TestMVSSEngineReadWriteSkew(t *testing.T) {
    engine := internal.NewMVSSEngine()

    // 初始: key1=100, key2=200
    txn0 := engine.Begin()
    txn0.Write("key1", []byte("100"))
    txn0.Write("key2", []byte("200"))
    txn0.Commit()

    // T1 读取两个 key
    txnA := engine.Begin()
    txnA.Read("key1")
    txnA.Read("key2")

    // T2 修改两个 key
    txnB := engine.Begin()
    txnB.Write("key1", []byte("150"))
    txnB.Write("key2", []byte("150"))
    txnB.Commit()

    // T1 仍看到一致的快照
    val1, _ := txnA.Read("key1")
    val2, _ := txnA.Read("key2")
    if string(val1) != "100" || string(val2) != "200" {
        t.Fatal("snapshot consistency violated")
    }
}
```

**测试点**:
- 事务内多次读取一致
- 不受其他事务提交影响
- 快照隔离保证一致性

## 测试结果示例

```
=== RUN   TestStorePutAndGet
--- PASS: TestStorePutAndGet (0.00s)
=== RUN   TestStoreMultipleVersions
--- PASS: TestStoreMultipleVersions (0.00s)
=== RUN   TestMVSSEngineSnapshotIsolation
--- PASS: TestMVSSEngineSnapshotIsolation (0.00s)
=== RUN   TestMVSSEngineWriteWriteConflict
--- PASS: TestMVSSEngineWriteWriteConflict (0.00s)
...
PASS
ok      mvcc/internal/store     0.002s
ok      mvcc/internal/transaction 0.003s
ok      mvcc/internal/gc        0.005s
ok      mvcc/test               0.008s
```

## 测试最佳实践

### 1. 测试命名

使用描述性的测试名称：

```go
// 好
func TestStoreMultipleVersions(t *testing.T) { ... }
func TestMVSSEngineSnapshotIsolation(t *testing.T) { ... }

// 不好
func TestStore1(t *testing.T) { ... }
func TestMVCC(t *testing.T) { ... }
```

### 2. 表驱动测试

使用表驱动测试测试多种情况：

```go
func TestVersionIsVisible(t *testing.T) {
    tests := []struct {
        name           string
        createdAt      uint64
        deletedAt      uint64
        expectedVisible bool
    }{
        // ... 多种情况
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            // 测试逻辑
        })
    }
}
```

### 3. 并发测试

使用 goroutine 和 WaitGroup 测试并发安全性：

```go
func TestConcurrentAccess(t *testing.T) {
    var wg sync.WaitGroup
    for i := 0; i < 100; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            // 并发操作
        }()
    }
    wg.Wait()
}
```

### 4. 错误测试

测试错误情况：

```go
func TestCommitNonExistent(t *testing.T) {
    tm := NewTransactionManager()
    _, err := tm.Commit(999)
    if err == nil {
        t.Fatal("expected error")
    }
}
```
