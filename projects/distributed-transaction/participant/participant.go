package participant

import (
	"fmt"
	"math/rand"
	"sync"
	"time"

	"distributed-transaction/pkg/utils"
	"distributed-transaction/transaction"
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

func (s Status) String() string {
	switch s {
	case StatusReady:
		return "READY"
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
	case StatusFailed:
		return "FAILED"
	default:
		return "UNKNOWN"
	}
}

// Cohort 参与者接口
type Cohort interface {
	// ID 返回参与者ID
	ID() string
	// Prepare 准备阶段：执行本地事务，锁定资源
	Prepare(tx *transaction.Transaction) error
	// Commit 提交阶段：提交本地事务
	Commit(tx *transaction.Transaction) error
	// Abort 回滚阶段：回滚本地事务
	Abort(tx *transaction.Transaction) error
	// Status 返回参与者状态
	Status() Status
}

// DefaultCohort 默认参与者实现
type DefaultCohort struct {
	id            string
	status        Status
	preparedTx    map[string]*transaction.Transaction
	logger        *utils.Logger
	simulateError bool
	simulateDelay bool
	mu            sync.RWMutex
}

// NewDefaultCohort 创建新参与者
func NewDefaultCohort(id string) *DefaultCohort {
	return &DefaultCohort{
		id:         id,
		status:     StatusReady,
		preparedTx: make(map[string]*transaction.Transaction),
		logger:     utils.NewLogger(fmt.Sprintf("Participant-%s", id)),
	}
}

// ID 返回参与者ID
func (c *DefaultCohort) ID() string {
	return c.id
}

// Status 返回参与者状态
func (c *DefaultCohort) Status() Status {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.status
}

// SetSimulateError 设置是否模拟错误
func (c *DefaultCohort) SetSimulateError(simulate bool) {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.simulateError = simulate
}

// SetSimulateDelay 设置是否模拟延迟
func (c *DefaultCohort) SetSimulateDelay(simulate bool) {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.simulateDelay = simulate
}

// Prepare 准备阶段
func (c *DefaultCohort) Prepare(tx *transaction.Transaction) error {
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
		return fmt.Errorf("participant %s: prepare failed (simulated error)", c.id)
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

func (c *DefaultCohort) doPrepare(tx *transaction.Transaction) error {
	c.logger.Debug("Executing local prepare for transaction %s", tx.ID)
	// 实际场景中，这里会锁定数据库行、记录undo/redo日志等
	return nil
}

// Commit 提交阶段
func (c *DefaultCohort) Commit(tx *transaction.Transaction) error {
	c.mu.Lock()
	defer c.mu.Unlock()

	c.logger.Info("Commit request received for transaction %s", tx.ID)

	// 检查事务是否已准备
	if _, ok := c.preparedTx[tx.ID]; !ok {
		return fmt.Errorf("participant %s: transaction %s not prepared", c.id, tx.ID)
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

func (c *DefaultCohort) doCommit(tx *transaction.Transaction) error {
	c.logger.Debug("Executing local commit for transaction %s", tx.ID)
	// 实际场景中，这里会提交数据库事务、释放锁等
	return nil
}

// Abort 回滚阶段
func (c *DefaultCohort) Abort(tx *transaction.Transaction) error {
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

func (c *DefaultCohort) doAbort(tx *transaction.Transaction) error {
	c.logger.Debug("Executing local abort for transaction %s", tx.ID)
	// 实际场景中，这里会回滚数据库事务、释放锁等
	return nil
}
