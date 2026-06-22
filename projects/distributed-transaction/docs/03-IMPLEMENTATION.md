# 实现细节文档

## 1. 项目结构

```
distributed-transaction/
├── cmd/
│   └── main.go                 # 主程序入口
├── internal/
│   ├── coordinator/
│   │   ├── coordinator.go      # 2PC协调者实现
│   │   └── three_phase.go      # 3PC协调者实现
│   ├── cohort/
│   │   └── cohort.go           # 参与者实现
│   └── transaction/
│       ├── transaction.go      # 事务定义
│       └── status.go           # 状态管理
├── pkg/
│   └── utils/
│       ├── logger.go           # 日志工具
│       └── errors.go           # 错误定义
└── test/
    ├── coordinator_test.go     # 协调者测试
    ├── cohort_test.go          # 参与者测试
    └── integration_test.go     # 集成测试
```

## 2. 核心实现

### 2.1 事务定义 (transaction/transaction.go)

```go
package transaction

import (
    "sync"
    "time"
)

// Status 事务状态
type Status int

const (
    StatusInit      Status = iota // 初始化
    StatusPreparing               // 准备中
    StatusPrepared                // 已准备
    StatusCommitting              // 提交中
    StatusCommitted               // 已提交
    StatusAborting                // 回滚中
    StatusAborted                 // 已回滚
)

// String 返回状态字符串
func (s Status) String() string {
    switch s {
    case StatusInit:
        return "INIT"
    case StatusPreparing:
        return "PREPARING"
    case StatusPrepared:
        return "PREPARED"
    case StatusCommitting:
        return "COMMITTING"
    case StatusCommitted:
        return "COMMITTED"
    case StatusAborting:
        return "ABORTING"
    case StatusAborted:
        return "ABORTED"
    default:
        return "UNKNOWN"
    }
}

// Transaction 事务
type Transaction struct {
    ID        string
    Status    Status
    Data      map[string]interface{}
    CreatedAt time.Time
    UpdatedAt time.Time
    mu        sync.RWMutex
}

// NewTransaction 创建新事务
func NewTransaction(id string) *Transaction {
    now := time.Now()
    return &Transaction{
        ID:        id,
        Status:    StatusInit,
        Data:      make(map[string]interface{}),
        CreatedAt: now,
        UpdatedAt: now,
    }
}

// SetStatus 设置事务状态
func (t *Transaction) SetStatus(status Status) {
    t.mu.Lock()
    defer t.mu.Unlock()
    t.Status = status
    t.UpdatedAt = time.Now()
}

// GetStatus 获取事务状态
func (t *Transaction) GetStatus() Status {
    t.mu.RLock()
    defer t.mu.RUnlock()
    return t.Status
}

// SetData 设置事务数据
func (t *Transaction) SetData(key string, value interface{}) {
    t.mu.Lock()
    defer t.mu.Unlock()
    t.Data[key] = value
    t.UpdatedAt = time.Now()
}

// GetData 获取事务数据
func (t *Transaction) GetData(key string) (interface{}, bool) {
    t.mu.RLock()
    defer t.mu.RUnlock()
    val, ok := t.Data[key]
    return val, ok
}
```

### 2.2 参与者实现 (cohort/cohort.go)

