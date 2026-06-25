package protocol

import (
	"encoding/json"
	"testing"
	"time"
)

func TestNewMessage(t *testing.T) {
	msg := NewMessage("test-topic", []byte("hello"))

	if msg.ID == "" {
		t.Error("expected non-empty ID")
	}
	if msg.Topic != "test-topic" {
		t.Errorf("expected topic 'test-topic', got %q", msg.Topic)
	}
	if string(msg.Payload) != "hello" {
		t.Errorf("expected payload 'hello', got %q", string(msg.Payload))
	}
	if msg.Status != StatusPending {
		t.Errorf("expected status pending, got %v", msg.Status)
	}
	if msg.CreatedAt.IsZero() {
		t.Error("expected non-zero CreatedAt")
	}
	if msg.Priority != PriorityNormal {
		t.Errorf("expected normal priority, got %v", msg.Priority)
	}
	if msg.MaxRetries != 3 {
		t.Errorf("expected max retries 3, got %d", msg.MaxRetries)
	}
	if msg.Headers == nil {
		t.Error("expected non-nil headers")
	}
}

func TestMessageStatusTransitions(t *testing.T) {
	msg := NewMessage("t", []byte("x"))

	msg.MarkDelivered()
	if msg.Status != StatusDelivered {
		t.Errorf("expected delivered, got %v", msg.Status)
	}
	if msg.DeliveredAt == nil {
		t.Error("expected non-nil DeliveredAt")
	}

	msg.MarkAcknowledged()
	if msg.Status != StatusAcknowledged {
		t.Errorf("expected acknowledged, got %v", msg.Status)
	}
	if msg.AcknowledgedAt == nil {
		t.Error("expected non-nil AcknowledgedAt")
	}
}

func TestMessageStatusDeadLetter(t *testing.T) {
	msg := NewMessage("t", []byte("x"))
	msg.MarkDeadLetter()

	if msg.Status != StatusDeadLetter {
		t.Errorf("expected dead_letter, got %v", msg.Status)
	}
}

func TestMessageStatusString(t *testing.T) {
	tests := []struct {
		status MessageStatus
		want   string
	}{
		{StatusPending, "pending"},
		{StatusDelivered, "delivered"},
		{StatusAcknowledged, "acknowledged"},
		{StatusDeadLetter, "dead_letter"},
		{MessageStatus(99), "unknown"},
	}

	for _, tc := range tests {
		if got := tc.status.String(); got != tc.want {
			t.Errorf("Status(%d).String() = %q, want %q", tc.status, got, tc.want)
		}
	}
}

func TestMessagePriorityString(t *testing.T) {
	tests := []struct {
		priority Priority
		want     string
	}{
		{PriorityLow, "low"},
		{PriorityNormal, "normal"},
		{PriorityHigh, "high"},
		{Priority(99), "normal"},
	}

	for _, tc := range tests {
		if got := tc.priority.String(); got != tc.want {
			t.Errorf("Priority(%d).String() = %q, want %q", tc.priority, got, tc.want)
		}
	}
}

func TestMessageWithPriority(t *testing.T) {
	msg := NewMessage("t", []byte("x")).WithPriority(PriorityHigh)

	if msg.Priority != PriorityHigh {
		t.Errorf("expected high priority, got %v", msg.Priority)
	}
}

func TestMessageWithHeaders(t *testing.T) {
	headers := map[string]string{"key1": "value1", "key2": "value2"}
	msg := NewMessage("t", []byte("x")).WithHeaders(headers)

	if msg.Headers["key1"] != "value1" {
		t.Errorf("expected header key1=value1, got %q", msg.Headers["key1"])
	}
}

func TestMessageWithHeader(t *testing.T) {
	msg := NewMessage("t", []byte("x")).WithHeader("key", "value")

	if msg.Headers["key"] != "value" {
		t.Errorf("expected header key=value, got %q", msg.Headers["key"])
	}
}

func TestMessageWithMaxRetries(t *testing.T) {
	msg := NewMessage("t", []byte("x")).WithMaxRetries(5)

	if msg.MaxRetries != 5 {
		t.Errorf("expected max retries 5, got %d", msg.MaxRetries)
	}
}

func TestMessageWithDelay(t *testing.T) {
	msg := NewMessage("t", []byte("x")).WithDelay(5 * time.Second)

	if msg.DeliverAfter == nil {
		t.Error("expected non-nil DeliverAfter")
	}
	if msg.DeliverAfter.Before(time.Now()) {
		t.Error("expected DeliverAfter to be in the future")
	}
}

