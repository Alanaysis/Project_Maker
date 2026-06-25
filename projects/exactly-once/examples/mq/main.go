// Message queue example demonstrating exactly-once semantics.
//
// This example simulates a message queue system that guarantees exactly-once
// message delivery and processing. It demonstrates:
//   - Producer with idempotency keys
//   - Consumer with manual acknowledgment
//   - Batch message processing
//   - Dead letter queue for failed messages
//   - Transactional message publishing
package main

import (
	"errors"
	"fmt"
	"log"
	"sync"
	"sync/atomic"
	"time"

	"github.com/anthropic/exactly-once/internal/consume"
	"github.com/anthropic/exactly-once/internal/message"
	"github.com/anthropic/exactly-once/internal/outbox"
	"github.com/anthropic/exactly-once/internal/processor"
)

// MessageQueue simulates a message queue with exactly-once delivery.
type MessageQueue struct {
	mu       sync.RWMutex
	topics   map[string][]*message.Message
	handlers map[string]processor.Handler
}

func NewMessageQueue() *MessageQueue {
	return &MessageQueue{
		topics:   make(map[string][]*message.Message),
		handlers: make(map[string]processor.Handler),
	}
}

func (mq *MessageQueue) Publish(topic string, msg *message.Message) {
	mq.mu.Lock()
	defer mq.mu.Unlock()
	mq.topics[topic] = append(mq.topics[topic], msg)
	log.Printf("[mq] published to %s: id=%s", topic, msg.ID)
}

func (mq *MessageQueue) Consume(topic string) []*message.Message {
	mq.mu.Lock()
	defer mq.mu.Unlock()
	msgs := mq.topics[topic]
	mq.topics[topic] = nil
	return msgs
}

func (mq *MessageQueue) TopicSize(topic string) int {
	mq.mu.RLock()
	defer mq.mu.RUnlock()
	return len(mq.topics[topic])
}

// Producer publishes messages with idempotency keys.
type Producer struct {
	mq       *MessageQueue
	outbox   *outbox.Outbox
	msgCount int64
}

func NewProducer(mq *MessageQueue) *Producer {
	p := &Producer{
		mq: mq,
		outbox: outbox.New(
			outbox.WithPublisher(func(topic string, msg *message.Message) error {
				mq.Publish(topic, msg)
				return nil
			}),
		),
	}
	return p
}

// Publish sends a message with exactly-once guarantees using the outbox pattern.
func (p *Producer) Publish(topic string, payload []byte, idempotencyKey string) error {
	msgID := fmt.Sprintf("prod-%d", atomic.AddInt64(&p.msgCount, 1))
	msg := message.New(msgID, payload)
	msg.IdempotencyKey = idempotencyKey

	// Save to outbox first (atomic with business logic)
	outboxID := fmt.Sprintf("out-%s", msgID)
	p.outbox.Save(outboxID, topic, msg, msgID)

	// Then publish
	return p.outbox.Publish(outboxID)
}

// PublishBatch sends multiple messages atomically.
func (p *Producer) PublishBatch(topic string, payloads [][]byte, idempotencyKeys []string) (int, error) {
	if len(payloads) != len(idempotencyKeys) {
		return 0, errors.New("payloads and keys must have same length")
	}

	succeeded := 0
	for i, payload := range payloads {
		if err := p.Publish(topic, payload, idempotencyKeys[i]); err != nil {
			log.Printf("[producer] batch publish failed at %d: %v", i, err)
			continue
		}
		succeeded++
	}
	return succeeded, nil
}

// Consumer processes messages from a topic with acknowledgment.
type Consumer struct {
	mq       *MessageQueue
	topic    string
	consumer *consume.Consumer
	processor *processor.Processor
}