```go
package cohort

import (
    "fmt"
    "math/rand"
    "sync"
    "time"
    
    "distributed-transaction/internal/transaction"
    "distributed-transaction/pkg/utils"
)

// Status 参与者状态
type Status int

const (
    StatusReady    Status = iota // 就绪
    StatusPreparing              // 准备中
    StatusPrepared               // 已准备
    StatusCommitting             // 提交中
    StatusCommitted              // 已提交
    StatusAborting               // 回滚中
    StatusAborted                // 已回滚
    StatusFailed                 // 失败
)

// Cohort 参与者
type Cohort struct {
    id            string
    status        Status
    preparedTx    map[string]*transaction.Transaction
    logger        *utils.Logger
    simulateError bool // 用于测试：模拟错误
    simulateDelay bool // 用于测试：模拟延迟
    mu            sync.RWMutex
}

// NewCohort 创建新参与者
func NewCohort(id string) *Cohort {
    return &Cohort{
        id:         id,
        status:     StatusReady,
        preparedTx: make(map[string]*transaction.Transaction),
        logger:     utils.NewLogger(fmt.Sprintf("Cohort-%s", id)),
    }
}

// ID 返回参与者ID
func (c *Cohort) ID() string {
    return c.id
}

// Status 返回参与者状态
func (c *Cohort) Status() Status {
    c.mu.RLock()
    defer c.mu.RUnlock()
    return c.status
}

// SetSimulateError 设置是否模拟错误
func (c *Cohort) SetSimulateError(simulate bool) {
    c.mu.Lock()
    defer c.mu.Unlock()
    c.simulateError = simulate
}

// SetSimulateDelay 设置是否模拟延迟
func (c *Cohort) SetSimulateDelay(simulate bool) {
    c.mu.Lock()
    defer c.mu.Unlock()
    c.simulateDelay = simulate
}

// Prepare 准备阶段
func (c *Cohort) Prepare(tx *transaction.Transaction) error {
    c.mu.Lock()
    defer c.mu.Unlock()
    
    c.logger.Info("Prepare request received for transaction %s", tx.ID)
    
    // 模拟延迟
    if c.simulateDelay {
        time.Sleep(time.Duration(rand.Intn(100)) * time.Millisecond)
    }
    
    // 模拟错误
    if c.simulateError {
        c.status = StatusFailed
        return fmt.Errorf("cohort %s: prepare failed", c.id)
    }
    
    c.status = StatusPreparing
    
    // 执行本地准备操作
    if err := c.doPrepare(tx); err != nil {
        c.status = StatusFailed
        return err
    }
    
    // 记录已准备的事务
    c.preparedTx[tx.ID] = tx
    c.status = StatusPrepared
    
    c.logger.Info("Prepare successful for transaction %s", tx.ID)
    return nil
}

// doPrepare 执行本地准备操作
func (c *Cohort) doPrepare(tx *transaction.Transaction) error {
    // 模拟本地事务操作
    c.logger.Debug("Executing local prepare for transaction %s", tx.ID)
    
    // 这里可以添加实际的本地事务逻辑
    // 例如：锁定数据库行、记录日志等
    
    return nil
}

// Commit 提交阶段
func (c *Cohort) Commit(tx *transaction.Transaction) error {
    c.mu.Lock()
    defer c.mu.Unlock()
    
    c.logger.Info("Commit request received for transaction %s", tx.ID)
    
    // 检查事务是否已准备
    if _, ok := c.preparedTx[tx.ID]; !ok {
        return fmt.Errorf("cohort %s: transaction %s not prepared", c.id, tx.ID)
    }
    
    c.status = StatusCommitting
    
    // 执行本地提交操作
    if err := c.doCommit(tx); err != nil {
        c.status = StatusFailed
        return err
    }
    
    // 清理已提交的事务
    delete(c.preparedTx, tx.ID)
    c.status = StatusCommitted
    
    c.logger.Info("Commit successful for transaction %s", tx.ID)
    return nil
}

// doCommit 执行本地提交操作
func (c *Cohort) doCommit(tx *transaction.Transaction) error {
    // 模拟本地事务提交
    c.logger.Debug("Executing local commit for transaction %s", tx.ID)
    
    // 这里可以添加实际的本地提交逻辑
    // 例如：提交数据库事务、释放锁等
    
    return nil
}

// Abort 回滚阶段
func (c *Cohort) Abort(tx *transaction.Transaction) error {
    c.mu.Lock()
    defer c.mu.Unlock()
    
    c.logger.Info("Abort request received for transaction %s", tx.ID)
    
    c.status = StatusAborting
    
    // 执行本地回滚操作
    if err := c.doAbort(tx); err != nil {
        c.status = StatusFailed
        return err
    }
    
    // 清理已回滚的事务
    delete(c.preparedTx, tx.ID)
    c.status = StatusAborted
    
    c.logger.Info("Abort successful for transaction %s", tx.ID)
    return nil
}

// doAbort 执行本地回滚操作
func (c *Cohort) doAbort(tx *transaction.Transaction) error {
    // 模拟本地事务回滚
    c.logger.Debug("Executing local abort for transaction %s", tx.ID)
    
    // 这里可以添加实际的本地回滚逻辑
    // 例如：回滚数据库事务、释放锁等
    
    return nil
}
```

