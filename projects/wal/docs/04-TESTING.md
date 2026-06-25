# 04-TESTING.md - 测试策略

## 测试层次

### 1. 单元测试
- 测试各个组件的独立功能
- 快速反馈，易于调试

### 2. 集成测试
- 测试组件之间的交互
- 验证整体流程

### 3. 压力测试
- 测试高并发场景
- 验证性能和稳定性

### 4. 崩溃测试
- 模拟各种崩溃场景
- 验证恢复机制

## 测试用例设计

### 日志记录测试

#### 1. 序列化/反序列化测试

```go
func TestLogEntrySerialization(t *testing.T) {
    entry := &LogEntry{
        LSN:       1,
        TxID:      100,
        OpType:    OpPut,
        Key:       "test-key",
        Value:     []byte("test-value"),
        Timestamp: time.Now().UnixNano(),
    }
    
    // 序列化
    data, err := entry.Serialize()
    assert.NoError(t, err)
    assert.NotEmpty(t, data)
    
    // 反序列化
    decoded, err := DeserializeLogEntry(data)
    assert.NoError(t, err)
    assert.Equal(t, entry.LSN, decoded.LSN)
    assert.Equal(t, entry.TxID, decoded.TxID)
    assert.Equal(t, entry.OpType, decoded.OpType)
    assert.Equal(t, entry.Key, decoded.Key)
    assert.Equal(t, entry.Value, decoded.Value)
}
```

#### 2. 校验和验证测试

```go
func TestChecksumValidation(t *testing.T) {
    entry := &LogEntry{
        LSN:       1,
        TxID:      100,
        OpType:    OpPut,
        Key:       "test-key",
        Value:     []byte("test-value"),
        Timestamp: time.Now().UnixNano(),
    }
    
    data, err := entry.Serialize()
    assert.NoError(t, err)
    
    // 修改数据
    corruptedData := make([]byte, len(data))
    copy(corruptedData, data)
    corruptedData[10] ^= 0xFF // 翻转一位
    
    // 应该失败
    _, err = DeserializeLogEntry(corruptedData)
    assert.ErrorIs(t, err, ErrChecksumMismatch)
}
```

### WAL 写入测试

#### 1. 基本写入测试

```go
func TestWALWriterBasicWrite(t *testing.T) {
    tmpDir := t.TempDir()
    walPath := filepath.Join(tmpDir, "test.wal")
    
    writer, err := NewWALWriter(walPath)
    assert.NoError(t, err)
    defer writer.Close()
    
    entry := &LogEntry{
        TxID:      1,
        OpType:    OpPut,
        Key:       "key1",
        Value:     []byte("value1"),
        Timestamp: time.Now().UnixNano(),
    }
    
    err = writer.Write(entry)
    assert.NoError(t, err)
    
    // 验证文件存在
    _, err = os.Stat(walPath)
    assert.NoError(t, err)
}
```

#### 2. 批量写入测试

```go
func TestWALWriterBatchWrite(t *testing.T) {
    tmpDir := t.TempDir()
    walPath := filepath.Join(tmpDir, "test.wal")
    
    writer, err := NewWALWriter(walPath)
    assert.NoError(t, err)
    defer writer.Close()
    
    entries := make([]*LogEntry, 100)
    for i := 0; i < 100; i++ {
        entries[i] = &LogEntry{
            TxID:      uint64(i),
            OpType:    OpPut,
            Key:       fmt.Sprintf("key%d", i),
            Value:     []byte(fmt.Sprintf("value%d", i)),
            Timestamp: time.Now().UnixNano(),
        }
    }
    
    err = writer.WriteBatch(entries)
    assert.NoError(t, err)
    
    // 验证 LSN 递增
    for i := 1; i < len(entries); i++ {
        assert.True(t, entries[i].LSN > entries[i-1].LSN)
    }
}
```

#### 3. 并发写入测试

