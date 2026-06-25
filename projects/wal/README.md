# WAL 日志

## 概述

WAL（Write-Ahead Logging，预写日志）是一种在数据库和文件系统中广泛使用的技术，用于保证数据的一致性和持久性。本项目实现了 WAL 日志的核心功能，包括日志格式定义、日志写入与读取、崩溃恢复、检查点机制、日志清理和保留策略。

**技术栈**：Go

**学习目标**：
- 理解 WAL 原理
- 掌握日志写入
- 学会崩溃恢复
- 实现日志清理和保留策略
- 应用事件溯源和审计日志

## 核心循环

```
操作 → 日志写入 → 数据写入 → 检查点 → 日志清理
```

## 最小可用版本

- [x] 实现 WAL 日志格式
- [x] 日志写入和读取
- [x] 崩溃恢复
- [x] 检查点机制
- [x] 日志清理和保留策略
- [x] WAL 文件截断
- [x] 事件溯源示例
- [x] 审计日志示例

## 项目结构

```
wal/
├── README.md
├── docs/
│   ├── 01-RESEARCH.md
│   ├── 02-DESIGN.md
│   ├── 03-IMPLEMENTATION.md
│   ├── 04-TESTING.md
│   └── 05-DEVELOPMENT.md
├── cmd/
│   └── wal-server/
│       └── main.go
├── internal/
│   ├── wal/
│   │   ├── wal.go           # WAL 核心实现（Writer/Reader）
│   │   ├── entry.go         # 日志条目格式
│   │   ├── recovery.go      # 崩溃恢复
│   │   ├── checkpoint.go    # 检查点管理
│   │   └── retention.go     # 日志清理和保留策略
│   └── storage/
│       └── storage.go       # 存储层实现
├── test/
│   ├── wal_test.go          # WAL 基础测试
│   ├── recovery_test.go     # 恢复测试
│   ├── checkpoint_test.go   # 检查点测试
│   └── retention_test.go    # 日志清理测试
└── examples/
    ├── usage.go             # 基础使用示例
    ├── event_sourcing.go    # 事件溯源示例
    └── audit_log.go         # 审计日志示例
```

## 快速开始

```bash
# 运行基础示例
cd projects/wal
go run examples/usage.go

# 运行事件溯源示例
go run examples/event_sourcing.go

# 运行审计日志示例
go run examples/audit_log.go

# 运行测试
go test ./test/...

# 运行 WAL 服务器
go run cmd/wal-server/main.go
```

## 核心功能

### 1. 日志写入

```go
// 创建 WAL Writer
writer, err := wal.NewWALWriter("data.wal", wal.SyncImmediate)

// 写入单条记录
entry := &wal.LogEntry{
    TxID:   1,
    OpType: wal.OpPut,
    Key:    "user:1",
    Value:  []byte("Alice"),
}
writer.Write(entry)

// 批量写入
entries := []*wal.LogEntry{entry1, entry2, entry3}
writer.WriteBatch(entries)
```

### 2. 日志格式

```
┌─────────────────────────────────────────────────┐
│ Log Entry                                       │
├─────────────────────────────────────────────────┤
│ LSN (8 bytes)      - 日志序列号                 │
│ TxID (8 bytes)     - 事务 ID                    │
│ OpType (1 byte)    - 操作类型                   │
│ Key (variable)     - 键                         │
│ Value (variable)   - 值                         │
│ Timestamp (8 bytes) - 时间戳                    │
│ CRC32 (4 bytes)    - 校验和                     │
└─────────────────────────────────────────────────┘
```

### 3. 崩溃恢复

```go
// 创建恢复管理器
recovery := wal.NewRecoveryManager("data.wal", storage)

// 执行恢复
err := recovery.Recover()

// 获取已提交的事务
committed := recovery.GetCommittedTransactions()
active := recovery.GetActiveTransactions()
```

### 4. 检查点

```go
// 创建检查点管理器
checkpointMgr := wal.NewCheckpointManager(walDir, writer, 30*time.Second)

// 启动定期检查点
checkpointMgr.StartPeriodicCheckpoint()

// 手动创建检查点
checkpointMgr.CreateCheckpoint()

// 标记脏页
checkpointMgr.MarkDirty("user:1")
```

