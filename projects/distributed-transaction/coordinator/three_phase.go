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

// ThreePhaseCoordinator 三阶段提交协调者
//
// 3PC 协议在 2PC 基础上增加了 PreCommit 阶段，解决了 2PC 的阻塞问题：
//   - CanCommit:  询问参与者是否可以提交（不锁定资源）
//   - PreCommit:  如果所有参与者同意，发送预提交（锁定资源）
//   - DoCommit:   如果所有参与者预提交成功，执行最终提交
//
// 优势：如果协调者在 PreCommit 后崩溃，参与者可以自主决定提交或回滚
type ThreePhaseCoordinator struct {
	id              string
	cohorts         []participant.Cohort
	logger          *utils.Logger
	canTimeout      time.Duration
	preTimeout      time.Duration
	commitTimeout   time.Duration
	mu              sync.RWMutex
}

// NewThreePhaseCoordinator 创建3PC协调者
func NewThreePhaseCoordinator(id string) *ThreePhaseCoordinator {
	return &ThreePhaseCoordinator{
		id:            id,
		cohorts:       make([]participant.Cohort, 0),
		logger:        utils.NewLogger(fmt.Sprintf("3PC-Coordinator-%s", id)),
		canTimeout:    5 * time.Second,
		preTimeout:    5 * time.Second,
		commitTimeout: 5 * time.Second,
	}
}

// RegisterCohort 注册参与者
func (c *ThreePhaseCoordinator) RegisterCohort(ch participant.Cohort) error {
	c.mu.Lock()
	defer c.mu.Unlock()

	for _, existing := range c.cohorts {
		if existing.ID() == ch.ID() {
			return fmt.Errorf("cohort %s already registered", ch.ID())
		}
	}

	c.cohorts = append(c.cohorts, ch)
	c.logger.Info("Cohort %s registered", ch.ID())
	return nil
}

// SetCanTimeout 设置 CanCommit 阶段超时
func (c *ThreePhaseCoordinator) SetCanTimeout(timeout time.Duration) {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.canTimeout = timeout
}

// SetPreTimeout 设置 PreCommit 阶段超时
func (c *ThreePhaseCoordinator) SetPreTimeout(timeout time.Duration) {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.preTimeout = timeout
}

// SetCommitTimeout 设置 DoCommit 阶段超时
func (c *ThreePhaseCoordinator) SetCommitTimeout(timeout time.Duration) {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.commitTimeout = timeout
}