```go
func TestWALWriterConcurrentWrite(t *testing.T) {
    tmpDir := t.TempDir()
    walPath := filepath.Join(tmpDir, "test.wal")
    
    writer, err := NewWALWriter(walPath)
    assert.NoError(t, err)
    defer writer.Close()
    
    var wg sync.WaitGroup
    for i := 0; i < 10; i++ {
        wg.Add(1)
        go func(id int) {
            defer wg.Done()
            for j := 0; j < 100; j++ {
                entry := &LogEntry{
                    TxID:      uint64(id*100 + j),
                    OpType:    OpPut,
                    Key:       fmt.Sprintf("key-%d-%d", id, j),
                    Value:     []byte(fmt.Sprintf("value-%d-%d", id, j)),
                    Timestamp: time.Now().UnixNano(),
                }
                err := writer.Write(entry)
                assert.NoError(t, err)
            }
        }(i)
    }
    
    wg.Wait()
    
    // 验证所有记录都写入
    reader, err := NewWALReader(walPath)
    assert.NoError(t, err)
    
    entries, err := reader.ReadAll()
    assert.NoError(t, err)
    assert.Equal(t, 1000, len(entries))
}
```

### WAL 读取测试

#### 1. 基本读取测试

```go
func TestWALReaderBasicRead(t *testing.T) {
    tmpDir := t.TempDir()
    walPath := filepath.Join(tmpDir, "test.wal")
    
    // 写入
    writer, err := NewWALWriter(walPath)
    assert.NoError(t, err)
    
    entry := &LogEntry{
        TxID:      1,
        OpType:    OpPut,
        Key:       "test-key",
        Value:     []byte("test-value"),
        Timestamp: time.Now().UnixNano(),
    }
    
    err = writer.Write(entry)
    assert.NoError(t, err)
    writer.Close()
    
    // 读取
    reader, err := NewWALReader(walPath)
    assert.NoError(t, err)
    defer reader.Close()
    
    entries, err := reader.ReadAll()
    assert.NoError(t, err)
    assert.Equal(t, 1, len(entries))
    assert.Equal(t, entry.Key, entries[0].Key)
    assert.Equal(t, entry.Value, entries[0].Value)
}
```

#### 2. 按 LSN 读取测试

```go
func TestWALReaderReadByLSN(t *testing.T) {
    tmpDir := t.TempDir()
    walPath := filepath.Join(tmpDir, "test.wal")
    
    // 写入多个记录
    writer, err := NewWALWriter(walPath)
    assert.NoError(t, err)
    
    entries := make([]*LogEntry, 10)
    for i := 0; i < 10; i++ {
        entries[i] = &LogEntry{
            TxID:      uint64(i),
            OpType:    OpPut,
            Key:       fmt.Sprintf("key%d", i),
            Value:     []byte(fmt.Sprintf("value%d", i)),
            Timestamp: time.Now().UnixNano(),
        }
        err = writer.Write(entries[i])
        assert.NoError(t, err)
    }
    writer.Close()
    
    // 读取特定 LSN
    reader, err := NewWALReader(walPath)
    assert.NoError(t, err)
    defer reader.Close()
    
    entry, err := reader.ReadByLSN(5)
    assert.NoError(t, err)
    assert.Equal(t, uint64(5), entry.LSN)
}
```

### 崩溃恢复测试

#### 1. 正常恢复测试

```go
func TestRecoveryNormal(t *testing.T) {
    tmpDir := t.TempDir()
    walPath := filepath.Join(tmpDir, "test.wal")
    dataPath := filepath.Join(tmpDir, "data")
    
    // 模拟正常操作
    writer, err := NewWALWriter(walPath)
    assert.NoError(t, err)
    
    // 写入数据
    entry1 := &LogEntry{TxID: 1, OpType: OpPut, Key: "key1", Value: []byte("value1")}
    entry2 := &LogEntry{TxID: 1, OpType: OpPut, Key: "key2", Value: []byte("value2")}
    entry3 := &LogEntry{TxID: 1, OpType: OpCommit}
    
    writer.Write(entry1)
    writer.Write(entry2)
    writer.Write(entry3)
    writer.Close()
    
    // 恢复
    recovery := NewRecoveryManager(walPath, dataPath)
    err = recovery.Recover()
    assert.NoError(t, err)
    
    // 验证数据
    storage, err := NewFileStorage(dataPath)
    assert.NoError(t, err)
    
    value, err := storage.Get("key1")
    assert.NoError(t, err)
    assert.Equal(t, []byte("value1"), value)
}
```

