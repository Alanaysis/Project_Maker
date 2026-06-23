// Package message defines the core message types for exactly-once processing.
//
// A Message is the fundamental unit of work. Each message has a unique ID
// that is used for deduplication, and an idempotency key that determines
// whether two messages represent the same logical operation.
package message

import (
	"crypto/sha256"
	"fmt"
	"time"
)

// State represents the lifecycle state of a message.
type State int

const (
	// StatePending indicates the message has been received but not yet processed.
	StatePending State = iota
	// StateProcessing indicates the message is currently being processed.
	StateProcessing
	// StateCompleted indicates the message has been successfully processed.
	StateCompleted
	// StateFailed indicates the message processing failed.
	StateFailed
	// StateDuplicate indicates the message was identified as a duplicate.
	StateDuplicate
)

// String returns a human-readable representation of the message state.
func (s State) String() string {
	switch s {
	case StatePending:
		return "PENDING"
	case StateProcessing:
		return "PROCESSING"
	case StateCompleted:
		return "COMPLETED"
	case StateFailed:
		return "FAILED"
	case StateDuplicate:
		return "DUPLICATE"
	default:
		return fmt.Sprintf("UNKNOWN(%d)", int(s))
	}
}

// Message represents a unit of work to be processed exactly once.
type Message struct {
	// ID is the unique identifier for this specific message delivery.
	ID string

	// IdempotencyKey identifies the logical operation. Messages with the
	// same IdempotencyKey are considered duplicates and will only be
	// processed once.
	IdempotencyKey string

	// Payload is the message content to be processed.
	Payload []byte

	// State tracks the current lifecycle state.
	State State

	// CreatedAt is when the message was first created.
	CreatedAt time.Time

	// ProcessedAt is when the message processing completed (success or failure).
	ProcessedAt *time.Time

	// RetryCount tracks how many times this message has been retried.
	RetryCount int

	// MaxRetries is the maximum number of retries before marking as failed.
	MaxRetries int

	// Result stores the output of successful processing.
	Result []byte

	// Error stores the error message if processing failed.
	Error string

	// Metadata holds additional key-value pairs for the message.
	Metadata map[string]string
}

// New creates a new Message with default values.
func New(id string, payload []byte) *Message {
	return &Message{
		ID:          id,
		IdempotencyKey: GenerateIdempotencyKey(id, payload),
		Payload:     payload,
		State:       StatePending,
		CreatedAt:   time.Now(),
		MaxRetries:  3,
		Metadata:    make(map[string]string),
	}
}

// WithIdempotencyKey sets a custom idempotency key.
func (m *Message) WithIdempotencyKey(key string) *Message {
	m.IdempotencyKey = key
	return m
}

// WithMaxRetries sets the maximum number of retries.
func (m *Message) WithMaxRetries(max int) *Message {
	m.MaxRetries = max
	return m
}

// WithMetadata adds a metadata key-value pair.
func (m *Message) WithMetadata(key, value string) *Message {
	m.Metadata[key] = value
	return m
}

// MarkProcessing transitions the message to the processing state.
func (m *Message) MarkProcessing() {
	m.State = StateProcessing
}

// MarkCompleted transitions the message to the completed state with a result.
func (m *Message) MarkCompleted(result []byte) {
	now := time.Now()
	m.State = StateCompleted
	m.ProcessedAt = &now
	m.Result = result
}

// MarkFailed transitions the message to the failed state with an error.
func (m *Message) MarkFailed(err string) {
	now := time.Now()
	m.State = StateFailed
	m.ProcessedAt = &now
	m.Error = err
}

// MarkDuplicate transitions the message to the duplicate state.
func (m *Message) MarkDuplicate() {
	m.State = StateDuplicate
}

// CanRetry returns true if the message can be retried.
func (m *Message) CanRetry() bool {
	return m.State == StateFailed && m.RetryCount < m.MaxRetries
}

// IncrementRetry increments the retry counter and resets state to pending.
func (m *Message) IncrementRetry() {
	m.RetryCount++
	m.State = StatePending
	m.Error = ""
	m.ProcessedAt = nil
}

// IsTerminal returns true if the message is in a terminal state.
func (m *Message) IsTerminal() bool {
	return m.State == StateCompleted || m.State == StateDuplicate
}

// GenerateIdempotencyKey creates a deterministic idempotency key from
// the message ID and payload. This ensures the same logical operation
// always produces the same key.
func GenerateIdempotencyKey(id string, payload []byte) string {
	h := sha256.New()
	h.Write([]byte(id))
	h.Write(payload)
	return fmt.Sprintf("%x", h.Sum(nil))
}
