package queue

import (
	"sync"

	"github.com/example/message-queue/internal/protocol"
)

// DeadLetterQueue holds messages that have exceeded their maximum retry count.
type DeadLetterQueue struct {
	name     string
	messages []*protocol.Message
	mu       sync.RWMutex
	capacity int
}

// NewDeadLetterQueue creates a new dead letter queue.
func NewDeadLetterQueue(name string, capacity int) *DeadLetterQueue {
	return &DeadLetterQueue{
		name:     name,
		messages: make([]*protocol.Message, 0),
		capacity: capacity,
	}
}

// Add adds a message to the dead letter queue.
func (dlq *DeadLetterQueue) Add(msg *protocol.Message) error {
	dlq.mu.Lock()
	defer dlq.mu.Unlock()

	if dlq.capacity > 0 && len(dlq.messages) >= dlq.capacity {
		return protocol.ErrQueueFull
	}

	msg.MarkDeadLetter()
	dlq.messages = append(dlq.messages, msg)
	return nil
}

// Messages returns all messages in the dead letter queue.
func (dlq *DeadLetterQueue) Messages() []*protocol.Message {
	dlq.mu.RLock()
	defer dlq.mu.RUnlock()

	result := make([]*protocol.Message, len(dlq.messages))
	copy(result, dlq.messages)
	return result
}

// Count returns the number of messages in the dead letter queue.
func (dlq *DeadLetterQueue) Count() int {
	dlq.mu.RLock()
	defer dlq.mu.RUnlock()
	return len(dlq.messages)
}

// Peek returns the next message without removing it.
func (dlq *DeadLetterQueue) Peek() *protocol.Message {
	dlq.mu.RLock()
	defer dlq.mu.RUnlock()

	if len(dlq.messages) == 0 {
		return nil
	}
	return dlq.messages[0]
}

// Pop removes and returns the next message from the dead letter queue.
func (dlq *DeadLetterQueue) Pop() *protocol.Message {
	dlq.mu.Lock()
	defer dlq.mu.Unlock()

	if len(dlq.messages) == 0 {
		return nil
	}

	msg := dlq.messages[0]
	dlq.messages = dlq.messages[1:]
	return msg
}

// RetryMessage moves a message back to pending status for retry.
func (dlq *DeadLetterQueue) RetryMessage(msgID string) *protocol.Message {
	dlq.mu.Lock()
	defer dlq.mu.Unlock()

	for i, msg := range dlq.messages {
		if msg.ID == msgID {
			// Remove from DLQ.
			dlq.messages = append(dlq.messages[:i], dlq.messages[i+1:]...)
			// Reset for retry.
			msg.IncrementRetry()
			return msg
		}
	}
	return nil
}

// Clear removes all messages from the dead letter queue.
func (dlq *DeadLetterQueue) Clear() {
	dlq.mu.Lock()
	defer dlq.mu.Unlock()
	dlq.messages = make([]*protocol.Message, 0)
}

// Name returns the name of the dead letter queue.
func (dlq *DeadLetterQueue) Name() string {
	return dlq.name
}
