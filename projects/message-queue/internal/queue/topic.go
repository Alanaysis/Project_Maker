// Package queue implements the core message queue with topic management.
package queue

import (
	"container/heap"
	"sort"
	"sync"
	"time"

	"github.com/example/message-queue/internal/protocol"
)

// TopicMode defines how messages are delivered to consumers.
type TopicMode int

const (
	// ModePubSub delivers each message to all subscribers (fan-out).
	ModePubSub TopicMode = iota
	// ModeQueue delivers each message to exactly one consumer (point-to-point).
	ModeQueue
)

// priorityQueue implements heap.Interface for priority-ordered messages.
type priorityQueue []*protocol.Message

func (pq priorityQueue) Len() int { return len(pq) }

func (pq priorityQueue) Less(i, j int) bool {
	// Higher priority value = higher priority (processed first).
	if pq[i].Priority != pq[j].Priority {
		return pq[i].Priority > pq[j].Priority
	}
	// Same priority: FIFO order by creation time.
	return pq[i].CreatedAt.Before(pq[j].CreatedAt)
}

func (pq priorityQueue) Swap(i, j int) {
	pq[i], pq[j] = pq[j], pq[i]
}

func (pq *priorityQueue) Push(x interface{}) {
	*pq = append(*pq, x.(*protocol.Message))
}

func (pq *priorityQueue) Pop() interface{} {
	old := *pq
	n := len(old)
	item := old[n-1]
	old[n-1] = nil // avoid memory leak
	*pq = old[:n-1]
	return item
}

// Topic represents a named channel that holds messages and subscribers.
type Topic struct {
	Name        string
	Mode        TopicMode
	messages    *priorityQueue
	mu          sync.RWMutex
	subscribers map[string]*Subscriber
	capacity    int
	filter      map[string]string // message filter for subscribers
}

// Subscriber represents a consumer subscribed to a topic.
type Subscriber struct {
	ID       string
	Ch       chan *protocol.Message
	Topics   []string
	mu       sync.Mutex
	filter   map[string]string // optional message filter
}

// NewTopic creates a topic with the given name and buffer capacity.
func NewTopic(name string, capacity int) *Topic {
	pq := &priorityQueue{}
	heap.Init(pq)
	return &Topic{
		Name:        name,
		Mode:        ModePubSub,
		messages:    pq,
		subscribers: make(map[string]*Subscriber),
		capacity:    capacity,
	}
}

// NewQueueTopic creates a point-to-point topic.
func NewQueueTopic(name string, capacity int) *Topic {
	t := NewTopic(name, capacity)
	t.Mode = ModeQueue
	return t
}

// SetFilter sets a message filter for this topic. Only messages matching
// the filter will be delivered to subscribers.
func (t *Topic) SetFilter(filter map[string]string) {
	t.mu.Lock()
	defer t.mu.Unlock()
	t.filter = filter
}

// Publish adds a message to the topic and delivers it based on the topic mode.
func (t *Topic) Publish(msg *protocol.Message) error {
	t.mu.Lock()
	defer t.mu.Unlock()

	if t.capacity > 0 && t.messages.Len() >= t.capacity {
		return protocol.ErrQueueFull
	}

	// Check topic-level filter.
	if !msg.MatchesFilter(t.filter) {
		return nil // silently drop messages that don't match filter
	}

	heap.Push(t.messages, msg)

	// Deliver based on mode.
	switch t.Mode {
	case ModePubSub:
		t.fanOut(msg)
	case ModeQueue:
		t.deliverToNext(msg)
	}
	return nil
}

// fanOut delivers a message to all subscribers (pub/sub mode).
func (t *Topic) fanOut(msg *protocol.Message) {
	for _, sub := range t.subscribers {
		// Check subscriber-level filter.
		if !msg.MatchesFilter(sub.filter) {
			continue
		}
		select {
		case sub.Ch <- msg:
		default:
			// Skip if subscriber buffer is full (non-blocking).
		}
	}
}

// deliverToNext delivers a message to the next available subscriber (queue mode).
func (t *Topic) deliverToNext(msg *protocol.Message) {
	// Round-robin: try each subscriber in order.
	// In a real system, this would use a more sophisticated algorithm.
	for _, sub := range t.subscribers {
		if !msg.MatchesFilter(sub.filter) {
			continue
		}
		select {
		case sub.Ch <- msg:
			return // delivered to one consumer
		default:
			continue // try next subscriber
		}
	}
	// No subscriber available - message stays in queue for later delivery.
}