// ExecuteTransaction 执行三阶段提交事务
//
// 流程：
//
//	Phase 1: CanCommit - 询问所有参与者是否可以提交
//	  - 全部同意 -> Phase 2
//	  - 任一拒绝 -> 直接 Abort
//
//	Phase 2: PreCommit - 发送预提交，参与者锁定资源
//	  - 全部成功 -> Phase 3
//	  - 任一失败 -> Abort
//
//	Phase 3: DoCommit - 执行最终提交
//	  - 全部成功 -> COMMITTED
//	  - 任一失败 -> 记录错误（不回滚，已提交的无法撤回）
func (c *ThreePhaseCoordinator) ExecuteTransaction(tx *transaction.Transaction) (*Result, error) {
	start := time.Now()
	c.logger.Info("========== 3PC Transaction %s Started ==========", tx.ID)

	// Phase 1: CanCommit
	c.logger.Info("Phase 1: CanCommit")
	tx.SetState(transaction.TxStatePreparing)

	if err := c.CanCommitPhase(tx); err != nil {
		c.logger.Error("CanCommit phase failed: %v", err)
		tx.SetState(transaction.TxStateAborting)
		c.AbortAll(tx)
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
	c.logger.Info("Phase 1: CanCommit completed")

	// Phase 2: PreCommit
	c.logger.Info("Phase 2: PreCommit")
	tx.SetState(transaction.TxStatePrepared)

	if err := c.PreCommitPhase(tx); err != nil {
		c.logger.Error("PreCommit phase failed: %v", err)
		tx.SetState(transaction.TxStateAborting)
		c.AbortAll(tx)
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
	c.logger.Info("Phase 2: PreCommit completed")

	// Phase 3: DoCommit
	c.logger.Info("Phase 3: DoCommit")
	tx.SetState(transaction.TxStateCommitting)

	if err := c.DoCommitPhase(tx); err != nil {
		c.logger.Error("DoCommit phase failed: %v", err)
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
	c.logger.Info("Phase 3: DoCommit completed")
	c.logger.Info("========== %s ==========", result)
	return result, nil
}

// CanCommitPhase 第一阶段：询问参与者是否可以提交
// 参与者在此阶段不锁定资源，只做可行性检查
func (c *ThreePhaseCoordinator) CanCommitPhase(tx *transaction.Transaction) error {
	c.mu.RLock()
	cohorts := make([]participant.Cohort, len(c.cohorts))
	copy(cohorts, c.cohorts)
	timeout := c.canTimeout
	c.mu.RUnlock()

	if len(cohorts) == 0 {
		return fmt.Errorf("no cohorts registered")
	}

	ctx, cancel := context.WithTimeout(context.Background(), timeout)
	defer cancel()

	return c.executeOnAll(ctx, cohorts, tx, "CanCommit", func(ch participant.Cohort, t *transaction.Transaction) error {
		return ch.Prepare(t)
	})
}

// PreCommitPhase 第二阶段：发送预提交，参与者锁定资源
// 如果协调者在此阶段后崩溃，参与者可以超时后自主提交
func (c *ThreePhaseCoordinator) PreCommitPhase(tx *transaction.Transaction) error {
	c.mu.RLock()
	cohorts := make([]participant.Cohort, len(c.cohorts))
	copy(cohorts, c.cohorts)
	timeout := c.preTimeout
	c.mu.RUnlock()

	ctx, cancel := context.WithTimeout(context.Background(), timeout)
	defer cancel()

	// PreCommit 阶段使用 Prepare 进行资源锁定
	// 实际系统中这里会记录日志以便参与者自主恢复
	return c.executeOnAll(ctx, cohorts, tx, "PreCommit", func(ch participant.Cohort, t *transaction.Transaction) error {
		return ch.Prepare(t)
	})
}

// DoCommitPhase 第三阶段：执行最终提交
func (c *ThreePhaseCoordinator) DoCommitPhase(tx *transaction.Transaction) error {
	c.mu.RLock()
	cohorts := make([]participant.Cohort, len(c.cohorts))
	copy(cohorts, c.cohorts)
	timeout := c.commitTimeout
	c.mu.RUnlock()

	ctx, cancel := context.WithTimeout(context.Background(), timeout)
	defer cancel()

	return c.executeOnAll(ctx, cohorts, tx, "DoCommit", func(ch participant.Cohort, t *transaction.Transaction) error {
		return ch.Commit(t)
	})
}

// AbortAll 向所有参与者发送回滚请求
func (c *ThreePhaseCoordinator) AbortAll(tx *transaction.Transaction) {
	c.mu.RLock()
	cohorts := make([]participant.Cohort, len(c.cohorts))
	copy(cohorts, c.cohorts)
	c.mu.RUnlock()

	c.logger.Info("AbortAll: sending abort to %d participants", len(cohorts))

	var wg sync.WaitGroup
	errChan := make(chan error, len(cohorts))

	for _, ch := range cohorts {
		wg.Add(1)
		go func(cohort participant.Cohort) {
			defer wg.Done()
			if err := cohort.Abort(tx); err != nil {
				errChan <- fmt.Errorf("participant %s: %v", cohort.ID(), err)
			}
		}(ch)
	}

	wg.Wait()
	close(errChan)

	for err := range errChan {
		c.logger.Error("Abort error: %v", err)
	}
}

// executeOnAll 在所有参与者上并发执行操作
func (c *ThreePhaseCoordinator) executeOnAll(
	ctx context.Context,
	cohorts []participant.Cohort,
	tx *transaction.Transaction,
	phase string,
	action func(participant.Cohort, *transaction.Transaction) error,
) error {
	errChan := make(chan error, len(cohorts))
	var wg sync.WaitGroup

	for _, ch := range cohorts {
		wg.Add(1)
		go func(cohort participant.Cohort) {
			defer wg.Done()
			select {
			case <-ctx.Done():
				errChan <- fmt.Errorf("%s timeout for participant %s", phase, cohort.ID())
				return
			default:
				if err := action(cohort, tx); err != nil {
					errChan <- fmt.Errorf("participant %s: %v", cohort.ID(), err)
				}
			}
		}(ch)
	}

	wg.Wait()
	close(errChan)

	var errors []error
	for err := range errChan {
		errors = append(errors, err)
	}

	if len(errors) > 0 {
		return fmt.Errorf("%s phase failed: %v", phase, errors)
	}
	return nil
}
