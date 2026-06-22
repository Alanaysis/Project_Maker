package coordinator

import (
	"context"
	"fmt"
	"sync"
	"time"

	"distributed-transaction/participant"
	"distributed-transaction/pkg/utils"
	"distributed-transaction/transaction"
)

// Result 事务执行结果
type Result struct {
	TransactionID string
	Status        string
	Error         error
	Duration      time.Duration
}

// String 返回结果的字符串表示
func (r *Result) String() string {
	return fmt.Sprintf("Transaction %s: %s (Duration: %v)", r.TransactionID, r.Status, r.Duration)
}

// Coordinator 2PC协调者
type Coordinator struct {
	id             string
	cohorts        []participant.Cohort
	logger         *utils.Logger
	prepareTimeout time.Duration
	commitTimeout  time.Duration
	mu             sync.RWMutex
}

// NewCoordinator 创建新协调者
func NewCoordinator(id string) *Coordinator {
	return &Coordinator{
		id:             id,
		cohorts:        make([]participant.Cohort, 0),
		logger:         utils.NewLogger(fmt.Sprintf("Coordinator-%s", id)),
		prepareTimeout: 5 * time.Second,
		commitTimeout:  5 * time.Second,
	}
}

// RegisterCohort 注册参与者
func (c *Coordinator) RegisterCohort(ch participant.Cohort) error {
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

// CohortCount 返回已注册的参与者数量
func (c *Coordinator) CohortCount() int {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return len(c.cohorts)
}

// SetPrepareTimeout 设置准备阶段超时时间
func (c *Coordinator) SetPrepareTimeout(timeout time.Duration) {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.prepareTimeout = timeout
}

// SetCommitTimeout 设置提交阶段超时时间
func (c *Coordinator) SetCommitTimeout(timeout time.Duration) {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.commitTimeout = timeout
}

// ExecuteTransaction 执行分布式事务（2PC）
//
// 流程：
//  1. 准备阶段：向所有参与者发送Prepare请求
//     - 如果所有参与者同意，进入提交阶段
//     - 如果有参与者拒绝或超时，进入回滚阶段
//  2. 提交阶段：向所有参与者发送Commit请求
//     - 如果所有参与者提交成功，事务完成
//     - 如果有参与者提交失败，记录错误（此时无法回滚）
//  3. 回滚阶段（异常路径）：向所有参与者发送Abort请求
func (c *Coordinator) ExecuteTransaction(tx *transaction.Transaction) (*Result, error) {
	start := time.Now()
	c.logger.Info("========== 2PC Transaction %s Started ==========", tx.ID)

	// 阶段1：准备阶段
	c.logger.Info("Phase 1: PREPARE")
	tx.SetState(transaction.TxStatePreparing)

	if err := c.PreparePhase(tx); err != nil {
		c.logger.Error("Prepare phase failed: %v", err)
		tx.SetState(transaction.TxStateAborting)
		c.AbortPhase(tx) // 尽力回滚
		tx.SetState(transaction.TxStateAborted)
		result := &Result{
			TransactionID: tx.ID,
			Status:        "ABORTED",
			Error:         err,
			Duration:      time.Since(start),
		}
		c.logger.Info("========== %s ==========", result)
		return result, err
	}

	tx.SetState(transaction.TxStatePrepared)
	c.logger.Info("Phase 1: PREPARE completed successfully")

	// 阶段2：提交阶段
	c.logger.Info("Phase 2: COMMIT")
	tx.SetState(transaction.TxStateCommitting)

	if err := c.CommitPhase(tx); err != nil {
		c.logger.Error("Commit phase failed: %v", err)
		// 注意：在2PC中，如果Commit阶段部分失败，已经提交的参与者无法回滚
		// 这是2PC的一个已知问题
		tx.SetState(transaction.TxStateAborted)
		result := &Result{
			TransactionID: tx.ID,
			Status:        "PARTIAL_COMMIT",
			Error:         err,
			Duration:      time.Since(start),
		}
		c.logger.Info("========== %s ==========", result)
		return result, err
	}

	tx.SetState(transaction.TxStateCommitted)
	result := &Result{
		TransactionID: tx.ID,
		Status:        "COMMITTED",
		Duration:      time.Since(start),
	}
	c.logger.Info("Phase 2: COMMIT completed successfully")
	c.logger.Info("========== %s ==========", result)
	return result, nil
}

// PreparePhase 准备阶段：向所有参与者发送Prepare请求
func (c *Coordinator) PreparePhase(tx *transaction.Transaction) error {
	c.mu.RLock()
	cohorts := make([]participant.Cohort, len(c.cohorts))
	copy(cohorts, c.cohorts)
	timeout := c.prepareTimeout
	c.mu.RUnlock()

	if len(cohorts) == 0 {
		return fmt.Errorf("no cohorts registered")
	}

	// 创建带超时的context
	ctx, cancel := context.WithTimeout(context.Background(), timeout)
	defer cancel()

	// 并发执行Prepare
	errChan := make(chan error, len(cohorts))
	var wg sync.WaitGroup

	for _, ch := range cohorts {
		wg.Add(1)
		go func(cohort participant.Cohort) {
			defer wg.Done()

			select {
			case <-ctx.Done():
				errChan <- fmt.Errorf("prepare timeout for participant %s", cohort.ID())
				return
			default:
				if err := cohort.Prepare(tx); err != nil {
					errChan <- fmt.Errorf("participant %s: %v", cohort.ID(), err)
				}
			}
		}(ch)
	}

	// 等待所有Prepare完成
	wg.Wait()
	close(errChan)

	// 收集错误
	var errors []error
	for err := range errChan {
		errors = append(errors, err)
	}

	if len(errors) > 0 {
		return fmt.Errorf("prepare phase failed: %v", errors)
	}

	return nil
}

// CommitPhase 提交阶段：向所有参与者发送Commit请求
func (c *Coordinator) CommitPhase(tx *transaction.Transaction) error {
	c.mu.RLock()
	cohorts := make([]participant.Cohort, len(c.cohorts))
	copy(cohorts, c.cohorts)
	timeout := c.commitTimeout
	c.mu.RUnlock()

	// 创建带超时的context
	ctx, cancel := context.WithTimeout(context.Background(), timeout)
	defer cancel()

	// 并发执行Commit
	errChan := make(chan error, len(cohorts))
	var wg sync.WaitGroup

	for _, ch := range cohorts {
		wg.Add(1)
		go func(cohort participant.Cohort) {
			defer wg.Done()

			select {
			case <-ctx.Done():
				errChan <- fmt.Errorf("commit timeout for participant %s", cohort.ID())
				return
			default:
				if err := cohort.Commit(tx); err != nil {
					errChan <- fmt.Errorf("participant %s: %v", cohort.ID(), err)
				}
			}
		}(ch)
	}

	// 等待所有Commit完成
	wg.Wait()
	close(errChan)

	// 收集错误
	var errors []error
	for err := range errChan {
		errors = append(errors, err)
	}

	if len(errors) > 0 {
		return fmt.Errorf("commit phase failed: %v", errors)
	}

	return nil
}

// AbortPhase 回滚阶段：向所有参与者发送Abort请求
func (c *Coordinator) AbortPhase(tx *transaction.Transaction) error {
	c.mu.RLock()
	cohorts := make([]participant.Cohort, len(c.cohorts))
	copy(cohorts, c.cohorts)
	c.mu.RUnlock()

	c.logger.Info("AbortPhase: sending abort to %d participants", len(cohorts))

	// 并发执行Abort
	errChan := make(chan error, len(cohorts))
	var wg sync.WaitGroup

	for _, ch := range cohorts {
		wg.Add(1)
		go func(cohort participant.Cohort) {
			defer wg.Done()
			if err := cohort.Abort(tx); err != nil {
				errChan <- fmt.Errorf("participant %s: %v", cohort.ID(), err)
			}
		}(ch)
	}

	// 等待所有Abort完成
	wg.Wait()
	close(errChan)

	// 收集错误
	var errors []error
	for err := range errChan {
		errors = append(errors, err)
	}

	if len(errors) > 0 {
		return fmt.Errorf("abort phase failed: %v", errors)
	}

	return nil
}