#### 2. 崩溃恢复测试

```go
func TestRecoveryCrash(t *testing.T) {
    tmpDir := t.TempDir()
    walPath := filepath.Join(tmpDir, "test.wal")
    dataPath := filepath.Join(tmpDir, "data")
    
    // 模拟崩溃（只写入部分数据）
    writer, err := NewWALWriter(walPath)
    assert.NoError(t, err)
    
    entry1 := &LogEntry{TxID: 1, OpType: OpPut, Key: "key1", Value: []byte("value1")}
    writer.Write(entry1)
    
    // 模拟崩溃：不写入 commit 记录就关闭
    writer.Close()
    
    // 恢复
    recovery := NewRecoveryManager(walPath, dataPath)
    err = recovery.Recover()
    assert.NoError(t, err)
    
    // 验证数据未提交
    storage, err := NewFileStorage(dataPath)
    assert.NoError(t, err)
    
    _, err = storage.Get("key1")
    assert.Error(t, err) // 应该不存在
}
```

### 检查点测试

#### 1. 检查点创建测试

```go
func TestCheckpointCreation(t *testing.T) {
    tmpDir := t.TempDir()
    walPath := filepath.Join(tmpDir, "test.wal")
    
    writer, err := NewWALWriter(walPath)
    assert.NoError(t, err)
    
    // 写入数据
    for i := 0; i < 100; i++ {
        entry := &LogEntry{
            TxID:   uint64(i),
            OpType: OpPut,
            Key:    fmt.Sprintf("key%d", i),
            Value:  []byte(fmt.Sprintf("value%d", i)),
        }
        writer.Write(entry)
    }
    
    // 创建检查点
    checkpointMgr := NewCheckpointManager(walPath)
    err = checkpointMgr.CreateCheckpoint()
    assert.NoError(t, err)
    
    writer.Close()
    
    // 验证检查点存在
    checkpoint, err := checkpointMgr.LoadLastCheckpoint()
    assert.NoError(t, err)
    assert.NotNil(t, checkpoint)
    assert.True(t, checkpoint.LSN > 0)
}
```

#### 2. 日志清理测试

```go
func TestCheckpointLogCleanup(t *testing.T) {
    tmpDir := t.TempDir()
    walPath := filepath.Join(tmpDir, "test.wal")
    
    writer, err := NewWALWriter(walPath)
    assert.NoError(t, err)
    
    // 写入第一批数据
    for i := 0; i < 50; i++ {
        entry := &LogEntry{
            TxID:   uint64(i),
            OpType: OpPut,
            Key:    fmt.Sprintf("key%d", i),
            Value:  []byte(fmt.Sprintf("value%d", i)),
        }
        writer.Write(entry)
    }
    
    // 创建检查点
    checkpointMgr := NewCheckpointManager(walPath)
    checkpointMgr.CreateCheckpoint()
    
    // 写入第二批数据
    for i := 50; i < 100; i++ {
        entry := &LogEntry{
            TxID:   uint64(i),
            OpType: OpPut,
            Key:    fmt.Sprintf("key%d", i),
            Value:  []byte(fmt.Sprintf("value%d", i)),
        }
        writer.Write(entry)
    }
    
    writer.Close()
    
    // 验证旧日志被清理
    files, _ := filepath.Glob(filepath.Join(tmpDir, "*.log"))
    assert.True(t, len(files) <= 2) // 最多两个文件
}
```

### 3. 保留策略测试

