// Package protocol defines the core data structures for the message queue.
package protocol

import (
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"strings"
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
	// StatusDeadLetter means the message exceeded max retries.
	StatusDeadLetter
)

// Priority levels for messages.
type Priority int

const (
	PriorityLow    Priority = 0
	PriorityNormal Priority = 5
	PriorityHigh   Priority = 10
)

// Message is the fundamental unit of data in the queue.
type Message struct {
	ID             string            `json:"id"`
	Topic          string            `json:"topic"`
	Payload        []byte            `json:"payload"`
	Status         MessageStatus     `json:"status"`
	Priority       Priority          `json:"priority"`
	Headers        map[string]string `json:"headers,omitempty"`
	CreatedAt      time.Time         `json:"created_at"`
	DeliveredAt    *time.Time        `json:"delivered_at,omitempty"`
	AcknowledgedAt *time.Time        `json:"acknowledged_at,omitempty"`
	DeliverAfter   *time.Time        `json:"deliver_after,omitempty"`
	RetryCount     int               `json:"retry_count"`
	MaxRetries     int               `json:"max_retries"`
	ConsumerGroup  string            `json:"consumer_group,omitempty"`
}

// NewMessage creates a new message with a generated ID.
func NewMessage(topic string, payload []byte) *Message {
	return &Message{
		ID:         generateID(),
		Topic:      topic,
		Payload:    payload,
		Status:     StatusPending,
		Priority:   PriorityNormal,
		Headers:    make(map[string]string),
		CreatedAt:  time.Now(),
		MaxRetries: 3, // default max retries
	}
}

// WithPriority sets the message priority.
func (m *Message) WithPriority(p Priority) *Message {
	m.Priority = p
	return m
}

// WithHeaders sets the message headers.
func (m *Message) WithHeaders(headers map[string]string) *Message {
	m.Headers = headers
	return m
}

// WithHeader adds a single header to the message.
func (m *Message) WithHeader(key, value string) *Message {
	if m.Headers == nil {
		m.Headers = make(map[string]string)
	}
	m.Headers[key] = value
	return m
}

// WithMaxRetries sets the maximum retry count.
func (m *Message) WithMaxRetries(max int) *Message {
	m.MaxRetries = max
	return m
}

// WithDelay sets a delivery delay from now.
func (m *Message) WithDelay(d time.Duration) *Message {
	after := time.Now().Add(d)
	m.DeliverAfter = &after
	return m
}

// WithDeliverAfter sets an absolute time after which the message should be delivered.
func (m *Message) WithDeliverAfter(t time.Time) *Message {
	m.DeliverAfter = &t
	return m
}

// IsReady returns true if the message is ready to be delivered (delay expired).
func (m *Message) IsReady() bool {
	if m.DeliverAfter == nil {
		return true
	}
	return time.Now().After(*m.DeliverAfter)
}

// MatchesFilter returns true if the message headers match the given filter.
func (m *Message) MatchesFilter(filter map[string]string) bool {
	if len(filter) == 0 {
		return true
	}
	if m.Headers == nil {
		return false
	}
	for k, v := range filter {
		if msgVal, ok := m.Headers[k]; !ok || msgVal != v {
			return false
		}
	}
	return true
}

// CanRetry returns true if the message has not exceeded its retry limit.
func (m *Message) CanRetry() bool {
	return m.RetryCount < m.MaxRetries
}

// IncrementRetry increments the retry counter.
func (m *Message) IncrementRetry() {
	m.RetryCount++
	m.Status = StatusPending
	m.DeliveredAt = nil
}

// MarkDeadLetter marks the message as dead letter (exceeded retries).
func (m *Message) MarkDeadLetter() {
	m.Status = StatusDeadLetter
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
	case "dead_letter":
		return StatusDeadLetter
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
	case StatusDeadLetter:
		return "dead_letter"
	default:
		return "unknown"
	}
}

// String returns a human-readable representation of the priority.
func (p Priority) String() string {
	switch p {
	case PriorityLow:
		return "low"
	case PriorityNormal:
		return "normal"
	case PriorityHigh:
		return "high"
	default:
		return "normal"
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

// randomHex generates a cryptographically random hex string of the given byte length.
func randomHex(n int) string {
	b := make([]byte, n)
	if _, err := rand.Read(b); err != nil {
		// Fallback to time-based if crypto/rand fails (should not happen).
		const hex = "0123456789abcdef"
		for i := range b {
			b[i] = hex[time.Now().UnixNano()%16]
			time.Sleep(1)
		}
		return string(b)
	}
	return hex.EncodeToString(b)
}

// MatchesHeaderFilter checks if message headers contain all key-value pairs in the filter.
func MatchesHeaderFilter(headers map[string]string, filter map[string]string) bool {
	if len(filter) == 0 {
		return true
	}
	if len(headers) == 0 {
		return false
	}
	for k, v := range filter {
		if msgVal, ok := headers[k]; !ok || !strings.Contains(msgVal, v) {
			return false
		}
	}
	return true
}
