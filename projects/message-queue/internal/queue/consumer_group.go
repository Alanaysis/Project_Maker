package queue

import (
	"sync"
	"sync/atomic"

	"github.com/example/message-queue/internal/protocol"
)

// ConsumerGroup represents a group of consumers that compete for messages
// in a point-to-point (queue) pattern. Only one consumer in the group
// receives each message.
type ConsumerGroup struct {
	Name      string
	Topic     string
	consumers map[string]*GroupConsumer
	mu        sync.RWMutex
	roundRobin uint64 // atomic counter for round-robin distribution
}

// GroupConsumer represents a consumer within a consumer group.
type GroupConsumer struct {
	ID     string
	Ch     chan *protocol.Message
	active bool
	mu     sync.Mutex
}

// NewConsumerGroup creates a new consumer group for the given topic.
func NewConsumerGroup(name, topic string) *ConsumerGroup {
	return &ConsumerGroup{
		Name:      name,
		Topic:     topic,
		consumers: make(map[string]*GroupConsumer),
	}
}

// AddConsumer adds a consumer to the group.
func (cg *ConsumerGroup) AddConsumer(consumerID string) (*GroupConsumer, error) {
	cg.mu.Lock()
	defer cg.mu.Unlock()

	if _, exists := cg.consumers[consumerID]; exists {
		return nil, protocol.ErrSubscriptionExists
	}

	gc := &GroupConsumer{
		ID:     consumerID,
		Ch:     make(chan *protocol.Message, 256),
		active: true,
	}
	cg.consumers[consumerID] = gc
	return gc, nil
}

// RemoveConsumer removes a consumer from the group.
func (cg *ConsumerGroup) RemoveConsumer(consumerID string) {
	cg.mu.Lock()
	defer cg.mu.Unlock()

	if gc, exists := cg.consumers[consumerID]; exists {
		gc.mu.Lock()
		gc.active = false
		close(gc.Ch)
		gc.mu.Unlock()
		delete(cg.consumers, consumerID)
	}
}

// Deliver delivers a message to the next available consumer in the group
// using round-robin distribution.
func (cg *ConsumerGroup) Deliver(msg *protocol.Message) error {
	cg.mu.RLock()
	defer cg.mu.RUnlock()

	if len(cg.consumers) == 0 {
		return protocol.ErrNoAvailableConsumer
	}

	// Get list of active consumers.
	var active []*GroupConsumer
	for _, gc := range cg.consumers {
		gc.mu.Lock()
		if gc.active {
			active = append(active, gc)
		}
		gc.mu.Unlock()
	}

	if len(active) == 0 {
		return protocol.ErrNoAvailableConsumer
	}

	// Round-robin selection.
	idx := atomic.AddUint64(&cg.roundRobin, 1) - 1
	selected := active[idx%uint64(len(active))]

	// Set the consumer group on the message.
	msg.ConsumerGroup = cg.Name

	// Try non-blocking send.
	select {
	case selected.Ch <- msg:
		return nil
	default:
		// If buffer is full, try other consumers.
		for _, gc := range active {
			if gc.ID == selected.ID {
				continue
			}
			select {
			case gc.Ch <- msg:
				return nil
			default:
				continue
			}
		}
		return protocol.ErrQueueFull
	}
}

// ConsumerCount returns the number of consumers in the group.
func (cg *ConsumerGroup) ConsumerCount() int {
	cg.mu.RLock()
	defer cg.mu.RUnlock()
	return len(cg.consumers)
}

// ActiveConsumerCount returns the number of active consumers in the group.
func (cg *ConsumerGroup) ActiveConsumerCount() int {
	cg.mu.RLock()
	defer cg.mu.RUnlock()

	count := 0
	for _, gc := range cg.consumers {
		gc.mu.Lock()
		if gc.active {
			count++
		}
		gc.mu.Unlock()
	}
	return count
}

// GetConsumer returns a consumer by ID.
func (cg *ConsumerGroup) GetConsumer(consumerID string) (*GroupConsumer, bool) {
	cg.mu.RLock()
	defer cg.mu.RUnlock()
	gc, ok := cg.consumers[consumerID]
	return gc, ok
}

// Close shuts down the consumer group.
func (cg *ConsumerGroup) Close() {
	cg.mu.Lock()
	defer cg.mu.Unlock()

	for _, gc := range cg.consumers {
		gc.mu.Lock()
		gc.active = false
		close(gc.Ch)
		gc.mu.Unlock()
	}
	cg.consumers = make(map[string]*GroupConsumer)
}
