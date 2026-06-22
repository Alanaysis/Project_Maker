package protocol

import (
	"encoding/json"
	"testing"
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

func TestMessageStatusString(t *testing.T) {
	tests := []struct {
		status MessageStatus
		want   string
	}{
		{StatusPending, "pending"},
		{StatusDelivered, "delivered"},
		{StatusAcknowledged, "acknowledged"},
		{MessageStatus(99), "unknown"},
	}

	for _, tc := range tests {
		if got := tc.status.String(); got != tc.want {
			t.Errorf("Status(%d).String() = %q, want %q", tc.status, got, tc.want)
		}
	}
}

func TestMessageJSON(t *testing.T) {
	msg := NewMessage("topic-1", []byte(`{"key":"value"}`))

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
}
