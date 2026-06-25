package saga

import (
	"fmt"
	"sync"

	"distributed-transaction/pkg/utils"
)

// EventType 事件类型
type EventType string

const (
	EventStepCompleted EventType = "STEP_COMPLETED"
	EventStepFailed    EventType = "STEP_FAILED"
	EventSagaCompleted EventType = "SAGA_COMPLETED"
	EventSagaFailed    EventType = "SAGA_FAILED"
	EventCompensate    EventType = "COMPENSATE"
)

// Event Saga 事件
type Event struct {
	Type    EventType
	SagaID  string
	StepID  string
	Data    map[string]interface{}
	Error   error
}

// EventHandler 事件处理函数
type EventHandler func(event Event) error

// ChoreographyParticipant 协调式 Saga 参与者
type ChoreographyParticipant struct {
	Name       string
	Action     StepFunc
	Compensate StepFunc
}

// ChoreographySaga 协调式 Saga
//
// 与编排式 Saga 不同，协调式 Saga 没有中心协调者。
// 参与者通过事件进行通信，每个参与者监听事件并决定是否执行自己的操作。
//
// 流程：
//  1. 参与者 A 完成 -> 发布 STEP_COMPLETED 事件
//  2. 参与者 B 监听到事件 -> 执行自己的操作
//  3. 如果 B 失败 -> 发布 STEP_FAILED 事件
//  4. 参与者 A 监听到失败 -> 执行补偿
type ChoreographySaga struct {
	ID           string
	participants []*ChoreographyParticipant
	eventBus     *EventBus
	Status       SagaStatus
	Data         map[string]interface{}
	logger       *utils.Logger
	mu           sync.RWMutex
}

// EventBus 事件总线
type EventBus struct {
	handlers map[EventType][]EventHandler
	mu       sync.RWMutex
}

// NewEventBus 创建事件总线
func NewEventBus() *EventBus {
	return &EventBus{
		handlers: make(map[EventType][]EventHandler),
	}
}

// Subscribe 订阅事件
func (eb *EventBus) Subscribe(eventType EventType, handler EventHandler) {
	eb.mu.Lock()
	defer eb.mu.Unlock()
	eb.handlers[eventType] = append(eb.handlers[eventType], handler)
}

// Publish 发布事件
func (eb *EventBus) Publish(event Event) {
	eb.mu.RLock()
	handlers := eb.handlers[event.Type]
	eb.mu.RUnlock()

	for _, handler := range handlers {
		_ = handler(event)
	}
}

// NewChoreographySaga 创建协调式 Saga
func NewChoreographySaga(id string) *ChoreographySaga {
	return &ChoreographySaga{
		ID:           id,
		participants: make([]*ChoreographyParticipant, 0),
		eventBus:     NewEventBus(),
		Status:       SagaPending,
		Data:         make(map[string]interface{}),
		logger:       utils.NewLogger(fmt.Sprintf("Choreography-%s", id)),
	}
}

// RegisterParticipant 注册参与者
func (cs *ChoreographySaga) RegisterParticipant(p *ChoreographyParticipant) {
	cs.mu.Lock()
	defer cs.mu.Unlock()
	cs.participants = append(cs.participants, p)
}

// Execute 执行协调式 Saga
//
// 按顺序触发每个参与者，通过事件总线传递状态。
// 任一参与者失败则触发补偿链。
func (cs *ChoreographySaga) Execute() error {
	cs.mu.Lock()
	cs.Status = SagaRunning
	cs.mu.Unlock()

	cs.logger.Info("========== Choreography Saga %s Started ==========", cs.ID)

	// 用于跟踪已完成的参与者（用于补偿）
	completed := make([]*ChoreographyParticipant, 0)
	var failed bool

	for i, p := range cs.participants {
		cs.logger.Info("Participant %d/%d: %s executing", i+1, len(cs.participants), p.Name)

		result, err := p.Action(cs.Data)
		if err != nil {
			cs.logger.Error("Participant %s failed: %v", p.Name, err)
			cs.eventBus.Publish(Event{
				Type:   EventStepFailed,
				SagaID: cs.ID,
				StepID: p.Name,
				Error:  err,
			})
			failed = true
			break
		}

		// 合并结果
		if result != nil {
			for k, v := range result {
				cs.Data[k] = v
			}
		}

		completed = append(completed, p)
		cs.eventBus.Publish(Event{
			Type:   EventStepCompleted,
			SagaID: cs.ID,
			StepID: p.Name,
			Data:   cs.Data,
		})
		cs.logger.Info("Participant %s completed", p.Name)
	}

	if failed {
		// 逆序补偿
		cs.logger.Info("Starting compensation chain")
		cs.mu.Lock()
		cs.Status = SagaCompensating
		cs.mu.Unlock()

		for i := len(completed) - 1; i >= 0; i-- {
			p := completed[i]
			if p.Compensate != nil {
				cs.logger.Info("Compensating participant: %s", p.Name)
				_, err := p.Compensate(cs.Data)
				if err != nil {
					cs.logger.Error("Compensation for %s failed: %v", p.Name, err)
				}
				cs.eventBus.Publish(Event{
					Type:   EventCompensate,
					SagaID: cs.ID,
					StepID: p.Name,
				})
			}
		}

		cs.mu.Lock()
		cs.Status = SagaCompensated
		cs.mu.Unlock()

		cs.eventBus.Publish(Event{
			Type:   EventSagaFailed,
			SagaID: cs.ID,
		})

		cs.logger.Info("========== Choreography Saga %s Compensated ==========", cs.ID)
		return fmt.Errorf("choreography saga %s: failed, compensated", cs.ID)
	}

	cs.mu.Lock()
	cs.Status = SagaCompleted
	cs.mu.Unlock()

	cs.eventBus.Publish(Event{
		Type:   EventSagaCompleted,
		SagaID: cs.ID,
		Data:   cs.Data,
	})

	cs.logger.Info("========== Choreography Saga %s Completed ==========", cs.ID)
	return nil
}
