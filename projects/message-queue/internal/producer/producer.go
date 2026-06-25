// Package producer provides the message publisher abstraction.
package producer

import (
	"fmt"
	"time"

	"github.com/example/message-queue/internal/protocol"
	"github.com/example/message-queue/internal/queue"
)

// Producer publishes messages to topics on a broker.
type Producer struct {
	broker *queue.Broker
}

// New creates a producer attached to the given broker.
func New(broker *queue.Broker) *Producer {
	return &Producer{broker: broker}
}

// Publish sends a message payload to a topic and returns the created message.
func (p *Producer) Publish(topic string, payload []byte) (*protocol.Message, error) {
	msg, err := p.broker.Publish(topic, payload)
	if err != nil {
		return nil, fmt.Errorf("publish to %q: %w", topic, err)
	}
	return msg, nil
}

// PublishString is a convenience method that accepts a string payload.
func (p *Producer) PublishString(topic string, payload string) (*protocol.Message, error) {
	return p.Publish(topic, []byte(payload))
}

// PublishWithPriority sends a message with a specific priority.
func (p *Producer) PublishWithPriority(topic string, payload []byte, priority protocol.Priority) (*protocol.Message, error) {
	msg, err := p.broker.PublishWithPriority(topic, payload, priority)
	if err != nil {
		return nil, fmt.Errorf("publish to %q with priority: %w", topic, err)
	}
	return msg, nil
}

// PublishDelayed sends a message that will be delivered after the specified delay.
func (p *Producer) PublishDelayed(topic string, payload []byte, delay time.Duration) (*protocol.Message, error) {
	msg, err := p.broker.PublishDelayed(topic, payload, delay)
	if err != nil {
		return nil, fmt.Errorf("publish delayed to %q: %w", topic, err)
	}
	return msg, nil
}

// PublishWithHeaders sends a message with custom headers for filtering.
func (p *Producer) PublishWithHeaders(topic string, payload []byte, headers map[string]string) (*protocol.Message, error) {
	msg, err := p.broker.PublishWithHeaders(topic, payload, headers)
	if err != nil {
		return nil, fmt.Errorf("publish to %q with headers: %w", topic, err)
	}
	return msg, nil
}

// PublishWithOptions sends a message with full options.
func (p *Producer) PublishWithOptions(topic string, payload []byte, priority protocol.Priority, headers map[string]string, delay *time.Duration) (*protocol.Message, error) {
	msg, err := p.broker.PublishWithOptions(topic, payload, priority, headers, delay)
	if err != nil {
		return nil, fmt.Errorf("publish to %q with options: %w", topic, err)
	}
	return msg, nil
}

// Pull retrieves the next available message from a topic (pull mode).
func (p *Producer) Pull(topic string, timeout time.Duration) (*protocol.Message, error) {
	msg, err := p.broker.Pull(topic, timeout)
	if err != nil {
		return nil, fmt.Errorf("pull from %q: %w", topic, err)
	}
	return msg, nil
}