### 2.3 2PC协调者实现 (coordinator/coordinator.go)

```go
package coordinator

import (
    "context"
    "fmt"
    "sync"
    "time"
    
    "distributed-transaction/internal/cohort"
    "distributed-transaction/internal/transaction"
    "distributed-transaction/pkg/utils"
)

// Result 事务执行结果
type Result struct {
    TransactionID string
    Status        string
    Error         error
    Duration      time.Duration
}

// Coordinator 2PC协调者
type Coordinator struct {
    id            string
    cohorts       []cohort.Cohort
    logger        *utils.Logger
    prepareTimeout time.Duration
    commitTimeout  time.Duration
    mu            sync.RWMutex
}

// NewCoordinator 创建新协调者
func NewCoordinator(id string) *Coordinator {
    return &Coordinator{
        id:             id,
        cohorts:        make([]cohort.Cohort, 0),
        logger:         utils.NewLogger(fmt.Sprintf("Coordinator-%s", id)),
        prepareTimeout: 5 * time.Second,
        commitTimeout:  5 * time.Second,
    }
}

// RegisterCohort 注册参与者
func (c *Coordinator) RegisterCohort(ch cohort.Cohort) error {
    c.mu.Lock()
    defer c.mu.Unlock()
    
    // 检查是否已注册
    for _, existing := range c.cohorts {
        if existing.ID() == ch.ID() {
            return fmt.Errorf("cohort %s already registered", ch.ID())
        }
    }
    
    c.cohorts = append(c.cohorts, ch)
    c.logger.Info("Cohort %s registered", ch.ID())
    return nil
}

// ExecuteTransaction 执行分布式事务
func (c *Coordinator) ExecuteTransaction(tx *transaction.Transaction) (*Result, error) {
    start := time.Now()
    c.logger.Info("Starting transaction %s", tx.ID)
    
    // 阶段1：准备阶段
    tx.SetStatus(transaction.StatusPreparing)
    if err := c.PreparePhase(tx); err != nil {
        c.logger.Error("Prepare phase failed: %v", err)
        tx.SetStatus(transaction.StatusAborting)
        c.AbortPhase(tx)
        return &Result{
            TransactionID: tx.ID,
            Status:        "ABORTED",
            Error:         err,
            Duration:      time.Since(start),
        }, err
    }
    
    tx.SetStatus(transaction.StatusPrepared)
    c.logger.Info("Prepare phase completed for transaction %s", tx.ID)
    
    // 阶段2：提交阶段
    tx.SetStatus(transaction.StatusCommitting)
    if err := c.CommitPhase(tx); err != nil {
        c.logger.Error("Commit phase failed: %v", err)
        tx.SetStatus(transaction.StatusAborting)
        c.AbortPhase(tx)
        return &Result{
            TransactionID: tx.ID,
            Status:        "ABORTED",
            Error:         err,
            Duration:      time.Since(start),
        }, err
    }
    
    tx.SetStatus(transaction.StatusCommitted)
    c.logger.Info("Transaction %s committed successfully", tx.ID)
    
    return &Result{
        TransactionID: tx.ID,
        Status:        "COMMITTED",
        Duration:      time.Since(start),
    }, nil
}

// PreparePhase 准备阶段
func (c *Coordinator) PreparePhase(tx *transaction.Transaction) error {
    c.mu.RLock()
    cohorts := make([]cohort.Cohort, len(c.cohorts))
    copy(cohorts, c.cohorts)
    c.mu.RUnlock()
    
    if len(cohorts) == 0 {
        return fmt.Errorf("no cohorts registered")
    }
    
    // 创建带超时的context
    ctx, cancel := context.WithTimeout(context.Background(), c.prepareTimeout)
    defer cancel()
    
    // 并发执行Prepare
    errChan := make(chan error, len(cohorts))
    var wg sync.WaitGroup
    
    for _, ch := range cohorts {
        wg.Add(1)
        go func(cohort cohort.Cohort) {
            defer wg.Done()
            
            select {
            case <-ctx.Done():
                errChan <- fmt.Errorf("prepare timeout for cohort %s", cohort.ID())
                return
            default:
                if err := cohort.Prepare(tx); err != nil {
                    errChan <- fmt.Errorf("cohort %s: %v", cohort.ID(), err)
                }
            }
        }(ch)
    }
    
    // 等待所有Prepare完成
    wg.Wait()
    close(errChan)
    
    // 检查是否有错误
    var errors []error
    for err := range errChan {
        errors = append(errors, err)
    }
    
    if len(errors) > 0 {
        return fmt.Errorf("prepare phase failed: %v", errors)
    }
    
    return nil
}

// CommitPhase 提交阶段
func (c *Coordinator) CommitPhase(tx *transaction.Transaction) error {
    c.mu.RLock()
    cohorts := make([]cohort.Cohort, len(c.cohorts))
    copy(cohorts, c.cohorts)
    c.mu.RUnlock()
    
    // 创建带超时的context
    ctx, cancel := context.WithTimeout(context.Background(), c.commitTimeout)
    defer cancel()
    
    // 并发执行Commit
    errChan := make(chan error, len(cohorts))
    var wg sync.WaitGroup
    
    for _, ch := range cohorts {
        wg.Add(1)
        go func(cohort cohort.Cohort) {
            defer wg.Done()
            
            select {
            case <-ctx.Done():
                errChan <- fmt.Errorf("commit timeout for cohort %s", cohort.ID())
                return
            default:
                if err := cohort.Commit(tx); err != nil {
                    errChan <- fmt.Errorf("cohort %s: %v", cohort.ID(), err)
                }
            }
        }(ch)
    }
    
    // 等待所有Commit完成
    wg.Wait()
    close(errChan)
    
    // 检查是否有错误
    var errors []error
    for err := range errChan {
        errors = append(errors, err)
    }
    
    if len(errors) > 0 {
        return fmt.Errorf("commit phase failed: %v", errors)
    }
    
    return nil
}

// AbortPhase 回滚阶段
func (c *Coordinator) AbortPhase(tx *transaction.Transaction) error {
    c.mu.RLock()
    cohorts := make([]cohort.Cohort, len(c.cohorts))
    copy(cohorts, c.cohorts)
    c.mu.RUnlock()
    
    // 并发执行Abort
    errChan := make(chan error, len(cohorts))
    var wg sync.WaitGroup
    
    for _, ch := range cohorts {
        wg.Add(1)
        go func(cohort cohort.Cohort) {
            defer wg.Done()
            if err := cohort.Abort(tx); err != nil {
                errChan <- fmt.Errorf("cohort %s: %v", cohort.ID(), err)
            }
        }(ch)
    }
    
    // 等待所有Abort完成
    wg.Wait()
    close(errChan)
    
    // 检查是否有错误
    var errors []error
    for err := range errChan {
        errors = append(errors, err)
    }
    
    if len(errors) > 0 {
        return fmt.Errorf("abort phase failed: %v", errors)
    }
    
    return nil
}
```

