// Package queue implements the core message queue with topic management.
package queue

import (
	"sync"

	"github.com/example/message-queue/internal/protocol"
)

// Topic represents a named channel that holds messages and subscribers.
type Topic struct {
	Name        string
	messages    []*protocol.Message
	mu          sync.RWMutex
	subscribers map[string]*Subscriber
	capacity    int
}

// Subscriber represents a consumer subscribed to a topic.
type Subscriber struct {
	ID       string
	Ch       chan *protocol.Message
	Topics   []string
	mu       sync.Mutex
}

// NewTopic creates a topic with the given name and buffer capacity.
func NewTopic(name string, capacity int) *Topic {
	return &Topic{
		Name:        name,
		messages:    make([]*protocol.Message, 0),
		subscribers: make(map[string]*Subscriber),
		capacity:    capacity,
	}
}

// Publish adds a message to the topic and fans it out to all subscribers.
func (t *Topic) Publish(msg *protocol.Message) error {
	t.mu.Lock()
	defer t.mu.Unlock()

	if t.capacity > 0 && len(t.messages) >= t.capacity {
		return protocol.ErrQueueFull
	}

	t.messages = append(t.messages, msg)

	// Fan-out: deliver to every subscriber's channel.
	for _, sub := range t.subscribers {
		select {
		case sub.Ch <- msg:
		default:
			// Skip if subscriber buffer is full (non-blocking).
		}
	}
	return nil
}

// AddSubscriber registers a subscriber to receive messages from this topic.
func (t *Topic) AddSubscriber(sub *Subscriber) error {
	t.mu.Lock()
	defer t.mu.Unlock()

	if _, exists := t.subscribers[sub.ID]; exists {
		return protocol.ErrSubscriptionExists
	}

	t.subscribers[sub.ID] = sub
	return nil
}

// RemoveSubscriber unregisters a subscriber.
func (t *Topic) RemoveSubscriber(subID string) {
	t.mu.Lock()
	defer t.mu.Unlock()

	if sub, ok := t.subscribers[subID]; ok {
		close(sub.Ch)
		delete(t.subscribers, subID)
	}
}

// Messages returns a copy of all messages in the topic.
func (t *Topic) Messages() []*protocol.Message {
	t.mu.RLock()
	defer t.mu.RUnlock()

	result := make([]*protocol.Message, len(t.messages))
	copy(result, t.messages)
	return result
}

// SubscriberCount returns the number of active subscribers.
func (t *Topic) SubscriberCount() int {
	t.mu.RLock()
	defer t.mu.RUnlock()
	return len(t.subscribers)
}

// PendingCount returns the number of unacknowledged messages.
func (t *Topic) PendingCount() int {
	t.mu.RLock()
	defer t.mu.RUnlock()

	count := 0
	for _, msg := range t.messages {
		if msg.Status == protocol.StatusPending || msg.Status == protocol.StatusDelivered {
			count++
		}
	}
	return count
}
