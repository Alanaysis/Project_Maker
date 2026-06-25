package queue

import (
	"fmt"
	"sync"
	"time"

	"github.com/example/message-queue/internal/persistence"
	"github.com/example/message-queue/internal/protocol"
)

// Broker is the central message router that manages topics and message delivery.
type Broker struct {
	topics           map[string]*Topic
	subscribers      map[string]*Subscriber
	consumerGroups   map[string]*ConsumerGroup
	deadLetterQueues map[string]*DeadLetterQueue
	store            persistence.Store
	mu               sync.RWMutex
	topicCap         int
	subBufSize       int
	retryWorkerStop  chan struct{}
	closed           bool
	closeMu          sync.Mutex
}

// BrokerConfig holds configuration for broker creation.
type BrokerConfig struct {
	TopicCapacity      int           // max messages per topic (0 = unlimited)
	SubscriberBufSize  int           // channel buffer size per subscriber
	DeadLetterCapacity int           // max messages per dead letter queue (0 = unlimited)
	RetryCheckInterval time.Duration // interval to check for retryable messages
}

// DefaultConfig returns a sensible default configuration.
func DefaultConfig() BrokerConfig {
	return BrokerConfig{
		TopicCapacity:      10000,
		SubscriberBufSize:  256,
		DeadLetterCapacity: 1000,
		RetryCheckInterval: 5 * time.Second,
	}
}

// NewBroker creates a new broker with the given config and persistence store.
func NewBroker(cfg BrokerConfig, store persistence.Store) *Broker {
	b := &Broker{
		topics:           make(map[string]*Topic),
		subscribers:      make(map[string]*Subscriber),
		consumerGroups:   make(map[string]*ConsumerGroup),
		deadLetterQueues: make(map[string]*DeadLetterQueue),
		store:            store,
		topicCap:         cfg.TopicCapacity,
		subBufSize:       cfg.SubscriberBufSize,
		retryWorkerStop:  make(chan struct{}),
	}

	// Start retry worker if interval is set.
	if cfg.RetryCheckInterval > 0 {
		go b.retryWorker(cfg.RetryCheckInterval)
	}

	return b
}

// CreateTopic declares a new topic. Returns error if it already exists.
func (b *Broker) CreateTopic(name string) error {
	b.mu.Lock()
	defer b.mu.Unlock()

	if _, exists := b.topics[name]; exists {
		return protocol.ErrTopicAlreadyExists
	}

	b.topics[name] = NewTopic(name, b.topicCap)
	return nil
}

// CreateQueueTopic declares a new point-to-point topic.
func (b *Broker) CreateQueueTopic(name string) error {
	b.mu.Lock()
	defer b.mu.Unlock()

	if _, exists := b.topics[name]; exists {
		return protocol.ErrTopicAlreadyExists
	}

	b.topics[name] = NewQueueTopic(name, b.topicCap)
	return nil
}

// getTopic returns a topic by name (internal, no locking).
func (b *Broker) getTopic(name string) (*Topic, bool) {
	topic, exists := b.topics[name]
	return topic, exists
}

// Publish sends a message to the named topic. The topic is auto-created if missing.
func (b *Broker) Publish(topicName string, payload []byte) (*protocol.Message, error) {
	return b.PublishWithOptions(topicName, payload, protocol.PriorityNormal, nil, nil)
}

// PublishWithOptions sends a message with full options.
func (b *Broker) PublishWithOptions(topicName string, payload []byte, priority protocol.Priority, headers map[string]string, delay *time.Duration) (*protocol.Message, error) {
	b.mu.RLock()
	topic, exists := b.topics[topicName]
	b.mu.RUnlock()

	if !exists {
		// Auto-create topic (pub/sub mode by default).
		b.mu.Lock()
		if topic, exists = b.topics[topicName]; !exists {
			topic = NewTopic(topicName, b.topicCap)
			b.topics[topicName] = topic
		}
		b.mu.Unlock()
	}

	msg := protocol.NewMessage(topicName, payload)
	msg.Priority = priority
	if headers != nil {
		msg.Headers = headers
	}
	if delay != nil {
		msg.WithDelay(*delay)
	}

	// Persist before publishing (at-least-once delivery).
	if b.store != nil {
		if err := b.store.SaveMessage(msg); err != nil {
			return nil, fmt.Errorf("persist message: %w", err)
		}
	}

	if err := topic.Publish(msg); err != nil {
		return nil, err
	}

	return msg, nil
}

// PublishDelayed sends a message that will be delivered after the specified delay.
func (b *Broker) PublishDelayed(topicName string, payload []byte, delay time.Duration) (*protocol.Message, error) {
	return b.PublishWithOptions(topicName, payload, protocol.PriorityNormal, nil, &delay)
}

// PublishWithPriority sends a message with a specific priority.
func (b *Broker) PublishWithPriority(topicName string, payload []byte, priority protocol.Priority) (*protocol.Message, error) {
	return b.PublishWithOptions(topicName, payload, priority, nil, nil)
}