### 2.4 3PC协调者实现 (coordinator/three_phase.go)

```go
package coordinator

import (
    "context"
    "fmt"
    "sync"
    "time"
    
    "distributed-transaction/internal/cohort"
    "distributed-transaction/internal/transaction"
    "distributed-transaction/pkg/utils"
)

// ThreePhaseCoordinator 3PC协调者
type ThreePhaseCoordinator struct {
    *Coordinator
    canCommitTimeout  time.Duration
    preCommitTimeout  time.Duration
    doCommitTimeout   time.Duration
}

// NewThreePhaseCoordinator 创建3PC协调者
func NewThreePhaseCoordinator(id string) *ThreePhaseCoordinator {
    base := NewCoordinator(id)
    return &ThreePhaseCoordinator{
        Coordinator:       base,
        canCommitTimeout:  3 * time.Second,
        preCommitTimeout:  3 * time.Second,
        doCommitTimeout:   3 * time.Second,
    }
}

// ExecuteTransaction 执行分布式事务（3PC版本）
func (c *ThreePhaseCoordinator) ExecuteTransaction(tx *transaction.Transaction) (*Result, error) {
    start := time.Now()
    c.logger.Info("Starting 3PC transaction %s", tx.ID)
    
    // 阶段1：CanCommit
    tx.SetStatus(transaction.StatusPreparing)
    if err := c.CanCommitPhase(tx); err != nil {
        c.logger.Error("CanCommit phase failed: %v", err)
        tx.SetStatus(transaction.StatusAborting)
        c.AbortPhase(tx)
        return &Result{
            TransactionID: tx.ID,
            Status:        "ABORTED",
            Error:         err,
            Duration:      time.Since(start),
        }, err
    }
    
    c.logger.Info("CanCommit phase completed for transaction %s", tx.ID)
    
    // 阶段2：PreCommit
    if err := c.PreCommitPhase(tx); err != nil {
        c.logger.Error("PreCommit phase failed: %v", err)
        tx.SetStatus(transaction.StatusAborting)
        c.AbortPhase(tx)
        return &Result{
            TransactionID: tx.ID,
            Status:        "ABORTED",
            Error:         err,
            Duration:      time.Since(start),
        }, err
    }
    
    c.logger.Info("PreCommit phase completed for transaction %s", tx.ID)
    
    // 阶段3：DoCommit
    tx.SetStatus(transaction.StatusCommitting)
    if err := c.DoCommitPhase(tx); err != nil {
        c.logger.Error("DoCommit phase failed: %v", err)
        // 在3PC中，如果DoCommit失败，参与者可以在超时后自行提交
        // 这里我们仍然尝试回滚
        tx.SetStatus(transaction.StatusAborting)
        c.AbortPhase(tx)
        return &Result{
            TransactionID: tx.ID,
            Status:        "ABORTED",
            Error:         err,
            Duration:      time.Since(start),
        }, err
    }
    
    tx.SetStatus(transaction.StatusCommitted)
    c.logger.Info("3PC transaction %s committed successfully", tx.ID)
    
    return &Result{
        TransactionID: tx.ID,
        Status:        "COMMITTED",
        Duration:      time.Since(start),
    }, nil
}

// CanCommitPhase CanCommit阶段
func (c *ThreePhaseCoordinator) CanCommitPhase(tx *transaction.Transaction) error {
    c.mu.RLock()
    cohorts := make([]cohort.Cohort, len(c.cohorts))
    copy(cohorts, c.cohorts)
    c.mu.RUnlock()
    
    if len(cohorts) == 0 {
        return fmt.Errorf("no cohorts registered")
    }
    
    // 创建带超时的context
    ctx, cancel := context.WithTimeout(context.Background(), c.canCommitTimeout)
    defer cancel()
    
    // 并发执行CanCommit
    errChan := make(chan error, len(cohorts))
    var wg sync.WaitGroup
    
    for _, ch := range cohorts {
        wg.Add(1)
        go func(cohort cohort.Cohort) {
            defer wg.Done()
            
            select {
            case <-ctx.Done():
                errChan <- fmt.Errorf("canCommit timeout for cohort %s", cohort.ID())
                return
            default:
                // 在3PC的CanCommit阶段，参与者只检查是否可以提交
                // 不执行实际的本地事务
                c.logger.Debug("CanCommit check for cohort %s", cohort.ID())
            }
        }(ch)
    }
    
    // 等待所有CanCommit完成
    wg.Wait()
    close(errChan)
    
    // 检查是否有错误
    var errors []error
    for err := range errChan {
        errors = append(errors, err)
    }
    
    if len(errors) > 0 {
        return fmt.Errorf("canCommit phase failed: %v", errors)
    }
    
    return nil
}

// PreCommitPhase PreCommit阶段
func (c *ThreePhaseCoordinator) PreCommitPhase(tx *transaction.Transaction) error {
    c.mu.RLock()
    cohorts := make([]cohort.Cohort, len(c.cohorts))
    copy(cohorts, c.cohorts)
    c.mu.RUnlock()
    
    // 创建带超时的context
    ctx, cancel := context.WithTimeout(context.Background(), c.preCommitTimeout)
    defer cancel()
    
    // 并发执行PreCommit（相当于2PC的Prepare）
    errChan := make(chan error, len(cohorts))
    var wg sync.WaitGroup
    
    for _, ch := range cohorts {
        wg.Add(1)
        go func(cohort cohort.Cohort) {
            defer wg.Done()
            
            select {
            case <-ctx.Done():
                errChan <- fmt.Errorf("preCommit timeout for cohort %s", cohort.ID())
                return
            default:
                if err := cohort.Prepare(tx); err != nil {
                    errChan <- fmt.Errorf("cohort %s: %v", cohort.ID(), err)
                }
            }
        }(ch)
    }
    
    // 等待所有PreCommit完成
    wg.Wait()
    close(errChan)
    
    // 检查是否有错误
    var errors []error
    for err := range errChan {
        errors = append(errors, err)
    }
    
    if len(errors) > 0 {
        return fmt.Errorf("preCommit phase failed: %v", errors)
    }
    
    return nil
}

// DoCommitPhase DoCommit阶段
func (c *ThreePhaseCoordinator) DoCommitPhase(tx *transaction.Transaction) error {
    // 使用基类的CommitPhase实现
    return c.CommitPhase(tx)
}
```