// GetReadyMessages returns messages that are ready for delivery (delay expired).
func (t *Topic) GetReadyMessages() []*protocol.Message {
	t.mu.RLock()
	defer t.mu.RUnlock()

	var ready []*protocol.Message
	for _, msg := range *t.messages {
		if msg.IsReady() {
			ready = append(ready, msg)
		}
	}
	return ready
}

// PopReadyMessage removes and returns the highest priority ready message.
func (t *Topic) PopReadyMessage() *protocol.Message {
	t.mu.Lock()
	defer t.mu.Unlock()

	if t.messages.Len() == 0 {
		return nil
	}

	// Find the highest priority ready message.
	// Since we use a priority queue, we check from the top.
	for i := 0; i < t.messages.Len(); i++ {
		msg := (*t.messages)[i]
		if msg.IsReady() {
			// Remove from heap.
			heap.Remove(t.messages, i)
			return msg
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

// Messages returns a copy of all messages in the topic (ordered by priority).
func (t *Topic) Messages() []*protocol.Message {
	t.mu.RLock()
	defer t.mu.RUnlock()

	result := make([]*protocol.Message, t.messages.Len())
	copy(result, *t.messages)

	// Sort by priority then creation time for consistent output.
	sort.Slice(result, func(i, j int) bool {
		if result[i].Priority != result[j].Priority {
			return result[i].Priority > result[j].Priority
		}
		return result[i].CreatedAt.Before(result[j].CreatedAt)
	})
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
	for _, msg := range *t.messages {
		if msg.Status == protocol.StatusPending || msg.Status == protocol.StatusDelivered {
			count++
		}
	}
	return count
}

// RemoveMessage removes a specific message from the topic.
func (t *Topic) RemoveMessage(msgID string) bool {
	t.mu.Lock()
	defer t.mu.Unlock()

	for i, msg := range *t.messages {
		if msg.ID == msgID {
			heap.Remove(t.messages, i)
			return true
		}
	}
	return false
}

// GetDelayedMessages returns messages that are not yet ready for delivery.
func (t *Topic) GetDelayedMessages() []*protocol.Message {
	t.mu.RLock()
	defer t.mu.RUnlock()

	var delayed []*protocol.Message
	now := time.Now()
	for _, msg := range *t.messages {
		if msg.DeliverAfter != nil && msg.DeliverAfter.After(now) {
			delayed = append(delayed, msg)
		}
	}
	return delayed
}

// AcknowledgeMessage marks a message as acknowledged and removes it from the topic.
func (t *Topic) AcknowledgeMessage(msgID string) error {
	t.mu.Lock()
	defer t.mu.Unlock()

	for i, msg := range *t.messages {
		if msg.ID == msgID {
			if msg.Status == protocol.StatusAcknowledged {
				return protocol.ErrAlreadyAcknowledged
			}
			msg.MarkAcknowledged()
			heap.Remove(t.messages, i)
			return nil
		}
	}
	return protocol.ErrMessageNotFound
}

// GetMessage returns a message by ID without removing it.
func (t *Topic) GetMessage(msgID string) *protocol.Message {
	t.mu.RLock()
	defer t.mu.RUnlock()

	for _, msg := range *t.messages {
		if msg.ID == msgID {
			return msg
		}
	}
	return nil
}

// AddMessage adds a message directly to the topic (used for recovery).
func (t *Topic) AddMessage(msg *protocol.Message) {
	t.mu.Lock()
	defer t.mu.Unlock()
	heap.Push(t.messages, msg)
}

// Close closes all subscriber channels.
func (t *Topic) Close() {
	t.mu.Lock()
	defer t.mu.Unlock()

	for _, sub := range t.subscribers {
		close(sub.Ch)
	}
	t.subscribers = make(map[string]*Subscriber)
}

// ProcessDeadLetters checks for messages that exceeded retry limit and moves them to DLQ.
func (t *Topic) ProcessDeadLetters(dlq *DeadLetterQueue) {
	t.mu.Lock()
	defer t.mu.Unlock()

	var remaining []*protocol.Message
	for _, msg := range *t.messages {
		if msg.Status == protocol.StatusDelivered && !msg.CanRetry() {
			dlq.Add(msg)
		} else {
			remaining = append(remaining, msg)
		}
	}

	// Rebuild the priority queue with remaining messages.
	*t.messages = priorityQueue(remaining)
}