func TestMessageIsReady(t *testing.T) {
	// No delay - should be ready.
	msg1 := NewMessage("t", []byte("x"))
	if !msg1.IsReady() {
		t.Error("expected message without delay to be ready")
	}

	// Future delay - should not be ready.
	msg2 := NewMessage("t", []byte("x")).WithDelay(1 * time.Hour)
	if msg2.IsReady() {
		t.Error("expected message with future delay to not be ready")
	}

	// Past delay - should be ready.
	msg3 := NewMessage("t", []byte("x")).WithDelay(-1 * time.Second)
	if !msg3.IsReady() {
		t.Error("expected message with past delay to be ready")
	}
}

func TestMessageMatchesFilter(t *testing.T) {
	msg := NewMessage("t", []byte("x")).WithHeaders(map[string]string{
		"channel": "sms",
		"type":    "alert",
	})

	// Empty filter matches everything.
	if !msg.MatchesFilter(map[string]string{}) {
		t.Error("expected empty filter to match")
	}

	// Matching filter.
	if !msg.MatchesFilter(map[string]string{"channel": "sms"}) {
		t.Error("expected matching filter to match")
	}

	// Non-matching filter.
	if msg.MatchesFilter(map[string]string{"channel": "email"}) {
		t.Error("expected non-matching filter to not match")
	}

	// Missing key.
	if msg.MatchesFilter(map[string]string{"missing": "value"}) {
		t.Error("expected missing key filter to not match")
	}
}

func TestMessageCanRetry(t *testing.T) {
	msg := NewMessage("t", []byte("x")).WithMaxRetries(3)

	if !msg.CanRetry() {
		t.Error("expected new message to be retryable")
	}

	msg.RetryCount = 2
	if !msg.CanRetry() {
		t.Error("expected message with retry count 2 to be retryable")
	}

	msg.RetryCount = 3
	if msg.CanRetry() {
		t.Error("expected message with retry count 3 to not be retryable")
	}
}

func TestMessageIncrementRetry(t *testing.T) {
	msg := NewMessage("t", []byte("x"))
	msg.MarkDelivered()

	msg.IncrementRetry()

	if msg.RetryCount != 1 {
		t.Errorf("expected retry count 1, got %d", msg.RetryCount)
	}
	if msg.Status != StatusPending {
		t.Errorf("expected status pending after retry, got %v", msg.Status)
	}
	if msg.DeliveredAt != nil {
		t.Error("expected nil DeliveredAfter retry")
	}
}

func TestMatchesHeaderFilter(t *testing.T) {
	headers := map[string]string{
		"channel":  "sms",
		"severity": "high",
	}

	// Empty filter matches everything.
	if !MatchesHeaderFilter(headers, map[string]string{}) {
		t.Error("expected empty filter to match")
	}

	// Matching filter.
	if !MatchesHeaderFilter(headers, map[string]string{"channel": "sms"}) {
		t.Error("expected matching filter to match")
	}

	// Non-matching filter.
	if MatchesHeaderFilter(headers, map[string]string{"channel": "email"}) {
		t.Error("expected non-matching filter to not match")
	}

	// Nil headers with filter.
	if MatchesHeaderFilter(nil, map[string]string{"channel": "sms"}) {
		t.Error("expected nil headers to not match filter")
	}
}

func TestMessageJSON(t *testing.T) {
	msg := NewMessage("topic-1", []byte(`{"key":"value"}`))
	msg.Priority = PriorityHigh
	msg.Headers = map[string]string{"channel": "sms"}

	data, err := json.Marshal(msg)
	if err != nil {
		t.Fatalf("marshal error: %v", err)
	}

	var parsed map[string]interface{}
	if err := json.Unmarshal(data, &parsed); err != nil {
		t.Fatalf("unmarshal error: %v", err)
	}

	if parsed["status"] != "pending" {
		t.Errorf("expected status 'pending' in JSON, got %v", parsed["status"])
	}
	if parsed["topic"] != "topic-1" {
		t.Errorf("expected topic 'topic-1' in JSON, got %v", parsed["topic"])
	}
	// Priority should be serialized as number.
	if parsed["priority"] != float64(10) {
		t.Errorf("expected priority 10 in JSON, got %v", parsed["priority"])
	}
}