## 3. 工具包实现

### 3.1 日志工具 (pkg/utils/logger.go)

```go
package utils

import (
    "fmt"
    "log"
    "os"
    "sync"
    "time"
)

// LogLevel 日志级别
type LogLevel int

const (
    LogLevelDebug LogLevel = iota
    LogLevelInfo
    LogLevelWarn
    LogLevelError
)

// Logger 日志记录器
type Logger struct {
    prefix string
    level  LogLevel
    logger *log.Logger
    mu     sync.Mutex
}

// NewLogger 创建日志记录器
func NewLogger(prefix string) *Logger {
    return &Logger{
        prefix: prefix,
        level:  LogLevelInfo,
        logger: log.New(os.Stdout, "", 0),
    }
}

// SetLevel 设置日志级别
func (l *Logger) SetLevel(level LogLevel) {
    l.mu.Lock()
    defer l.mu.Unlock()
    l.level = level
}

// Debug 输出调试日志
func (l *Logger) Debug(format string, args ...interface{}) {
    l.log(LogLevelDebug, format, args...)
}

// Info 输出信息日志
func (l *Logger) Info(format string, args ...interface{}) {
    l.log(LogLevelInfo, format, args...)
}

// Warn 输出警告日志
func (l *Logger) Warn(format string, args ...interface{}) {
    l.log(LogLevelWarn, format, args...)
}

// Error 输出错误日志
func (l *Logger) Error(format string, args ...interface{}) {
    l.log(LogLevelError, format, args...)
}

// log 输出日志
func (l *Logger) log(level LogLevel, format string, args ...interface{}) {
    l.mu.Lock()
    defer l.mu.Unlock()
    
    if level < l.level {
        return
    }
    
    timestamp := time.Now().Format("2006-01-02 15:04:05")
    levelStr := l.levelString(level)
    message := fmt.Sprintf(format, args...)
    
    l.logger.Printf("[%s] [%s] [%s] %s", timestamp, levelStr, l.prefix, message)
}

// levelString 返回日志级别字符串
func (l *Logger) levelString(level LogLevel) string {
    switch level {
    case LogLevelDebug:
        return "DEBUG"
    case LogLevelInfo:
        return "INFO"
    case LogLevelWarn:
        return "WARN"
    case LogLevelError:
        return "ERROR"
    default:
        return "UNKNOWN"
    }
}
```

