// Package protocol defines the core data structures for the message queue.
package protocol

import (
	"encoding/json"
	"time"
)

// MessageStatus represents the lifecycle state of a message.
type MessageStatus int

const (
	// StatusPending means the message has been published but not yet delivered.
	StatusPending MessageStatus = iota
	// StatusDelivered means the message has been sent to a consumer.
	StatusDelivered
	// StatusAcknowledged means the consumer confirmed processing.
	StatusAcknowledged
)

// Message is the fundamental unit of data in the queue.
type Message struct {
	ID           string        `json:"id"`
	Topic        string        `json:"topic"`
	Payload      []byte        `json:"payload"`
	Status       MessageStatus `json:"status"`
	CreatedAt    time.Time     `json:"created_at"`
	DeliveredAt  *time.Time    `json:"delivered_at,omitempty"`
	AcknowledgedAt *time.Time  `json:"acknowledged_at,omitempty"`
	RetryCount   int           `json:"retry_count"`
}

// NewMessage creates a new message with a generated ID.
func NewMessage(topic string, payload []byte) *Message {
	return &Message{
		ID:        generateID(),
		Topic:     topic,
		Payload:   payload,
		Status:    StatusPending,
		CreatedAt: time.Now(),
	}
}

// MarshalJSON implements custom JSON marshaling for MessageStatus.
func (m Message) MarshalJSON() ([]byte, error) {
	type Alias Message
	return json.Marshal(&struct {
		Alias
		Status string `json:"status"`
	}{
		Alias:  (Alias)(m),
		Status: m.Status.String(),
	})
}

// UnmarshalJSON implements custom JSON unmarshaling for MessageStatus.
func (m *Message) UnmarshalJSON(data []byte) error {
	type Alias Message
	aux := &struct {
		Alias
		Status string `json:"status"`
	}{}
	if err := json.Unmarshal(data, aux); err != nil {
		return err
	}
	*m = Message(aux.Alias)
	m.Status = parseStatus(aux.Status)
	return nil
}

// parseStatus converts a string back to MessageStatus.
func parseStatus(s string) MessageStatus {
	switch s {
	case "pending":
		return StatusPending
	case "delivered":
		return StatusDelivered
	case "acknowledged":
		return StatusAcknowledged
	default:
		return StatusPending
	}
}

// String returns a human-readable representation of the message status.
func (s MessageStatus) String() string {
	switch s {
	case StatusPending:
		return "pending"
	case StatusDelivered:
		return "delivered"
	case StatusAcknowledged:
		return "acknowledged"
	default:
		return "unknown"
	}
}

// MarkDelivered transitions the message to delivered status.
func (m *Message) MarkDelivered() {
	now := time.Now()
	m.Status = StatusDelivered
	m.DeliveredAt = &now
}

// MarkAcknowledged transitions the message to acknowledged status.
func (m *Message) MarkAcknowledged() {
	now := time.Now()
	m.Status = StatusAcknowledged
	m.AcknowledgedAt = &now
}

// generateID creates a unique message identifier.
func generateID() string {
	return time.Now().Format("20060102150405.000000000") + "-" + randomHex(8)
}

// randomHex generates a random hex string of the given length.
func randomHex(n int) string {
	const hex = "0123456789abcdef"
	b := make([]byte, n)
	for i := range b {
		b[i] = hex[time.Now().UnixNano()%16]
		time.Sleep(1) // ensure different nanosecond
	}
	return string(b)
}
