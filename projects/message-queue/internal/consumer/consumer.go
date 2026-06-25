// Package consumer provides the message subscriber abstraction.
package consumer

import (
	"fmt"
	"sync"
	"time"

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
	return c.SubscribeWithFilter(topic, nil)
}

// SubscribeWithFilter starts receiving messages from a topic with an optional filter.
func (c *Consumer) SubscribeWithFilter(topic string, filter map[string]string) error {
	c.mu.Lock()
	defer c.mu.Unlock()

	if _, exists := c.subs[topic]; exists {
		return fmt.Errorf("already subscribed to %q", topic)
	}

	sub, err := c.broker.SubscribeWithFilter(topic, c.ID, filter)
	if err != nil {
		return fmt.Errorf("subscribe to %q: %w", topic, err)
	}

	c.subs[topic] = sub

	// Start consuming in a goroutine.
	go c.consumeLoop(sub, topic)
	return nil
}

// JoinGroup joins a consumer group for point-to-point messaging.
func (c *Consumer) JoinGroup(groupName string) error {
	c.mu.Lock()
	defer c.mu.Unlock()

	gc, err := c.broker.JoinConsumerGroup(groupName, c.ID)
	if err != nil {
		return fmt.Errorf("join group %q: %w", groupName, err)
	}

	// Start consuming from the group channel.
	go c.consumeGroupLoop(gc, groupName)
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

// consumeGroupLoop reads messages from a consumer group channel.
func (c *Consumer) consumeGroupLoop(gc *queue.GroupConsumer, groupName string) {
	for {
		select {
		case msg, ok := <-gc.Ch:
			if !ok {
				return // channel closed
			}
			msg.MarkDelivered()

			if err := c.handler(msg); err != nil {
				// Handler error: negative ack for retry.
				c.broker.NegativeAcknowledge(msg.Topic, msg.ID)
				continue
			}

			// Auto-acknowledge on successful handler execution.
			if err := c.broker.Acknowledge(msg.Topic, msg.ID); err != nil {
				fmt.Printf("ack error for %s: %v\n", msg.ID, err)
			}

		case <-c.done:
			return
		}
	}
}

// Pull retrieves the next available message from a topic (pull mode).
func (c *Consumer) Pull(topic string, timeout time.Duration) (*protocol.Message, error) {
	return c.broker.Pull(topic, timeout)
}

// PullAndProcess pulls a message and processes it with the handler.
func (c *Consumer) PullAndProcess(topic string, timeout time.Duration) error {
	msg, err := c.Pull(topic, timeout)
	if err != nil {
		return err
	}

	if err := c.handler(msg); err != nil {
		// Negative ack for retry.
		c.broker.NegativeAcknowledge(msg.Topic, msg.ID)
		return fmt.Errorf("handler error: %w", err)
	}

	// Acknowledge on success.
	if err := c.broker.Acknowledge(msg.Topic, msg.ID); err != nil {
		return fmt.Errorf("ack error: %w", err)
	}

	return nil
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

// LeaveGroup leaves a consumer group.
func (c *Consumer) LeaveGroup(groupName string) {
	c.broker.LeaveConsumerGroup(groupName, c.ID)
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