// PublishWithHeaders sends a message with custom headers for filtering.
func (b *Broker) PublishWithHeaders(topicName string, payload []byte, headers map[string]string) (*protocol.Message, error) {
	return b.PublishWithOptions(topicName, payload, protocol.PriorityNormal, headers, nil)
}

// Subscribe registers a consumer to receive messages from a topic.
func (b *Broker) Subscribe(topicName string, consumerID string) (*Subscriber, error) {
	return b.SubscribeWithFilter(topicName, consumerID, nil)
}

// SubscribeWithFilter registers a consumer with an optional message filter.
func (b *Broker) SubscribeWithFilter(topicName string, consumerID string, filter map[string]string) (*Subscriber, error) {
	b.mu.RLock()
	topic, exists := b.topics[topicName]
	b.mu.RUnlock()

	if !exists {
		return nil, protocol.ErrTopicNotFound
	}

	sub := &Subscriber{
		ID:     consumerID,
		Ch:     make(chan *protocol.Message, b.subBufSize),
		Topics: []string{topicName},
		filter: filter,
	}

	if err := topic.AddSubscriber(sub); err != nil {
		return nil, err
	}

	b.mu.Lock()
	b.subscribers[consumerID] = sub
	b.mu.Unlock()

	return sub, nil
}

// Unsubscribe removes a consumer from a topic.
func (b *Broker) Unsubscribe(topicName string, consumerID string) {
	b.mu.RLock()
	topic, exists := b.topics[topicName]
	b.mu.RUnlock()

	if !exists {
		return
	}

	topic.RemoveSubscriber(consumerID)

	b.mu.Lock()
	delete(b.subscribers, consumerID)
	b.mu.Unlock()
}

// Acknowledge marks a message as processed by a consumer.
func (b *Broker) Acknowledge(topicName string, messageID string) error {
	b.mu.RLock()
	topic, exists := b.topics[topicName]
	b.mu.RUnlock()

	if !exists {
		return protocol.ErrTopicNotFound
	}

	// Use topic's own method to acknowledge and remove.
	if err := topic.AcknowledgeMessage(messageID); err != nil {
		return err
	}

	// Persist acknowledgement if store is available.
	if b.store != nil {
		// We need to get the message from the store to update it.
		// Since we already removed it from the topic, we'll just update the store.
		msg, err := b.store.LoadMessage(messageID)
		if err == nil {
			msg.MarkAcknowledged()
			b.store.UpdateMessage(msg)
		}
	}

	return nil
}

// NegativeAcknowledge marks a message for retry. If max retries exceeded,
// moves it to the dead letter queue.
func (b *Broker) NegativeAcknowledge(topicName string, messageID string) error {
	b.mu.RLock()
	topic, exists := b.topics[topicName]
	b.mu.RUnlock()

	if !exists {
		return protocol.ErrTopicNotFound
	}

	// Find the message and handle retry/DLQ.
	msg := topic.GetMessage(messageID)
	if msg == nil {
		return protocol.ErrMessageNotFound
	}

	if msg.CanRetry() {
		msg.IncrementRetry()
		// Persist update.
		if b.store != nil {
			if err := b.store.UpdateMessage(msg); err != nil {
				return fmt.Errorf("persist retry: %w", err)
			}
		}
		return nil
	}

	// Max retries exceeded - move to dead letter queue.
	topic.RemoveMessage(messageID)
	dlq := b.getOrCreateDLQ(topicName)
	dlq.Add(msg)

	// Persist update.
	if b.store != nil {
		if err := b.store.UpdateMessage(msg); err != nil {
			return fmt.Errorf("persist dead letter: %w", err)
		}
	}

	return nil
}

// getOrCreateDLQ returns the dead letter queue for a topic, creating it if needed.
func (b *Broker) getOrCreateDLQ(topicName string) *DeadLetterQueue {
	b.mu.Lock()
	defer b.mu.Unlock()

	dlqName := topicName + "_dlq"
	if dlq, exists := b.deadLetterQueues[dlqName]; exists {
		return dlq
	}

	dlq := NewDeadLetterQueue(dlqName, b.topicCap)
	b.deadLetterQueues[dlqName] = dlq
	return dlq
}

// CreateConsumerGroup creates a new consumer group for a topic.
func (b *Broker) CreateConsumerGroup(groupName, topicName string) (*ConsumerGroup, error) {
	b.mu.Lock()
	defer b.mu.Unlock()

	if _, exists := b.consumerGroups[groupName]; exists {
		return nil, protocol.ErrConsumerGroupExists
	}

	topic, exists := b.topics[topicName]
	if !exists {
		return nil, protocol.ErrTopicNotFound
	}

	// Ensure topic is in queue mode for consumer groups.
	topic.Mode = ModeQueue

	cg := NewConsumerGroup(groupName, topicName)
	b.consumerGroups[groupName] = cg
	return cg, nil
}

// JoinConsumerGroup adds a consumer to an existing group.
func (b *Broker) JoinConsumerGroup(groupName, consumerID string) (*GroupConsumer, error) {
	b.mu.RLock()
	cg, exists := b.consumerGroups[groupName]
	b.mu.RUnlock()

	if !exists {
		return nil, protocol.ErrConsumerGroupNotFound
	}

	return cg.AddConsumer(consumerID)
}