### 5. 日志清理和保留策略

```go
// 创建保留策略
policy := &wal.RetentionPolicy{
    MaxSize:  1024 * 1024 * 1024, // 1 GB
    MaxAge:   7 * 24 * time.Hour, // 7 天
    MaxFiles: 10,
    MinFiles: 2,
}

// 创建日志清理器
cleaner := wal.NewLogCleaner(walDir, policy, 1*time.Hour)

// 启动定期清理
cleaner.Start()

// 手动执行清理
cleaner.Cleanup()

// 获取统计信息
totalSize, _ := cleaner.GetTotalSize()
fileCount, _ := cleaner.GetFileCount()
```

### 6. WAL 截断

```go
// 按 LSN 截断
err := wal.TruncateWAL("data.wal", 100)

// 按时间截断
cutoff := time.Now().Add(-24 * time.Hour)
err := wal.TruncateWALAfterTime("data.wal", cutoff)

// 获取 WAL 统计信息
stats, err := wal.GetWALStats("data.wal")
fmt.Println(stats.String())
```

## 实际应用

### 1. 数据库 WAL

```go
// 数据库事务示例
writer.Write(&wal.LogEntry{TxID: 1, OpType: wal.OpPut, Key: "users:1", Value: userData})
writer.Write(&wal.LogEntry{TxID: 1, OpType: wal.OpPut, Key: "accounts:1", Value: accountData})
writer.Write(&wal.LogEntry{TxID: 1, OpType: wal.OpCommit})
```

### 2. 事件溯源

```go
// 事件溯源示例
eventStore.AppendEvent("user:1", "UserCreated", map[string]interface{}{
    "name":  "Alice",
    "email": "alice@example.com",
})

eventStore.AppendEvent("user:1", "UserUpdated", map[string]interface{}{
    "name": "Alice Smith",
})

// 重放事件重建状态
events := eventStore.GetEvents("user:1")
user := &UserAggregate{}
for _, event := range events {
    user.ApplyEvent(event)
}
```

### 3. 审计日志

```go
// 审计日志示例
auditLogger.LogAction("user:1", ActionLogin, "auth", "User logged in", "192.168.1.1", "Mozilla/5.0", true)
auditLogger.LogAction("user:1", ActionUpdate, "users:1", "Updated email", "192.168.1.1", "Mozilla/5.0", true)

// 查询审计日志
userEntries := auditLogger.GetEntriesByUser("user:1")
failedEntries := auditLogger.GetFailedEntries()
report := auditLogger.GenerateReport()
```

## 同步模式

```go
// 同步写入（每次写入后 fsync）
writer, _ := wal.NewWALWriter("data.wal", wal.SyncImmediate)

// 批量同步（定期 fsync）
writer, _ := wal.NewWALWriter("data.wal", wal.SyncBatch)

// 不同步（仅用于测试）
writer, _ := wal.NewWALWriter("data.wal", wal.SyncNone)
```

## 文档

- [01-RESEARCH.md](docs/01-RESEARCH.md) - WAL 技术研究
- [02-DESIGN.md](docs/02-DESIGN.md) - 系统设计
- [03-IMPLEMENTATION.md](docs/03-IMPLEMENTATION.md) - 实现细节
- [04-TESTING.md](docs/04-TESTING.md) - 测试策略
- [05-DEVELOPMENT.md](docs/05-DEVELOPMENT.md) - 开发指南

## 依赖

- Go 1.21+
- 无外部依赖

## 测试

```bash
# 运行所有测试
go test ./test/...

# 运行特定测试
go test -run TestWAL ./test/...

# 运行测试并生成覆盖率报告
go test -coverprofile=coverage.out ./test/...
go tool cover -html=coverage.out
```

## 性能优化

1. **批量写入**：使用 `WriteBatch` 减少 I/O 次数
2. **同步模式**：根据场景选择合适的同步模式
3. **日志清理**：定期清理旧日志减少文件数量
4. **检查点**：合理设置检查点间隔减少恢复时间

## 许可证

本项目仅供学习使用。
