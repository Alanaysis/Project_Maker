// Package api provides a high-level facade for the message queue.
package api

import (
	"github.com/example/message-queue/internal/consumer"
	"github.com/example/message-queue/internal/persistence"
	"github.com/example/message-queue/internal/producer"
	"github.com/example/message-queue/internal/protocol"
	"github.com/example/message-queue/internal/queue"
)

// MessageQueue is the top-level API that ties all components together.
type MessageQueue struct {
	broker *queue.Broker
	store  persistence.Store
}

// Config holds creation parameters for the message queue.
type Config struct {
	// TopicCapacity is the max messages per topic (0 = unlimited).
	TopicCapacity int
	// SubscriberBufSize is the channel buffer per subscriber.
	SubscriberBufSize int
	// DataDir is the filesystem path for persistent storage. Empty = memory only.
	DataDir string
}

// DefaultConfig returns sensible defaults.
func DefaultConfig() Config {
	return Config{
		TopicCapacity:     10000,
		SubscriberBufSize: 256,
	}
}

// New creates and initializes a message queue.
func New(cfg Config) (*MessageQueue, error) {
	var store persistence.Store

	if cfg.DataDir != "" {
		fs, err := persistence.NewFileStore(cfg.DataDir)
		if err != nil {
			return nil, err
		}
		store = fs
	} else {
		store = persistence.NewMemStore()
	}

	brokerCfg := queue.BrokerConfig{
		TopicCapacity:     cfg.TopicCapacity,
		SubscriberBufSize: cfg.SubscriberBufSize,
	}

	broker := queue.NewBroker(brokerCfg, store)

	// Recover persisted messages.
	if err := broker.Recover(); err != nil {
		return nil, err
	}

	return &MessageQueue{
		broker: broker,
		store:  store,
	}, nil
}

// NewProducer creates a producer bound to this queue.
func (mq *MessageQueue) NewProducer() *producer.Producer {
	return producer.New(mq.broker)
}

// NewConsumer creates a consumer with the given ID and message handler.
func (mq *MessageQueue) NewConsumer(id string, handler consumer.Handler) *consumer.Consumer {
	return consumer.New(id, mq.broker, handler)
}

// CreateTopic explicitly creates a topic.
func (mq *MessageQueue) CreateTopic(name string) error {
	return mq.broker.CreateTopic(name)
}

// GetTopic returns a topic by name for inspection.
func (mq *MessageQueue) GetTopic(name string) (*queue.Topic, error) {
	return mq.broker.GetTopic(name)
}

// Topics returns all topic names.
func (mq *MessageQueue) Topics() []string {
	return mq.broker.Topics()
}

// TopicInfo returns basic stats for a topic.
func (mq *MessageQueue) TopicInfo(name string) (int, int, error) {
	topic, err := mq.broker.GetTopic(name)
	if err != nil {
		return 0, 0, err
	}
	return len(topic.Messages()), topic.SubscriberCount(), nil
}

// Close shuts down the message queue and releases resources.
func (mq *MessageQueue) Close() error {
	mq.broker.Close()
	if mq.store != nil {
		return mq.store.Close()
	}
	return nil
}

// Ensure interfaces are satisfied at compile time.
var _ persistence.Store = (*persistence.FileStore)(nil)
var _ persistence.Store = (*persistence.MemStore)(nil)
var _ *protocol.Message = (*protocol.Message)(nil)