```go
func TestRetentionPolicyDefaults(t *testing.T) {
    policy := DefaultRetentionPolicy()
    
    assert.Equal(t, int64(1024*1024*1024), policy.MaxSize)
    assert.Equal(t, 7*24*time.Hour, policy.MaxAge)
    assert.Equal(t, 10, policy.MaxFiles)
    assert.Equal(t, 2, policy.MinFiles)
}

func TestLogCleanerFileCount(t *testing.T) {
    tmpDir := t.TempDir()
    
    // 创建多个 WAL 文件
    for i := 0; i < 5; i++ {
        walPath := filepath.Join(tmpDir, fmt.Sprintf("wal.%d.wal", i))
        writer, _ := NewWALWriter(walPath, SyncImmediate)
        writer.Write(&LogEntry{TxID: uint64(i), OpType: OpPut, Key: "key", Value: []byte("value")})
        writer.Close()
    }
    
    // 创建清理器（最大 3 个文件）
    policy := &RetentionPolicy{MaxFiles: 3, MinFiles: 1}
    cleaner := NewLogCleaner(tmpDir, policy, time.Hour)
    
    // 执行清理
    err := cleaner.Cleanup()
    assert.NoError(t, err)
    
    // 验证文件数量
    count, _ := cleaner.GetFileCount()
    assert.True(t, count <= 3)
}

func TestLogCleanerMinFiles(t *testing.T) {
    tmpDir := t.TempDir()
    
    // 创建多个 WAL 文件
    for i := 0; i < 5; i++ {
        walPath := filepath.Join(tmpDir, fmt.Sprintf("wal.%d.wal", i))
        writer, _ := NewWALWriter(walPath, SyncImmediate)
        writer.Write(&LogEntry{TxID: uint64(i), OpType: OpPut, Key: "key", Value: []byte("value")})
        writer.Close()
    }
    
    // 创建清理器（最大 2 个文件，最小 3 个文件）
    policy := &RetentionPolicy{MaxFiles: 2, MinFiles: 3}
    cleaner := NewLogCleaner(tmpDir, policy, time.Hour)
    
    // 执行清理
    err := cleaner.Cleanup()
    assert.NoError(t, err)
    
    // 验证文件数量（最小文件数量）
    count, _ := cleaner.GetFileCount()
    assert.True(t, count >= 3)
}
```

### 4. WAL 截断测试

```go
func TestTruncateWAL(t *testing.T) {
    tmpDir := t.TempDir()
    walPath := filepath.Join(tmpDir, "test.wal")
    
    // 创建 WAL 文件
    writer, _ := NewWALWriter(walPath, SyncImmediate)
    for i := 0; i < 10; i++ {
        writer.Write(&LogEntry{
            TxID:   uint64(i),
            OpType: OpPut,
            Key:    fmt.Sprintf("key%d", i),
            Value:  []byte(fmt.Sprintf("value%d", i)),
        })
    }
    writer.Close()
    
    // 截断到 LSN 5
    err := TruncateWAL(walPath, 5)
    assert.NoError(t, err)
    
    // 验证剩余条目
    reader, _ := NewWALReader(walPath)
    entries, _ := reader.ReadAll()
    assert.Equal(t, 5, len(entries))
    
    // 验证所有条目 LSN <= 5
    for _, entry := range entries {
        assert.True(t, entry.LSN <= 5)
    }
}

func TestTruncateWALAfterTime(t *testing.T) {
    tmpDir := t.TempDir()
    walPath := filepath.Join(tmpDir, "test.wal")
    
    // 创建 WAL 文件
    writer, _ := NewWALWriter(walPath, SyncImmediate)
    baseTime := time.Now()
    for i := 0; i < 10; i++ {
        writer.Write(&LogEntry{
            TxID:      uint64(i),
            OpType:    OpPut,
            Key:       fmt.Sprintf("key%d", i),
            Value:     []byte(fmt.Sprintf("value%d", i)),
            Timestamp: baseTime.Add(time.Duration(i) * time.Minute).UnixNano(),
        })
    }
    writer.Close()
    
    // 截断到 5 分钟后
    truncateTime := baseTime.Add(5 * time.Minute)
    err := TruncateWALAfterTime(walPath, truncateTime)
    assert.NoError(t, err)
    
    // 验证剩余条目
    reader, _ := NewWALReader(walPath)
    entries, _ := reader.ReadAll()
    
    // 验证所有条目时间戳 <= 截断时间
    for _, entry := range entries {
        entryTime := time.Unix(0, entry.Timestamp)
        assert.True(t, entryTime.Before(truncateTime) || entryTime.Equal(truncateTime))
    }
}
```

### 5. WAL 统计测试

