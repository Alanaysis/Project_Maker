# 设计文档：分布式事务系统

## 1. 系统架构

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────┐
│                   应用层 (Application)                │
├─────────────────────────────────────────────────────┤
│               事务管理器 (Transaction Manager)         │
├─────────────────────────────────────────────────────┤
│         协调者 (Coordinator)                         │
│         ┌─────────┐ ┌─────────┐ ┌─────────┐        │
│         │ Cohort1 │ │ Cohort2 │ │ Cohort3 │        │
│         └─────────┘ └─────────┘ └─────────┘        │
├─────────────────────────────────────────────────────┤
│               资源管理器 (Resource Manager)            │
│         ┌─────────┐ ┌─────────┐ ┌─────────┐        │
│         │   DB1   │ │   DB2   │ │   DB3   │        │
│         └─────────┘ └─────────┘ └─────────┘        │
└─────────────────────────────────────────────────────┘
```

### 1.2 组件职责

| 组件 | 职责 |
|------|------|
| 应用层 | 发起事务请求 |
| 事务管理器 | 管理事务生命周期 |
| 协调者 | 协调分布式事务的执行 |
| 参与者 | 执行本地事务 |
| 资源管理器 | 管理本地资源（数据库等） |

## 2. 详细设计

### 2.1 事务模型

```go
// Transaction 表示一个分布式事务
type Transaction struct {
    ID        string
    Status    TransactionStatus
    Cohorts   []Cohort
    CreatedAt time.Time
    UpdatedAt time.Time
    Timeout   time.Duration
}

// TransactionStatus 事务状态
type TransactionStatus int

const (
    TxStatusInit      TransactionStatus = iota // 初始化
    TxStatusPreparing                          // 准备中
    TxStatusPrepared                           // 已准备
    TxStatusCommitting                         // 提交中
    TxStatusCommitted                          // 已提交
    TxStatusAborting                           // 回滚中
    TxStatusAborted                            // 已回滚
)
```

### 2.2 协调者设计

```go
// Coordinator 2PC协调者接口
type Coordinator interface {
    // RegisterCohort 注册参与者
    RegisterCohort(cohort Cohort) error
    
    // ExecuteTransaction 执行分布式事务
    ExecuteTransaction(tx *Transaction) (*Result, error)
    
    // PreparePhase 准备阶段
    PreparePhase(tx *Transaction) error
    
    // CommitPhase 提交阶段
    CommitPhase(tx *Transaction) error
    
    // AbortPhase 回滚阶段
    AbortPhase(tx *Transaction) error
}
```

### 2.3 参与者设计

```go
// Cohort 2PC参与者接口
type Cohort interface {
    // ID 返回参与者ID
    ID() string
    
    // Prepare 准备阶段：执行本地事务，锁定资源
    Prepare(tx *Transaction) error
    
    // Commit 提交阶段：提交本地事务
    Commit(tx *Transaction) error
    
    // Abort 回滚阶段：回滚本地事务
    Abort(tx *Transaction) error
    
    // Status 返回参与者状态
    Status() CohortStatus
}
```

### 2.4 3PC协调者设计

```go
// ThreePhaseCoordinator 3PC协调者接口
type ThreePhaseCoordinator interface {
    Coordinator
    
    // CanCommitPhase CanCommit阶段
    CanCommitPhase(tx *Transaction) error
    
    // PreCommitPhase PreCommit阶段
    PreCommitPhase(tx *Transaction) error
    
    // DoCommitPhase DoCommit阶段
    DoCommitPhase(tx *Transaction) error
}
```

## 3. 状态机设计

### 3.1 2PC状态转换

```
                    ┌──────────────────┐
                    │   Init (初始化)   │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │  Prepare (准备)   │
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
        ┌─────────┐   ┌─────────┐   ┌─────────┐
        │  Commit  │   │  Abort  │   │ Timeout │
        │  (提交)   │   │  (回滚)  │   │  (超时)  │
        └─────────┘   └─────────┘   └─────────┘
              │              │              │
              ▼              ▼              ▼
        ┌─────────────────────────────────────────┐
        │           Completed (完成)               │
        └─────────────────────────────────────────┘
```

### 3.2 3PC状态转换

```
                    ┌──────────────────┐
                    │   Init (初始化)   │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ CanCommit (可提交) │
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
        ┌─────────┐   ┌─────────┐   ┌─────────┐
        │PreCommit│   │  Abort  │   │ Timeout │
        │ (预提交)  │   │  (回滚)  │   │  (超时)  │
        └────┬────┘   └─────────┘   └─────────┘
             │
             ▼
        ┌──────────────────┐
        │  DoCommit (提交)   │
        └────────┬─────────┘
                 │
                 ▼
        ┌──────────────────┐
        │  Completed (完成)  │
        └──────────────────┘
```

## 4. 错误处理设计

### 4.1 错误类型

```go
// ErrorType 错误类型
type ErrorType int

const (
    ErrTimeout      ErrorType = iota // 超时错误
    ErrNetwork                       // 网络错误
    ErrParticipant                   // 参与者错误
    ErrCoordinator                   // 协调者错误
    ErrTransaction                   // 事务错误
)

