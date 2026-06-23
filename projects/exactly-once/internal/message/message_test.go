package message

import (
	"testing"
	"time"
)

func TestNewMessage(t *testing.T) {
	msg := New("msg-001", []byte("hello"))

	if msg.ID != "msg-001" {
		t.Errorf("expected ID 'msg-001', got '%s'", msg.ID)
	}
	if msg.State != StatePending {
		t.Errorf("expected state PENDING, got %s", msg.State)
	}
	if msg.MaxRetries != 3 {
		t.Errorf("expected MaxRetries 3, got %d", msg.MaxRetries)
	}
	if msg.RetryCount != 0 {
		t.Errorf("expected RetryCount 0, got %d", msg.RetryCount)
	}
	if msg.IdempotencyKey == "" {
		t.Error("expected non-empty idempotency key")
	}
	if msg.Metadata == nil {
		t.Error("expected non-nil metadata")
	}
}

func TestMessageStateTransitions(t *testing.T) {
	msg := New("msg-001", []byte("test"))

	// PENDING -> PROCESSING
	msg.MarkProcessing()
	if msg.State != StateProcessing {
		t.Errorf("expected PROCESSING, got %s", msg.State)
	}

	// PROCESSING -> COMPLETED
	msg.MarkCompleted([]byte("result"))
	if msg.State != StateCompleted {
		t.Errorf("expected COMPLETED, got %s", msg.State)
	}
	if msg.ProcessedAt == nil {
		t.Error("expected ProcessedAt to be set")
	}
	if string(msg.Result) != "result" {
		t.Errorf("expected result 'result', got '%s'", string(msg.Result))
	}
}

func TestMessageMarkFailed(t *testing.T) {
	msg := New("msg-001", []byte("test"))
	msg.MarkProcessing()
	msg.MarkFailed("connection timeout")

	if msg.State != StateFailed {
		t.Errorf("expected FAILED, got %s", msg.State)
	}
	if msg.Error != "connection timeout" {
		t.Errorf("expected error 'connection timeout', got '%s'", msg.Error)
	}
	if msg.ProcessedAt == nil {
		t.Error("expected ProcessedAt to be set")
	}
}

func TestMessageMarkDuplicate(t *testing.T) {
	msg := New("msg-001", []byte("test"))
	msg.MarkDuplicate()

	if msg.State != StateDuplicate {
		t.Errorf("expected DUPLICATE, got %s", msg.State)
	}
}

func TestMessageCanRetry(t *testing.T) {
	msg := New("msg-001", []byte("test"))
	msg.MaxRetries = 2

	// Pending message cannot retry
	if msg.CanRetry() {
		t.Error("pending message should not be retryable")
	}

	// Failed message can retry (count < max)
	msg.MarkFailed("error")
	if !msg.CanRetry() {
		t.Error("failed message with retries left should be retryable")
	}

	// After max retries, cannot retry
	msg.IncrementRetry()
	msg.MarkFailed("error")
	msg.IncrementRetry()
	msg.MarkFailed("error")
	if msg.CanRetry() {
		t.Error("message at max retries should not be retryable")
	}
}

func TestMessageIncrementRetry(t *testing.T) {
	msg := New("msg-001", []byte("test"))
	msg.MarkFailed("error")

	msg.IncrementRetry()
	if msg.RetryCount != 1 {
		t.Errorf("expected RetryCount 1, got %d", msg.RetryCount)
	}
	if msg.State != StatePending {
		t.Errorf("expected PENDING after retry, got %s", msg.State)
	}
	if msg.Error != "" {
		t.Error("expected error to be cleared after retry")
	}
}

func TestMessageIsTerminal(t *testing.T) {
	tests := []struct {
		state    State
		terminal bool
	}{
		{StatePending, false},
		{StateProcessing, false},
		{StateCompleted, true},
		{StateFailed, false},
		{StateDuplicate, true},
	}

	for _, tt := range tests {
		msg := New("msg-001", []byte("test"))
		msg.State = tt.state
		if got := msg.IsTerminal(); got != tt.terminal {
			t.Errorf("state %s: expected IsTerminal=%v, got %v", tt.state, tt.terminal, got)
		}
	}
}

func TestMessageWithIdempotencyKey(t *testing.T) {
	msg := New("msg-001", []byte("test"))
	originalKey := msg.IdempotencyKey

	msg.WithIdempotencyKey("custom-key")
	if msg.IdempotencyKey != "custom-key" {
		t.Errorf("expected 'custom-key', got '%s'", msg.IdempotencyKey)
	}
	if msg.IdempotencyKey == originalKey {
		t.Error("expected idempotency key to change")
	}
}

func TestMessageWithMaxRetries(t *testing.T) {
	msg := New("msg-001", []byte("test"))
	msg.WithMaxRetries(10)

	if msg.MaxRetries != 10 {
		t.Errorf("expected MaxRetries 10, got %d", msg.MaxRetries)
	}
}

func TestMessageWithMetadata(t *testing.T) {
	msg := New("msg-001", []byte("test"))
	msg.WithMetadata("source", "kafka").WithMetadata("topic", "orders")

	if msg.Metadata["source"] != "kafka" {
		t.Errorf("expected metadata source=kafka, got %s", msg.Metadata["source"])
	}
	if msg.Metadata["topic"] != "orders" {
		t.Errorf("expected metadata topic=orders, got %s", msg.Metadata["topic"])
	}
}

func TestStateString(t *testing.T) {
	tests := []struct {
		state    State
		expected string
	}{
		{StatePending, "PENDING"},
		{StateProcessing, "PROCESSING"},
		{StateCompleted, "COMPLETED"},
		{StateFailed, "FAILED"},
		{StateDuplicate, "DUPLICATE"},
		{State(99), "UNKNOWN(99)"},
	}

	for _, tt := range tests {
		if got := tt.state.String(); got != tt.expected {
			t.Errorf("State(%d).String() = %q, want %q", int(tt.state), got, tt.expected)
		}
	}
}

func TestGenerateIdempotencyKey(t *testing.T) {
	// Same input should produce same key
	key1 := GenerateIdempotencyKey("msg-001", []byte("payload"))
	key2 := GenerateIdempotencyKey("msg-001", []byte("payload"))
	if key1 != key2 {
		t.Errorf("expected deterministic keys, got %s and %s", key1, key2)
	}

	// Different input should produce different key
	key3 := GenerateIdempotencyKey("msg-002", []byte("payload"))
	if key1 == key3 {
		t.Error("expected different keys for different IDs")
	}

	key4 := GenerateIdempotencyKey("msg-001", []byte("different"))
	if key1 == key4 {
		t.Error("expected different keys for different payloads")
	}
}

func TestMessageTimestamps(t *testing.T) {
	before := time.Now()
	msg := New("msg-001", []byte("test"))
	after := time.Now()

	if msg.CreatedAt.Before(before) || msg.CreatedAt.After(after) {
		t.Error("expected CreatedAt to be between before and after")
	}
	if msg.ProcessedAt != nil {
		t.Error("expected ProcessedAt to be nil for new message")
	}
}
