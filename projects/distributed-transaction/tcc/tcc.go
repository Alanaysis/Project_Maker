package tcc

import (
	"fmt"
	"sync"

	"distributed-transaction/pkg/utils"
)

// TCCStatus TCC 事务状态
type TCCStatus int

const (
	TCCPending    TCCStatus = iota // 待执行
	TCCTrying                      // Try 阶段
	TCCConfirmed                   // 已确认
	TCCCancelled                   // 已取消
	TCCFailed                      // 失败
)

func (s TCCStatus) String() string {
	switch s {
	case TCCPending:
		return "PENDING"
	case TCCTrying:
		return "TRYING"
	case TCCConfirmed:
		return "CONFIRMED"
	case TCCCancelled:
		return "CANCELLED"
	case TCCFailed:
		return "FAILED"
	default:
		return "UNKNOWN"
	}
}

// ParticipantStatus 参与者状态
type ParticipantStatus int

const (
	ParticipantPending   ParticipantStatus = iota // 待执行
	ParticipantTried                              // Try 成功
	ParticipantConfirmed                          // Confirm 成功
	ParticipantCancelled                          // Cancel 成功
	ParticipantFailed                             // 失败
)

func (s ParticipantStatus) String() string {
	switch s {
	case ParticipantPending:
		return "PENDING"
	case ParticipantTried:
		return "TRIED"
	case ParticipantConfirmed:
		return "CONFIRMED"
	case ParticipantCancelled:
		return "CANCELLED"
	case ParticipantFailed:
		return "FAILED"
	default:
		return "UNKNOWN"
	}
}

// TCCFunc TCC 操作函数
type TCCFunc func(data map[string]interface{}) (map[string]interface{}, error)

// TCCParticipant TCC 参与者
type TCCParticipant struct {
	Name    string
	Try     TCCFunc // 资源预留
	Confirm TCCFunc // 确认提交
	Cancel  TCCFunc // 取消释放
	Status  ParticipantStatus
}

// TCCTransaction TCC 事务
//
// TCC（Try-Confirm-Cancel）模式：
//   - Try:     预留资源（如冻结金额、预留库存）
//   - Confirm: 确认提交（如扣减冻结金额）
//   - Cancel:  取消释放（如解冻金额）
//
// 与 2PC 的区别：
//   - 2PC 是数据库层面的阻塞协议
//   - TCC 是业务层面的柔性事务
//   - TCC 不会长时间锁定资源
type TCCTransaction struct {
	ID           string
	participants []*TCCParticipant
	Status       TCCStatus
	Data         map[string]interface{}
	logger       *utils.Logger
	mu           sync.RWMutex
}

// NewTCCTransaction 创建 TCC 事务
func NewTCCTransaction(id string) *TCCTransaction {
	return &TCCTransaction{
		ID:           id,
		participants: make([]*TCCParticipant, 0),
		Status:       TCCPending,
		Data:         make(map[string]interface{}),
		logger:       utils.NewLogger(fmt.Sprintf("TCC-%s", id)),
	}
}

// RegisterParticipant 注册参与者
func (t *TCCTransaction) RegisterParticipant(p *TCCParticipant) {
	t.mu.Lock()
	defer t.mu.Unlock()
	t.participants = append(t.participants, p)
}

// Execute 执行 TCC 事务
//
// 流程：
//  1. Try 阶段：所有参与者预留资源
//  2. 如果全部成功 -> Confirm 阶段
//  3. 如果任一失败 -> Cancel 阶段
func (t *TCCTransaction) Execute() error {
	t.mu.Lock()
	t.Status = TCCTrying
	t.mu.Unlock()

	t.logger.Info("========== TCC Transaction %s Started ==========", t.ID)

	// Phase 1: Try
	t.logger.Info("Phase 1: Try")
	triedParticipants := make([]*TCCParticipant, 0)

	for i, p := range t.participants {
		t.logger.Info("Try %d/%d: %s", i+1, len(t.participants), p.Name)

		result, err := p.Try(t.Data)
		if err != nil {
			t.logger.Error("Try for %s failed: %v", p.Name, err)
			p.Status = ParticipantFailed

			// Try 失败，取消所有已 Try 的参与者
			t.cancelAll(triedParticipants)

			t.mu.Lock()
			t.Status = TCCCancelled
			t.mu.Unlock()

			return fmt.Errorf("tcc %s: try for %s failed: %w", t.ID, p.Name, err)
		}

		// 合并结果
		if result != nil {
			for k, v := range result {
				t.Data[k] = v
			}
		}

		p.Status = ParticipantTried
		triedParticipants = append(triedParticipants, p)
		t.logger.Info("Try for %s succeeded", p.Name)
	}

	// Phase 2: Confirm
	t.logger.Info("Phase 2: Confirm")
	t.mu.Lock()
	t.Status = TCCTrying
	t.mu.Unlock()

	for i, p := range t.participants {
		t.logger.Info("Confirm %d/%d: %s", i+1, len(t.participants), p.Name)

		result, err := p.Confirm(t.Data)
		if err != nil {
			t.logger.Error("Confirm for %s failed: %v", p.Name, err)
			p.Status = ParticipantFailed

			// Confirm 失败需要重试或人工介入
			// 这里简化处理，标记为失败
			t.mu.Lock()
			t.Status = TCCFailed
			t.mu.Unlock()

			return fmt.Errorf("tcc %s: confirm for %s failed: %w", t.ID, p.Name, err)
		}

		if result != nil {
			for k, v := range result {
				t.Data[k] = v
			}
		}

		p.Status = ParticipantConfirmed
		t.logger.Info("Confirm for %s succeeded", p.Name)
	}

	t.mu.Lock()
	t.Status = TCCConfirmed
	t.mu.Unlock()

	t.logger.Info("========== TCC Transaction %s Confirmed ==========", t.ID)
	return nil
}

// cancelAll 取消所有已 Try 的参与者
func (t *TCCTransaction) cancelAll(participants []*TCCParticipant) {
	t.logger.Info("Cancelling %d tried participants", len(participants))

	// 逆序取消
	for i := len(participants) - 1; i >= 0; i-- {
		p := participants[i]
		t.logger.Info("Cancelling participant: %s", p.Name)

		_, err := p.Cancel(t.Data)
		if err != nil {
			t.logger.Error("Cancel for %s failed: %v", p.Name, err)
			p.Status = ParticipantFailed
			continue
		}

		p.Status = ParticipantCancelled
		t.logger.Info("Participant %s cancelled", p.Name)
	}
}

// GetStatus 获取 TCC 事务状态
func (t *TCCTransaction) GetStatus() TCCStatus {
	t.mu.RLock()
	defer t.mu.RUnlock()
	return t.Status
}
