# 04 - 测试: LSM Tree 测试策略

## 测试架构

```
test/
├── skiplist_test.go     # 跳表单元测试
├── memtable_test.go     # (通过 engine 测试覆盖)
├── sstable_test.go      # SSTable 单元测试
├── wal_test.go          # WAL 单元测试
├── compaction_test.go   # Compaction 单元测试
└── engine_test.go       # 端到端集成测试
```

## 测试覆盖率

```
总体覆盖率: 59.9%

高覆盖率模块:
- SkipList: 100% (核心操作)
- MemTable: 100% (核心操作)
- SSTable.Get: 94.7%
- Engine.Get: 86.7%
- Engine.compactLevel: 87.5%

低覆盖率模块:
- MergeIterator: 0% (未在测试中使用)
- NewCompactor: 0% (使用 Compact 函数代替)
```

## 测试用例详解

### SkipList 测试

```go
// 测试插入和查找
func TestSkipListInsertAndGet(t *testing.T)

// 测试更新 (覆盖已存在的 key)
func TestSkipListUpdate(t *testing.T)

// 测试删除 (墓碑标记)
func TestSkipListDelete(t *testing.T)

// 测试有序性 (验证排序正确)
func TestSkipListSortedOrder(t *testing.T)

// 测试迭代器
func TestSkipListIterator(t *testing.T)

// 测试大小统计
func TestSkipListSize(t *testing.T)

// 大数据量测试 (1000 个 entry)
func TestSkipListLargeDataset(t *testing.T)
```

### SSTable 测试

```go
// 测试构建和查找
func TestSSTableBuildAndGet(t *testing.T)

// 测试 tombstone
func TestSSTableTombstone(t *testing.T)

// 测试排序 (乱序写入，有序读出)
func TestSSTableSorted(t *testing.T)

// 大数据量测试 (1000 个 entry)
func TestSSTableLargeDataset(t *testing.T)

// 测试持久化 (关闭后重新打开)
func TestSSTablePersistence(t *testing.T)

// 测试空 SSTable
func TestSSTableEmpty(t *testing.T)
```

### WAL 测试

```go
// 测试写入和重放
func TestWALWriteAndReplay(t *testing.T)

// 测试多次写入
func TestWALMultiplePuts(t *testing.T)

// 测试不存在的 WAL (应该成功)
func TestWALNonExistentReplay(t *testing.T)

// 测试数据完整性 (CRC 校验)
func TestWALIntegrity(t *testing.T)

// 测试删除 WAL 文件
func TestWALRemove(t *testing.T)
```

### Compaction 测试

```go
// 测试合并两个表
func TestCompactMergeTwoTables(t *testing.T)

// 测试 tombstone 移除
func TestCompactRemovesTombstones(t *testing.T)

// 测试合并多个表
func TestCompactMultipleTables(t *testing.T)

// 测试空表合并
func TestCompactEmptyTables(t *testing.T)
```

### Engine 测试

```go
// 测试基本 CRUD
func TestEngineBasicOperations(t *testing.T)

// 测试更新
func TestEngineUpdate(t *testing.T)

// 测试删除
func TestEngineDelete(t *testing.T)

// 测试 Flush (小 MemTable)
func TestEngineFlush(t *testing.T)

// 测试持久化 (关闭后重新打开)
func TestEnginePersistence(t *testing.T)

// 测试崩溃恢复 (WAL 重放)
func TestEngineCrashRecovery(t *testing.T)

// 测试混合操作
func TestEngineMixedOperations(t *testing.T)

// 大数据量测试 (500 个 entry)
func TestEngineLargeDataset(t *testing.T)

// 测试统计信息
func TestEngineStats(t *testing.T)
```

## 关键测试场景

### 1. 崩溃恢复测试

```go
func TestEngineCrashRecovery(t *testing.T) {
    dir := t.TempDir()

    // 写入数据 (未 Flush)
    engine, _ := lsm.NewLSMEngine(dir, 1024*1024)
    engine.Put([]byte("key1"), []byte("value1"))
    engine.Put([]byte("key2"), []byte("value2"))
    // 模拟崩溃: 不调用 Close，直接创建新引擎

    // 重新打开 (WAL 重放)
    engine2, _ := lsm.NewLSMEngine(dir, 1024*1024)
    defer engine2.Close()

    // 验证数据恢复
    val, _ := engine2.Get([]byte("key1"))
    assert(val == "value1")
}
```

### 2. 持久化测试

```go
func TestEnginePersistence(t *testing.T) {
    dir := t.TempDir()

    // 写入并 Flush
    engine, _ := lsm.NewLSMEngine(dir, 4096)
    engine.Put([]byte("key1"), []byte("value1"))
    engine.Close() // 触发 Flush

    // 重新打开
    engine2, _ := lsm.NewLSMEngine(dir, 4096)
    defer engine2.Close()

    // 验证数据持久化
    val, _ := engine2.Get([]byte("key1"))
    assert(val == "value1")
}
```

### 3. CRC 校验测试

```go
func TestWALIntegrity(t *testing.T) {
    dir := t.TempDir()
    walPath := filepath.Join(dir, "test.wal")

    // 写入数据
    wal, _ := lsm.NewWAL(walPath)
    wal.WritePut([]byte("key1"), []byte("value1"))
    wal.Close()

    // 破坏文件
    data, _ := os.ReadFile(walPath)
    data[len(data)-1] ^= 0xFF
    os.WriteFile(walPath, data, 0644)

    // 重放应该失败
    memTable := lsm.NewMemTable(1024 * 1024)
    err := lsm.WALReplay(walPath, memTable)
    assert(err != nil) // CRC 错误
}
```

## 运行测试

```bash
# 运行所有测试
go test ./test/ -v

# 运行特定测试
go test ./test/ -v -run "TestSSTable"

# 生成覆盖率
go test ./test/ -coverpkg=./internal/ -coverprofile=coverage.out
go tool cover -func=coverage.out

# 查看 HTML 覆盖率报告
go tool cover -html=coverage.out
```

## 测试最佳实践

1. **使用 t.TempDir()**: 自动清理临时目录
2. **测试边界条件**: 空表、单个 entry、大数据量
3. **测试错误路径**: CRC 错误、文件不存在
4. **测试持久化**: 关闭后重新打开
5. **测试崩溃恢复**: WAL 重放