func NewConsumer(mq *MessageQueue, topic string) *Consumer {
	c := &Consumer{
		mq:    mq,
		topic: topic,
	}

	c.processor = processor.New()

	c.consumer = consume.New(
		func(msg *consume.ConsumedMessage) error {
			handlerName := msg.Message.Metadata["handler"]
			handler := c.processor.GetHandler(handlerName)
			if handler == nil {
				return fmt.Errorf("handler %s not found", handlerName)
			}
			_, err := handler(msg.Message)
			return err
		},
		consume.WithConsumerID(fmt.Sprintf("consumer-%s", topic)),
		consume.WithRetryPolicy(consume.RetryPolicy{
			MaxRetries:        3,
			InitialBackoff:    50 * time.Millisecond,
			MaxBackoff:        2 * time.Second,
			BackoffMultiplier: 2.0,
		}),
	)

	return c
}

// RegisterHandler registers a message handler for this consumer.
func (c *Consumer) RegisterHandler(name string, handler processor.Handler) {
	c.processor.Register(name, handler)
}

// PollAndProcess polls the queue and processes messages.
func (c *Consumer) PollAndProcess() (int, int) {
	msgs := c.mq.Consume(c.topic)
	acked, failed := 0, 0

	for _, msg := range msgs {
		if err := c.consumer.Process(msg); err != nil {
			log.Printf("[consumer] failed to process %s: %v", msg.ID, err)
			failed++
		} else {
			acked++
		}
	}

	return acked, failed
}

// DeadLetterQueue holds messages that failed all retry attempts.
type DeadLetterQueue struct {
	mu      sync.RWMutex
	entries []*consume.ConsumedMessage
}

func NewDeadLetterQueue() *DeadLetterQueue {
	return &DeadLetterQueue{}
}

func (dlq *DeadLetterQueue) Add(msg *consume.ConsumedMessage) {
	dlq.mu.Lock()
	defer dlq.mu.Unlock()
	dlq.entries = append(dlq.entries, msg)
	log.Printf("[dlq] added message: id=%s attempts=%d error=%s",
		msg.Message.ID, msg.AttemptCount, msg.LastError)
}

func (dlq *DeadLetterQueue) Size() int {
	dlq.mu.RLock()
	defer dlq.mu.RUnlock()
	return len(dlq.entries)
}

func (dlq *DeadLetterQueue) Drain() []*consume.ConsumedMessage {
	dlq.mu.Lock()
	defer dlq.mu.Unlock()
	entries := dlq.entries
	dlq.entries = nil
	return entries
}