// LeaveConsumerGroup removes a consumer from a group.
func (b *Broker) LeaveConsumerGroup(groupName, consumerID string) {
	b.mu.RLock()
	cg, exists := b.consumerGroups[groupName]
	b.mu.RUnlock()

	if !exists {
		return
	}

	cg.RemoveConsumer(consumerID)
}

// DeliverToGroup delivers a message to a consumer group.
func (b *Broker) DeliverToGroup(groupName string, msg *protocol.Message) error {
	b.mu.RLock()
	cg, exists := b.consumerGroups[groupName]
	b.mu.RUnlock()

	if !exists {
		return protocol.ErrConsumerGroupNotFound
	}

	return cg.Deliver(msg)
}

// Pull retrieves the next available message from a topic (pull mode).
func (b *Broker) Pull(topicName string, timeout time.Duration) (*protocol.Message, error) {
	b.mu.RLock()
	topic, exists := b.topics[topicName]
	b.mu.RUnlock()

	if !exists {
		return nil, protocol.ErrTopicNotFound
	}

	deadline := time.Now().Add(timeout)

	for time.Now().Before(deadline) {
		msg := topic.PopReadyMessage()
		if msg != nil {
			msg.MarkDelivered()

			// Persist delivery.
			if b.store != nil {
				if err := b.store.UpdateMessage(msg); err != nil {
					return nil, fmt.Errorf("persist delivery: %w", err)
				}
			}
			return msg, nil
		}

		// Wait a bit before trying again.
		time.Sleep(10 * time.Millisecond)
	}

	return nil, protocol.ErrMessageNotFound
}

// GetTopic returns a topic by name.
func (b *Broker) GetTopic(name string) (*Topic, error) {
	b.mu.RLock()
	defer b.mu.RUnlock()

	topic, exists := b.topics[name]
	if !exists {
		return nil, protocol.ErrTopicNotFound
	}
	return topic, nil
}

// Topics returns a list of all topic names.
func (b *Broker) Topics() []string {
	b.mu.RLock()
	defer b.mu.RUnlock()

	names := make([]string, 0, len(b.topics))
	for name := range b.topics {
		names = append(names, name)
	}
	return names
}

// GetConsumerGroup returns a consumer group by name.
func (b *Broker) GetConsumerGroup(name string) (*ConsumerGroup, error) {
	b.mu.RLock()
	defer b.mu.RUnlock()

	cg, exists := b.consumerGroups[name]
	if !exists {
		return nil, protocol.ErrConsumerGroupNotFound
	}
	return cg, nil
}

// GetDeadLetterQueue returns the dead letter queue for a topic.
func (b *Broker) GetDeadLetterQueue(topicName string) *DeadLetterQueue {
	return b.getOrCreateDLQ(topicName)
}

// Recover loads persisted messages back into topics on startup.
func (b *Broker) Recover() error {
	if b.store == nil {
		return nil
	}

	messages, err := b.store.LoadAll()
	if err != nil {
		return fmt.Errorf("recover messages: %w", err)
	}

	for _, msg := range messages {
		b.mu.Lock()
		topic, exists := b.topics[msg.Topic]
		if !exists {
			topic = NewTopic(msg.Topic, b.topicCap)
			b.topics[msg.Topic] = topic
		}
		b.mu.Unlock()

		// Route based on message status.
		switch msg.Status {
		case protocol.StatusDeadLetter:
			dlq := b.getOrCreateDLQ(msg.Topic)
			dlq.Add(msg)
		case protocol.StatusAcknowledged:
			// Skip acknowledged messages.
			continue
		default:
			// Replay unacknowledged messages.
			topic.AddMessage(msg)
		}
	}
	return nil
}

// retryWorker periodically checks for messages that need retry.
func (b *Broker) retryWorker(interval time.Duration) {
	ticker := time.NewTicker(interval)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			b.processRetries()
		case <-b.retryWorkerStop:
			return
		}
	}
}

// processRetries checks all topics for messages that exceeded retry limit.
func (b *Broker) processRetries() {
	b.closeMu.Lock()
	if b.closed {
		b.closeMu.Unlock()
		return
	}
	b.closeMu.Unlock()

	b.mu.RLock()
	topics := make([]*Topic, 0, len(b.topics))
	for _, topic := range b.topics {
		topics = append(topics, topic)
	}
	b.mu.RUnlock()

	for _, topic := range topics {
		topic.ProcessDeadLetters(b.getOrCreateDLQ(topic.Name))
	}
}

// Close shuts down the broker gracefully.
func (b *Broker) Close() {
	b.closeMu.Lock()
	if b.closed {
		b.closeMu.Unlock()
		return
	}
	b.closed = true
	b.closeMu.Unlock()

	close(b.retryWorkerStop)

	b.mu.Lock()
	defer b.mu.Unlock()

	for _, topic := range b.topics {
		topic.Close()
	}

	for _, cg := range b.consumerGroups {
		cg.Close()
	}
}
