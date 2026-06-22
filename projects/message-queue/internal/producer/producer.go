// Package producer provides the message publisher abstraction.
package producer

import (
	"fmt"

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
