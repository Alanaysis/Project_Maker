package source

import (
	"fmt"
	"sync"
	"time"

	"github.com/learning/stream-processing/internal/core"
)

// KafkaMessage represents a simplified Kafka message.
// In a real implementation, this would use a Kafka client library.
type KafkaMessage struct {
	Topic     string
	Partition int
	Offset    int64
	Key       string
	Value     string
	Timestamp time.Time
}

// KafkaConsumer is an interface for Kafka consumer operations.
// This allows for mock implementations in testing.
type KafkaConsumer interface {
	// Subscribe starts consuming from the given topics.
	Subscribe(topics []string) error

	// ReadMessage reads the next message. Blocks until a message is available
	// or the consumer is closed.
	ReadMessage() (KafkaMessage, error)

	// Close stops the consumer.
	Close() error
}

// KafkaSource reads messages from Apache Kafka topics.
//
// Usage:
//
//	consumer := NewMockKafkaConsumer(messages)
//	src := NewKafkaSource(consumer, []string{"my-topic"})
//	stream, err := src.Open()
//
// Note: This implementation uses a KafkaConsumer interface.
// For production, implement this interface with a real Kafka client
// (e.g., confluent-kafka-go, segmentio/kafka-go, or Sarama).
type KafkaSource struct {
	consumer KafkaConsumer
	topics   []string
	groupID  string
	stopped  bool
	mu       sync.Mutex
	stopCh   chan struct{}
}

// KafkaSourceOption configures a KafkaSource.
type KafkaSourceOption func(*KafkaSource)

// WithGroupID sets the consumer group ID.
func WithGroupID(groupID string) KafkaSourceOption {
	return func(ks *KafkaSource) {
		ks.groupID = groupID
	}
}

// NewKafkaSource creates a Kafka source with the given consumer and topics.
func NewKafkaSource(consumer KafkaConsumer, topics []string, opts ...KafkaSourceOption) *KafkaSource {
	ks := &KafkaSource{
		consumer: consumer,
		topics:   topics,
		stopCh:   make(chan struct{}),
	}

	for _, opt := range opts {
		opt(ks)
	}

	return ks
}

func (ks *KafkaSource) Name() string {
	return fmt.Sprintf("kafka:%v", ks.topics)
}

// Open subscribes to topics and emits messages as events.
func (ks *KafkaSource) Open() (*core.Stream, error) {
	if err := ks.consumer.Subscribe(ks.topics); err != nil {
		return nil, fmt.Errorf("subscribe to %v: %w", ks.topics, err)
	}

	stream := core.NewStream(1000)

	go func() {
		defer stream.Close()

		for {
			ks.mu.Lock()
			if ks.stopped {
				ks.mu.Unlock()
				return
			}
			ks.mu.Unlock()

			msg, err := ks.consumer.ReadMessage()
			if err != nil {
				// In production, check for specific errors
				// (e.g., consumer closed, timeout, etc.)
				select {
				case <-ks.stopCh:
					return
				default:
					continue
				}
			}

			key := msg.Key
			if key == "" {
				key = msg.Topic
			}

			event := core.NewEventWithTime(
				key,
				msg.Value,
				msg.Timestamp,
			)

			select {
			case <-ks.stopCh:
				return
			default:
				if !stream.Emit(event) {
					return
				}
			}
		}
	}()

	return stream, nil
}

// Stop signals the source to stop consuming.
func (ks *KafkaSource) Stop() error {
	ks.mu.Lock()
	defer ks.mu.Unlock()

	if !ks.stopped {
		ks.stopped = true
		close(ks.stopCh)
		return ks.consumer.Close()
	}
	return nil
}

// MockKafkaConsumer is an in-memory Kafka consumer for testing.
type MockKafkaConsumer struct {
	messages []KafkaMessage
	index    int
	mu       sync.Mutex
}

// NewMockKafkaConsumer creates a mock consumer with the given messages.
func NewMockKafkaConsumer(messages []KafkaMessage) *MockKafkaConsumer {
	return &MockKafkaConsumer{
		messages: messages,
	}
}

func (m *MockKafkaConsumer) Subscribe(topics []string) error {
	return nil
}

func (m *MockKafkaConsumer) ReadMessage() (KafkaMessage, error) {
	m.mu.Lock()
	defer m.mu.Unlock()

	if m.index >= len(m.messages) {
		// Block until closed (simulating waiting for new messages)
		time.Sleep(time.Hour)
		return KafkaMessage{}, fmt.Errorf("consumer closed")
	}

	msg := m.messages[m.index]
	m.index++
	return msg, nil
}

func (m *MockKafkaConsumer) Close() error {
	return nil
}
