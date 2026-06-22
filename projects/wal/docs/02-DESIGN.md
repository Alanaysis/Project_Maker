# 02-DESIGN.md - 系统设计

## 设计目标

1. **可靠性**：保证数据不会丢失
2. **一致性**：数据状态始终保持一致
3. **性能**：高效的日志写入和读取
4. **可恢复性**：系统崩溃后能够恢复数据

## 架构设计

### 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      Application Layer                      │
├─────────────────────────────────────────────────────────────┤
│                      WAL Manager                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Writer    │  │   Reader    │  │  Recovery   │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
├─────────────────────────────────────────────────────────────┤
│                      Storage Layer                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  Log File   │  │  Checkpoint │  │  Data File  │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

### 模块划分

#### 1. WAL Manager（WAL 管理器）
- 协调各个组件
- 管理事务生命周期
- 处理检查点调度

#### 2. Writer（写入器）
- 负责日志记录的写入
- 管理日志缓冲区
- 处理日志刷盘

#### 3. Reader（读取器）
- 读取日志记录
- 解析日志格式
- 支持顺序和随机读取

#### 4. Recovery（恢复器）
- 处理崩溃恢复
- 重放日志
- 回滚未完成事务

#### 5. Storage Layer（存储层）
- 管理物理文件
- 处理文件 I/O
- 管理文件生命周期

## 数据模型

### LogEntry（日志记录）

```go
type LogEntry struct {
    LSN         uint64      // 日志序列号
    TxID        uint64      // 事务 ID
    OpType      OperationType // 操作类型
    Key         string      // 键
    Value       []byte      // 值
    Checksum    uint32      // CRC32 校验和
    Timestamp   int64       // 时间戳
}

type OperationType uint8

const (
    OpPut      OperationType = 1
    OpDelete   OperationType = 2
    OpCheckpoint OperationType = 3
)
```

### Checkpoint（检查点）

```go
type Checkpoint struct {
    LSN         uint64      // 检查点 LSN
    Timestamp   int64       // 检查点时间戳
    ActiveTxIDs []uint64    // 活跃事务列表
    DirtyPages  []PageInfo  // 脏页列表
}

type PageInfo struct {
    PageID      uint64
    LSN         uint64
}
```

### WALFile（WAL 文件）

```go
type WALFile struct {
    Path        string
    File        *os.File
    CurrentLSN  uint64
    Buffer      []byte
    BufferSize  int
}
```

## 接口设计

### WAL Manager 接口

```go
type WALManager interface {
    // 初始化 WAL
    Init() error
    
    // 开始事务
    BeginTx() (uint64, error)
    
    // 记录操作
    LogPut(txID uint64, key string, value []byte) error
    LogDelete(txID uint64, key string) error
    
    // 提交事务
    CommitTx(txID uint64) error
    
    // 回滚事务
    RollbackTx(txID uint64) error
    
    // 创建检查点
    CreateCheckpoint() error
    
    // 恢复
    Recover() error
    
    // 关闭 WAL
    Close() error
}
```

### Storage 接口

```go
type Storage interface {
    // 读取数据
    Get(key string) ([]byte, error)
    
    // 写入数据
    Put(key string, value []byte) error
    
    // 删除数据
    Delete(key string) error
    
    // 列出所有键
    List() ([]string, error)
    
    // 关闭存储
    Close() error
}
```

## 日志格式设计

### 文件结构

```
┌─────────────────────────────────────────────────────────────┐
│                    WAL Log File                             │
├─────────────────────────────────────────────────────────────┤
│ Header                                                       │
│  - Magic Number: 4 bytes (0x57414C00)                       │
│  - Version: 4 bytes                                         │
│  - Created At: 8 bytes                                      │
│  - Checksum: 4 bytes                                        │
├─────────────────────────────────────────────────────────────┤
│ Log Entry 1                                                  │
│  - Length: 4 bytes                                           │
│  - LSN: 8 bytes                                             │
│  - TxID: 8 bytes                                            │
│  - OpType: 1 byte                                           │
│  - Key Length: 4 bytes                                       │
│  - Key: variable                                             │
│  - Value Length: 4 bytes                                     │
│  - Value: variable                                           │
│  - Timestamp: 8 bytes                                        │
│  - CRC32: 4 bytes                                           │
├─────────────────────────────────────────────────────────────┤
│ Log Entry 2                                                  │
│  ...                                                         │
├─────────────────────────────────────────────────────────────┤
│ Checkpoint Record                                            │
│  ...                                                         │
└─────────────────────────────────────────────────────────────┘
```

### 序列化格式

使用二进制格式，采用小端字节序（Little-Endian）：

```
┌─────────────────────────────────────────────────────────────┐
│ Entry Length (4 bytes)                                       │
├─────────────────────────────────────────────────────────────┤
│ LSN (8 bytes)                                                │
├─────────────────────────────────────────────────────────────┤
│ Transaction ID (8 bytes)                                     │
├─────────────────────────────────────────────────────────────┤
│ Operation Type (1 byte)                                      │
├─────────────────────────────────────────────────────────────┤
│ Key Length (4 bytes)                                          │
├─────────────────────────────────────────────────────────────┤
│ Key (variable)                                               │
├─────────────────────────────────────────────────────────────┤
│ Value Length (4 bytes)                                        │
├─────────────────────────────────────────────────────────────┤
│ Value (variable)                                              │
├─────────────────────────────────────────────────────────────┤
│ Timestamp (8 bytes)                                           │
├─────────────────────────────────────────────────────────────┤
│ CRC32 (4 bytes)                                               │
└─────────────────────────────────────────────────────────────┘
```

## 并发设计

### 锁策略

1. **全局锁**：用于保护 WAL 文件的创建和删除
2. **写锁**：用于保护日志写入操作
3. **读锁**：用于保护日志读取操作
4. **事务锁**：用于保护事务状态

### 并发流程

```
Thread 1: BeginTx → LogPut → CommitTx
Thread 2: BeginTx → LogDelete → CommitTx
Thread 3: CreateCheckpoint

锁层次：
- 全局锁（低频）
- 写锁（中频）
- 事务锁（高频）
```

## 错误处理

### 错误类型

```go
var (
    ErrWALNotInitialized = errors.New("WAL not initialized")
    ErrTransactionNotFound = errors.New("transaction not found")
    ErrChecksumMismatch = errors.New("checksum mismatch")
    ErrCorruptedLog = errors.New("corrupted log entry")
    ErrDiskFull = errors.New("disk full")
    ErrIOError = errors.New("I/O error")
)
```

### 错误恢复策略

1. **校验和错误**：尝试读取下一条记录
2. **文件损坏**：从最后一个有效检查点恢复
3. **磁盘满**：触发紧急检查点并清理旧日志
4. **I/O 错误**：重试或切换到备用存储

## 性能设计

### 缓冲策略

1. **写缓冲**：批量写入减少 I/O 次数
2. **读缓存**：缓存热点日志记录
3. **内存池**：重用内存分配

### 刷盘策略

1. **同步刷盘**：每次写入后立即 fsync
2. **异步刷盘**：定期批量 fsync
3. **组提交**：多个事务合并刷盘

### 文件管理

1. **日志轮转**：当日志文件达到阈值时创建新文件
2. **文件压缩**：压缩旧日志文件
3. **文件清理**：删除已检查点的日志文件
