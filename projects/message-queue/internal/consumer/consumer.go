// Package consumer provides the message subscriber abstraction.
package consumer

import (
	"fmt"
	"sync"

	"github.com/example/message-queue/internal/protocol"
	"github.com/example/message-queue/internal/queue"
)

// Handler is a callback invoked for each delivered message.
type Handler func(msg *protocol.Message) error

// Consumer subscribes to topics and processes messages via a handler.
type Consumer struct {
	ID       string
	broker   *queue.Broker
	handler  Handler
	subs     map[string]*queue.Subscriber
	mu       sync.Mutex
	done     chan struct{}
	closed   bool
}

// New creates a consumer with the given ID and message handler.
func New(id string, broker *queue.Broker, handler Handler) *Consumer {
	return &Consumer{
		ID:      id,
		broker:  broker,
		handler: handler,
		subs:    make(map[string]*queue.Subscriber),
		done:    make(chan struct{}),
	}
}

// Subscribe starts receiving messages from a topic.
func (c *Consumer) Subscribe(topic string) error {
	c.mu.Lock()
	defer c.mu.Unlock()

	if _, exists := c.subs[topic]; exists {
		return fmt.Errorf("already subscribed to %q", topic)
	}

	sub, err := c.broker.Subscribe(topic, c.ID)
	if err != nil {
		return fmt.Errorf("subscribe to %q: %w", topic, err)
	}

	c.subs[topic] = sub

	// Start consuming in a goroutine.
	go c.consumeLoop(sub, topic)
	return nil
}

// consumeLoop reads messages from the subscription channel and processes them.
func (c *Consumer) consumeLoop(sub *queue.Subscriber, topic string) {
	for {
		select {
		case msg, ok := <-sub.Ch:
			if !ok {
				return // channel closed
			}
			msg.MarkDelivered()

			if err := c.handler(msg); err != nil {
				// Handler error: message stays unacknowledged for retry.
				continue
			}

			// Auto-acknowledge on successful handler execution.
			if err := c.broker.Acknowledge(topic, msg.ID); err != nil {
				// Log error but continue processing.
				fmt.Printf("ack error for %s: %v\n", msg.ID, err)
			}

		case <-c.done:
			return
		}
	}
}

// Unsubscribe stops receiving messages from a topic.
func (c *Consumer) Unsubscribe(topic string) {
	c.mu.Lock()
	defer c.mu.Unlock()

	if sub, exists := c.subs[topic]; exists {
		c.broker.Unsubscribe(topic, sub.ID)
		delete(c.subs, topic)
	}
}

// Close stops all subscriptions and cleans up.
func (c *Consumer) Close() {
	c.mu.Lock()
	defer c.mu.Unlock()

	if c.closed {
		return
	}
	c.closed = true
	close(c.done)

	for topic, sub := range c.subs {
		c.broker.Unsubscribe(topic, sub.ID)
	}
	c.subs = make(map[string]*queue.Subscriber)
}