### 3.2 错误定义 (pkg/utils/errors.go)

```go
package utils

import "fmt"

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

// Error 实现error接口
func (e *TransactionError) Error() string {
    if e.Err != nil {
        return fmt.Sprintf("%s: %v", e.Message, e.Err)
    }
    return e.Message
}

// Unwrap 返回包装的错误
func (e *TransactionError) Unwrap() error {
    return e.Err
}

// NewTimeoutError 创建超时错误
func NewTimeoutError(message string) *TransactionError {
    return &TransactionError{
        Type:    ErrTimeout,
        Message: message,
    }
}

// NewParticipantError 创建参与者错误
func NewParticipantError(message string, err error) *TransactionError {
    return &TransactionError{
        Type:    ErrParticipant,
        Message: message,
        Err:     err,
    }
}

// NewCoordinatorError 创建协调者错误
func NewCoordinatorError(message string, err error) *TransactionError {
    return &TransactionError{
        Type:    ErrCoordinator,
        Message: message,
        Err:     err,
    }
}
```

## 4. 主程序实现

### 4.1 示例程序 (cmd/main.go)

```go
package main

import (
    "flag"
    "fmt"
    "log"
    
    "distributed-transaction/internal/cohort"
    "distributed-transaction/internal/coordinator"
    "distributed-transaction/internal/transaction"
)

func main() {
    mode := flag.String("mode", "2pc", "Transaction mode: 2pc or 3pc")
    flag.Parse()
    
    fmt.Printf("Starting distributed transaction demo in %s mode\n", *mode)
    
    switch *mode {
    case "2pc":
        run2PCDemo()
    case "3pc":
        run3PCDemo()
    default:
        log.Fatalf("Unknown mode: %s", *mode)
    }
}

func run2PCDemo() {
    fmt.Println("\n=== 2PC Transaction Demo ===\n")
    
    // 创建协调者
    coord := coordinator.NewCoordinator("coordinator-1")
    
    // 创建参与者
    cohort1 := cohort.NewCohort("cohort-1")
    cohort2 := cohort.NewCohort("cohort-2")
    cohort3 := cohort.NewCohort("cohort-3")
    
    // 注册参与者
    if err := coord.RegisterCohort(cohort1); err != nil {
        log.Fatal(err)
    }
    if err := coord.RegisterCohort(cohort2); err != nil {
        log.Fatal(err)
    }
    if err := coord.RegisterCohort(cohort3); err != nil {
        log.Fatal(err)
    }
    
    // 创建事务
    tx := transaction.NewTransaction("tx-1")
    
    // 执行事务
    result, err := coord.ExecuteTransaction(tx)
    if err != nil {
        fmt.Printf("Transaction failed: %v\n", err)
    } else {
        fmt.Printf("Transaction %s: %s (Duration: %v)\n", 
            result.TransactionID, result.Status, result.Duration)
    }
    
    // 演示失败场景
    fmt.Println("\n=== Failed Transaction Demo ===\n")
    
    // 创建会失败的参与者
    failingCohort := cohort.NewCohort("failing-cohort")
    failingCohort.SetSimulateError(true)
    
    coord2 := coordinator.NewCoordinator("coordinator-2")
    coord2.RegisterCohort(failingCohort)
    
    tx2 := transaction.NewTransaction("tx-2")
    result2, err := coord2.ExecuteTransaction(tx2)
    if err != nil {
        fmt.Printf("Transaction failed as expected: %v\n", err)
    } else {
        fmt.Printf("Transaction %s: %s\n", result2.TransactionID, result2.Status)
    }
}

func run3PCDemo() {
    fmt.Println("\n=== 3PC Transaction Demo ===\n")
    
    // 创建3PC协调者
    coord := coordinator.NewThreePhaseCoordinator("coordinator-1")
    
    // 创建参与者
    cohort1 := cohort.NewCohort("cohort-1")
    cohort2 := cohort.NewCohort("cohort-2")
    
    // 注册参与者
    if err := coord.RegisterCohort(cohort1); err != nil {
        log.Fatal(err)
    }
    if err := coord.RegisterCohort(cohort2); err != nil {
        log.Fatal(err)
    }
    
    // 创建事务
    tx := transaction.NewTransaction("tx-1")
    
    // 执行事务
    result, err := coord.ExecuteTransaction(tx)
    if err != nil {
        fmt.Printf("Transaction failed: %v\n", err)
    } else {
        fmt.Printf("Transaction %s: %s (Duration: %v)\n", 
            result.TransactionID, result.Status, result.Duration)
    }
}
```

## 5. 实现要点

### 5.1 并发安全

- 使用`sync.Mutex`和`sync.RWMutex`保护共享资源
- 使用`sync.WaitGroup`等待并发操作完成
- 使用`context`控制超时

### 5.2 错误处理

- 定义明确的错误类型
- 使用`fmt.Errorf`包装错误
- 提供错误链（Unwrap）

### 5.3 日志记录

- 记录关键操作
- 支持不同日志级别
- 包含时间戳和来源信息

### 5.4 测试支持

- 支持模拟错误（SimulateError）
- 支持模拟延迟（SimulateDelay）
- 便于测试各种故障场景