// TransactionError 事务错误
type TransactionError struct {
    Type    ErrorType
    Message string
    Err     error
}
```

### 4.2 故障恢复策略

1. **协调者故障**
   - 使用备份协调者
   - 参与者超时后自行决定

2. **参与者故障**
   - 协调者等待超时后中止事务
   - 故障参与者恢复后清理资源

3. **网络分区**
   - 使用超时机制
   - 记录日志用于后续恢复

## 5. 性能优化设计

### 5.1 并发处理

```go
// 并发执行Prepare阶段
func (c *coordinator) PreparePhase(tx *Transaction) error {
    var wg sync.WaitGroup
    errChan := make(chan error, len(tx.Cohorts))
    
    for _, cohort := range tx.Cohorts {
        wg.Add(1)
        go func(ch Cohort) {
            defer wg.Done()
            if err := ch.Prepare(tx); err != nil {
                errChan <- err
            }
        }(cohort)
    }
    
    wg.Wait()
    close(errChan)
    
    // 检查是否有错误
    for err := range errChan {
        if err != nil {
            return err
        }
    }
    return nil
}
```

### 5.2 超时控制

```go
// 带超时的事务执行
func (c *coordinator) ExecuteTransaction(tx *Transaction) (*Result, error) {
    ctx, cancel := context.WithTimeout(context.Background(), tx.Timeout)
    defer cancel()
    
    select {
    case result := <-c.executeAsync(tx):
        return result, nil
    case <-ctx.Done():
        return nil, &TransactionError{
            Type:    ErrTimeout,
            Message: "transaction timeout",
        }
    }
}
```

## 6. 日志设计

### 6.1 日志格式

```
[2024-01-01 12:00:00] [INFO] [Coordinator] Transaction tx-1 started
[2024-01-01 12:00:01] [DEBUG] [Cohort-1] Prepare request received
[2024-01-01 12:00:02] [INFO] [Cohort-1] Prepare successful
[2024-01-01 12:00:03] [INFO] [Coordinator] Commit phase started
[2024-01-01 12:00:04] [INFO] [Coordinator] Transaction tx-1 committed
```

### 6.2 日志级别

- **DEBUG**: 详细的调试信息
- **INFO**: 关键操作信息
- **WARN**: 潜在问题警告
- **ERROR**: 错误信息

## 7. 配置设计

### 7.1 配置结构

```go
// Config 系统配置
type Config struct {
    // 超时配置
    PrepareTimeout time.Duration `yaml:"prepare_timeout"`
    CommitTimeout  time.Duration `yaml:"commit_timeout"`
    
    // 重试配置
    MaxRetries int           `yaml:"max_retries"`
    RetryDelay time.Duration `yaml:"retry_delay"`
    
    // 日志配置
    LogLevel string `yaml:"log_level"`
    LogFile  string `yaml:"log_file"`
    
    // 性能配置
    MaxConcurrent int `yaml:"max_concurrent"`
}
```

## 8. 测试策略

### 8.1 单元测试

- 测试各个组件的独立功能
- Mock外部依赖

### 8.2 集成测试

- 测试组件之间的交互
- 模拟真实的分布式环境

### 8.3 故障注入测试

- 模拟各种故障场景
- 验证系统的容错能力

## 9. 接口定义

### 9.1 核心接口

```go
// Message 消息接口
type Message interface {
    Type() MessageType
    Payload() interface{}
    Timestamp() time.Time
}

// Channel 通信通道接口
type Channel interface {
    Send(msg Message) error
    Receive() (Message, error)
    Close() error
}

// Logger 日志接口
type Logger interface {
    Debug(msg string, args ...interface{})
    Info(msg string, args ...interface{})
    Warn(msg string, args ...interface{})
    Error(msg string, args ...interface{})
}
```

## 10. 部署架构

### 10.1 单机部署

```
┌─────────────────────────────────────┐
│           应用服务器                  │
│  ┌─────────────────────────────────┐│
│  │      协调者 + 多个参与者         ││
│  └─────────────────────────────────┘│
│  ┌─────────────────────────────────┐│
│  │         本地数据库               ││
│  └─────────────────────────────────┘│
└─────────────────────────────────────┘
```

### 10.2 分布式部署

```
┌─────────────────────────────────────┐
│        负载均衡器 (Load Balancer)    │
└─────────────────────────────────────┘
                    │
    ┌───────────────┼───────────────┐
    │               │               │
    ▼               ▼               ▼
┌─────────┐   ┌─────────┐   ┌─────────┐
│协调者节点1│   │协调者节点2│   │协调者节点3│
└─────────┘   └─────────┘   └─────────┘
    │               │               │
    ▼               ▼               ▼
┌─────────┐   ┌─────────┐   ┌─────────┐
│参与者节点1│   │参与者节点2│   │参与者节点3│
└─────────┘   └─────────┘   └─────────┘
```

## 11. 未来扩展

### 11.1 可扩展性

1. **动态参与者注册**：支持运行时添加/移除参与者
2. **分布式协调者**：支持多个协调者节点
3. **跨数据中心**：支持跨数据中心的分布式事务

### 11.2 监控和运维

1. **指标收集**：收集事务性能指标
2. **告警系统**：异常情况告警
3. **管理界面**：可视化管理工具

### 11.3 高级特性

1. **读写分离**：优化读操作性能
2. **分片支持**：支持数据分片
3. **缓存集成**：集成分布式缓存
