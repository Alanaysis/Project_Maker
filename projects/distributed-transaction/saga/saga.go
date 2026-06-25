package saga

import (
	"fmt"
	"sync"

	"distributed-transaction/pkg/utils"
)

// StepStatus 步骤状态
type StepStatus int

const (
	StepPending   StepStatus = iota // 待执行
	StepCompleted                   // 已完成
	StepFailed                      // 执行失败
	StepCompensated                 // 已补偿
	StepCompensating                // 补偿中
)

func (s StepStatus) String() string {
	switch s {
	case StepPending:
		return "PENDING"
	case StepCompleted:
		return "COMPLETED"
	case StepFailed:
		return "FAILED"
	case StepCompensated:
		return "COMPENSATED"
	case StepCompensating:
		return "COMPENSATING"
	default:
		return "UNKNOWN"
	}
}

// SagaStatus Saga 状态
type SagaStatus int

const (
	SagaPending    SagaStatus = iota // 待执行
	SagaRunning                      // 执行中
	SagaCompleted                    // 已完成
	SagaCompensating                 // 补偿中
	SagaCompensated                  // 已补偿
	SagaFailed                       // 失败
)

func (s SagaStatus) String() string {
	switch s {
	case SagaPending:
		return "PENDING"
	case SagaRunning:
		return "RUNNING"
	case SagaCompleted:
		return "COMPLETED"
	case SagaCompensating:
		return "COMPENSATING"
	case SagaCompensated:
		return "COMPENSATED"
	case SagaFailed:
		return "FAILED"
	default:
		return "UNKNOWN"
	}
}

// StepFunc 步骤执行函数
type StepFunc func(data map[string]interface{}) (map[string]interface{}, error)

// Step Saga 步骤
type Step struct {
	Name       string
	Action     StepFunc // 正向操作
	Compensate StepFunc // 补偿操作
	Status     StepStatus
}

// Saga 编排式 Saga
//
// Saga 模式将长事务拆分为一系列本地事务，每个本地事务有对应的补偿事务。
// 如果某个步骤失败，按逆序执行已完成步骤的补偿事务。
//
// 流程：Step1 -> Step2 -> Step3 (失败) -> Compensate(Step2) -> Compensate(Step1)
type Saga struct {
	ID        string
	Steps     []*Step
	Status    SagaStatus
	Data      map[string]interface{}
	logger    *utils.Logger
	mu        sync.RWMutex
}

// NewSaga 创建新的 Saga
func NewSaga(id string) *Saga {
	return &Saga{
		ID:     id,
		Steps:  make([]*Step, 0),
		Status: SagaPending,
		Data:   make(map[string]interface{}),
		logger: utils.NewLogger(fmt.Sprintf("Saga-%s", id)),
	}
}

// AddStep 添加步骤
func (s *Saga) AddStep(name string, action, compensate StepFunc) *Saga {
	s.mu.Lock()
	defer s.mu.Unlock()

	s.Steps = append(s.Steps, &Step{
		Name:       name,
		Action:     action,
		Compensate: compensate,
		Status:     StepPending,
	})
	return s
}

// Execute 执行 Saga
//
// 正向执行所有步骤。如果某一步失败，逆序执行补偿。
func (s *Saga) Execute() error {
	s.mu.Lock()
	s.Status = SagaRunning
	s.mu.Unlock()

	s.logger.Info("========== Saga %s Started ==========", s.ID)
	completedSteps := make([]*Step, 0)

	for i, step := range s.Steps {
		s.logger.Info("Executing step %d/%d: %s", i+1, len(s.Steps), step.Name)

		result, err := step.Action(s.Data)
		if err != nil {
			s.logger.Error("Step %s failed: %v", step.Name, err)
			step.Status = StepFailed

			// 合并结果数据
			if result != nil {
				for k, v := range result {
					s.Data[k] = v
				}
			}

			// 执行补偿
			s.compensate(completedSteps)

			s.mu.Lock()
			s.Status = SagaFailed
			s.mu.Unlock()

			return fmt.Errorf("saga %s: step %s failed: %w", s.ID, step.Name, err)
		}

		// 合并结果数据
		if result != nil {
			for k, v := range result {
				s.Data[k] = v
			}
		}

		step.Status = StepCompleted
		completedSteps = append(completedSteps, step)
		s.logger.Info("Step %s completed", step.Name)
	}

	s.mu.Lock()
	s.Status = SagaCompleted
	s.mu.Unlock()

	s.logger.Info("========== Saga %s Completed ==========", s.ID)
	return nil
}

// compensate 逆序执行补偿操作
func (s *Saga) compensate(completedSteps []*Step) {
	s.mu.Lock()
	s.Status = SagaCompensating
	s.mu.Unlock()

	s.logger.Info("Starting compensation for %d completed steps", len(completedSteps))

	// 逆序补偿
	for i := len(completedSteps) - 1; i >= 0; i-- {
		step := completedSteps[i]
		s.logger.Info("Compensating step: %s", step.Name)

		step.Status = StepCompensating
		if step.Compensate == nil {
			s.logger.Warn("No compensate function for step %s, skipping", step.Name)
			step.Status = StepCompensated
			continue
		}

		_, err := step.Compensate(s.Data)
		if err != nil {
			s.logger.Error("Compensation for step %s failed: %v", step.Name, err)
			step.Status = StepFailed
			// 补偿失败需要人工介入
			continue
		}

		step.Status = StepCompensated
		s.logger.Info("Step %s compensated", step.Name)
	}

	s.mu.Lock()
	s.Status = SagaCompensated
	s.mu.Unlock()
}

// GetStatus 获取 Saga 状态
func (s *Saga) GetStatus() SagaStatus {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return s.Status
}
