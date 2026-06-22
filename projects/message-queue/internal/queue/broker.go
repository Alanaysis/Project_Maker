package queue

import (
	"fmt"
	"sync"

	"github.com/example/message-queue/internal/persistence"
	"github.com/example/message-queue/internal/protocol"
)

// Broker is the central message router that manages topics and message delivery.
type Broker struct {
	topics      map[string]*Topic
	subscribers map[string]*Subscriber
	store       persistence.Store
	mu          sync.RWMutex
	topicCap    int
	subBufSize  int
}

// BrokerConfig holds configuration for broker creation.
type BrokerConfig struct {
	TopicCapacity     int // max messages per topic (0 = unlimited)
	SubscriberBufSize int // channel buffer size per subscriber
}

// DefaultConfig returns a sensible default configuration.
func DefaultConfig() BrokerConfig {
	return BrokerConfig{
		TopicCapacity:     10000,
		SubscriberBufSize: 256,
	}
}

// NewBroker creates a new broker with the given config and persistence store.
func NewBroker(cfg BrokerConfig, store persistence.Store) *Broker {
	return &Broker{
		topics:      make(map[string]*Topic),
		subscribers: make(map[string]*Subscriber),
		store:       store,
		topicCap:    cfg.TopicCapacity,
		subBufSize:  cfg.SubscriberBufSize,
	}
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

// Publish sends a message to the named topic. The topic is auto-created if missing.
func (b *Broker) Publish(topicName string, payload []byte) (*protocol.Message, error) {
	b.mu.RLock()
	topic, exists := b.topics[topicName]
	b.mu.RUnlock()

	if !exists {
		// Auto-create topic.
		b.mu.Lock()
		// Double-check after acquiring write lock.
		if topic, exists = b.topics[topicName]; !exists {
			topic = NewTopic(topicName, b.topicCap)
			b.topics[topicName] = topic
		}
		b.mu.Unlock()
	}

	msg := protocol.NewMessage(topicName, payload)

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

// Subscribe registers a consumer to receive messages from a topic.
func (b *Broker) Subscribe(topicName string, consumerID string) (*Subscriber, error) {
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

	topic.mu.RLock()
	defer topic.mu.RUnlock()

	for _, msg := range topic.messages {
		if msg.ID == messageID {
			if msg.Status == protocol.StatusAcknowledged {
				return protocol.ErrAlreadyAcknowledged
			}
			msg.MarkAcknowledged()

			// Persist acknowledgement.
			if b.store != nil {
				if err := b.store.UpdateMessage(msg); err != nil {
					return fmt.Errorf("persist ack: %w", err)
				}
			}
			return nil
		}
	}
	return protocol.ErrMessageNotFound
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

		// Only replay unacknowledged messages.
		if msg.Status != protocol.StatusAcknowledged {
			topic.mu.Lock()
			topic.messages = append(topic.messages, msg)
			topic.mu.Unlock()
		}
	}
	return nil
}

// Close shuts down the broker gracefully.
func (b *Broker) Close() {
	b.mu.Lock()
	defer b.mu.Unlock()

	for _, topic := range b.topics {
		topic.mu.Lock()
		for _, sub := range topic.subscribers {
			close(sub.Ch)
		}
		topic.subscribers = make(map[string]*Subscriber)
		topic.mu.Unlock()
	}
}