```go
func TestGetWALStats(t *testing.T) {
    tmpDir := t.TempDir()
    walPath := filepath.Join(tmpDir, "test.wal")
    
    // 创建 WAL 文件
    writer, _ := NewWALWriter(walPath, SyncImmediate)
    writer.Write(&LogEntry{TxID: 1, OpType: OpPut, Key: "key1", Value: []byte("value1")})
    writer.Write(&LogEntry{TxID: 2, OpType: OpPut, Key: "key2", Value: []byte("value2")})
    writer.Write(&LogEntry{TxID: 3, OpType: OpDelete, Key: "key1"})
    writer.Write(&LogEntry{TxID: 1, OpType: OpCommit})
    writer.Write(&LogEntry{TxID: 2, OpType: OpCommit})
    writer.Write(&LogEntry{TxID: 3, OpType: OpCommit})
    writer.Close()
    
    // 获取统计信息
    stats, err := GetWALStats(walPath)
    assert.NoError(t, err)
    
    assert.Equal(t, 6, stats.TotalEntries)
    assert.Equal(t, 2, stats.PutOperations)
    assert.Equal(t, 1, stats.DeleteOperations)
    assert.Equal(t, 3, stats.Commits)
    assert.Equal(t, uint64(6), stats.MaxLSN)
    assert.True(t, stats.FileSize > 0)
}
```

## 压力测试

### 1. 高并发写入测试

```go
func BenchmarkWALWriterConcurrent(b *testing.B) {
    tmpDir := b.TempDir()
    walPath := filepath.Join(tmpDir, "bench.wal")
    
    writer, _ := NewWALWriter(walPath)
    defer writer.Close()
    
    b.ResetTimer()
    b.RunParallel(func(pb *testing.PB) {
        i := 0
        for pb.Next() {
            entry := &LogEntry{
                TxID:   uint64(i),
                OpType: OpPut,
                Key:    fmt.Sprintf("key%d", i),
                Value:  []byte(fmt.Sprintf("value%d", i)),
            }
            writer.Write(entry)
            i++
        }
    })
}
```

### 2. 批量写入测试

```go
func BenchmarkWALWriterBatch(b *testing.B) {
    tmpDir := b.TempDir()
    walPath := filepath.Join(tmpDir, "bench.wal")
    
    writer, _ := NewWALWriter(walPath)
    defer writer.Close()
    
    batchSize := 1000
    entries := make([]*LogEntry, batchSize)
    for i := 0; i < batchSize; i++ {
        entries[i] = &LogEntry{
            TxID:   uint64(i),
            OpType: OpPut,
            Key:    fmt.Sprintf("key%d", i),
            Value:  []byte(fmt.Sprintf("value%d", i)),
        }
    }
    
    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        writer.WriteBatch(entries)
    }
}
```

## 测试工具

### 1. 测试辅助函数

```go
func createTestWAL(t *testing.T, entries int) (string, []*LogEntry) {
    tmpDir := t.TempDir()
    walPath := filepath.Join(tmpDir, "test.wal")
    
    writer, err := NewWALWriter(walPath)
    require.NoError(t, err)
    
    logEntries := make([]*LogEntry, entries)
    for i := 0; i < entries; i++ {
        logEntries[i] = &LogEntry{
            TxID:      uint64(i),
            OpType:    OpPut,
            Key:       fmt.Sprintf("key%d", i),
            Value:     []byte(fmt.Sprintf("value%d", i)),
            Timestamp: time.Now().UnixNano(),
        }
        writer.Write(logEntries[i])
    }
    
    writer.Close()
    return walPath, logEntries
}
```

### 2. 测试覆盖率

```bash
# 运行测试并生成覆盖率报告
go test -coverprofile=coverage.out ./...
go tool cover -html=coverage.out
```

## 测试环境

### 1. 本地测试

```bash
# 运行所有测试
go test ./...

# 运行特定测试
go test -run TestWALWriter ./...

# 运行基准测试
go test -bench=. ./...
```

### 2. CI/CD 测试

```yaml
# .github/workflows/test.yml
name: Test
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-go@v2
        with:
          go-version: '1.21'
      - run: go test -race -coverprofile=coverage.out ./...
```