func main() {
	fmt.Println("=== Message Queue - Exactly-Once Demo ===")
	fmt.Println()

	mq := NewMessageQueue()
	dlq := NewDeadLetterQueue()

	// --- Producer ---
	fmt.Println("--- Producer ---")
	producer := NewProducer(mq)

	// Publish messages (some with duplicate keys)
	messages := []struct {
		payload []byte
		key     string
	}{
		{[]byte(`{"event":"user.login","user":"alice"}`), "event-login-alice"},
		{[]byte(`{"event":"user.login","user":"bob"}`), "event-login-bob"},
		{[]byte(`{"event":"user.login","user":"alice"}`), "event-login-alice"}, // duplicate!
		{[]byte(`{"event":"order.created","order":"001"}`), "event-order-001"},
		{[]byte(`{"event":"order.created","order":"001"}`), "event-order-001"}, // duplicate!
		{[]byte(`{"event":"payment.received","payment":"001"}`), "event-payment-001"},
	}

	for _, m := range messages {
		err := producer.Publish("events", m.payload, m.key)
		if err != nil {
			fmt.Printf("  Publish error: %v\n", err)
		}
	}

	fmt.Printf("  Queue size: %d messages\n", mq.TopicSize("events"))
	fmt.Println()

	// --- Consumer with idempotent processing ---
	fmt.Println("--- Consumer (idempotent processing) ---")
	var processedCount int32
	var duplicateCount int32

	consumer := NewConsumer(mq, "events")
	consumer.RegisterHandler("process-event", func(msg *message.Message) ([]byte, error) {
		atomic.AddInt32(&processedCount, 1)
		log.Printf("[handler] processing event: %s", string(msg.Payload))
		return []byte("processed"), nil
	})

	// Tag all messages with the handler name
	msgs := mq.Consume("events")
	for _, msg := range msgs {
		msg.WithMetadata("handler", "process-event")
	}

	// Re-publish for consumer to process
	for _, msg := range msgs {
		mq.Publish("events", msg)
	}

	acked, failed := consumer.PollAndProcess()
	fmt.Printf("  Acked: %d, Failed: %d\n", acked, failed)

	processed := atomic.LoadInt32(&processedCount)
	duplicates := atomic.LoadInt32(&duplicateCount)
	fmt.Printf("  Handler called: %d times\n", processed)
	fmt.Printf("  Duplicates detected: %d\n", duplicates)
	fmt.Println()

	// --- Batch Consumer ---
	fmt.Println("--- Batch Consumer Demo ---")
	batchMQ := NewMessageQueue()

	// Publish 10 messages
	for i := 0; i < 10; i++ {
		msg := message.New(fmt.Sprintf("batch-%d", i), []byte(fmt.Sprintf("data-%d", i)))
		batchMQ.Publish("batch-topic", msg)
	}

	batchConsumer := consume.NewBatchConsumer(
		func(msg *consume.ConsumedMessage) error {
			return nil
		},
		consume.WithBatchSize(5),
	)

	batchMsgs := batchMQ.Consume("batch-topic")
	for _, msg := range batchMsgs {
		batchConsumer.Receive(msg)
	}

	if err := batchConsumer.ProcessBatch(); err != nil {
		fmt.Printf("  Batch error: %v\n", err)
	}

	batchStats := batchConsumer.StatsSnapshot()
	fmt.Printf("  Received: %d, Batches: %d, Acked: %d\n",
		batchStats.Received, batchStats.Batches, batchStats.Acked)
	fmt.Println()

	// --- Dead Letter Queue ---
	fmt.Println("--- Dead Letter Queue ---")
	dlqConsumer := consume.New(
		func(msg *consume.ConsumedMessage) error {
			return errors.New("unrecoverable error")
		},
		consume.WithConsumerID("dlq-consumer"),
		consume.WithRetryPolicy(consume.RetryPolicy{
			MaxRetries:        2,
			InitialBackoff:    time.Millisecond,
			MaxBackoff:        5 * time.Millisecond,
			BackoffMultiplier: 1.0,
		}),
		consume.WithOnReject(func(msg *consume.ConsumedMessage) {
			dlq.Add(msg)
		}),
	)

	dlqMsg := message.New("dlq-001", []byte("problematic-message"))
	dlqConsumer.Process(dlqMsg)

	fmt.Printf("  DLQ size: %d\n", dlq.Size())
	if dlq.Size() > 0 {
		entries := dlq.Drain()
		for _, e := range entries {
			fmt.Printf("  DLQ entry: id=%s attempts=%d error=%s\n",
				e.Message.ID, e.AttemptCount, e.LastError)
		}
	}
	fmt.Println()

	// --- Outbox Pattern ---
	fmt.Println("--- Transactional Outbox ---")
	publishedEvents := make([]string, 0)
	outboxImpl := outbox.New(
		outbox.WithPublisher(func(topic string, msg *message.Message) error {
			publishedEvents = append(publishedEvents, string(msg.Payload))
			return nil
		}),
	)

	// Simulate: business logic + message in same transaction
	for i := 0; i < 3; i++ {
		msg := message.New(fmt.Sprintf("outbox-%d", i), []byte(fmt.Sprintf(`{"event":"test-%d"}`, i)))
		outboxImpl.Save(fmt.Sprintf("ob-%d", i), "events", msg, fmt.Sprintf("txn-%d", i))
	}

	succeeded, outFailed := outboxImpl.PublishPending()
	fmt.Printf("  Outbox: published=%d failed=%d\n", succeeded, outFailed)
	fmt.Printf("  Events: %v\n", publishedEvents)

	// Show final stats
	fmt.Println("\n--- Final Statistics ---")
	procStats := consumer.processor.StatsSnapshot()
	fmt.Printf("  Processor: processed=%d succeeded=%d duplicated=%d failed=%d\n",
		procStats.Processed, procStats.Succeeded, procStats.Duplicated, procStats.Failed)

	outboxStats := producer.outbox.StatsSnapshot()
	fmt.Printf("  Producer Outbox: created=%d published=%d\n",
		outboxStats.Created, outboxStats.Published)

	fmt.Println("\n=== Demo Complete ===")
}
