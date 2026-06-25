package outbox

import (
	"errors"
	"fmt"
	"testing"

	"github.com/anthropic/exactly-once/internal/message"
	"github.com/anthropic/exactly-once/internal/transaction"
)

func TestOutboxSaveAndPublish(t *testing.T) {
	var published []*message.Message
	o := New(WithPublisher(func(topic string, msg *message.Message) error {
		published = append(published, msg)
		return nil
	}))

	msg := message.New("msg-001", []byte("data"))
	entry := o.Save("out-001", "orders", msg, "txn-001")

	if entry.State != EntryStatePending {
		t.Errorf("expected PENDING, got %s", entry.State)
	}

	err := o.Publish("out-001")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	entry = o.GetEntry("out-001")
	if entry.State != EntryStatePublished {
		t.Errorf("expected PUBLISHED, got %s", entry.State)
	}
	if len(published) != 1 {
		t.Errorf("expected 1 published, got %d", len(published))
	}
}

func TestOutboxPublishFailure(t *testing.T) {
	o := New(WithPublisher(func(topic string, msg *message.Message) error {
		return errors.New("broker unavailable")
	}))

	msg := message.New("msg-001", []byte("data"))
	o.Save("out-001", "orders", msg, "txn-001")

	err := o.Publish("out-001")
	if err == nil {
		t.Fatal("expected error, got nil")
	}

	stats := o.StatsSnapshot()
	if stats.Retried != 1 {
		t.Errorf("expected 1 retried, got %d", stats.Retried)
	}
}

func TestOutboxPublishRetryExhausted(t *testing.T) {
	o := New(
		WithPublisher(func(topic string, msg *message.Message) error {
			return errors.New("permanent failure")
		}),
		WithMaxRetries(2),
	)

	msg := message.New("msg-001", []byte("data"))
	o.Save("out-001", "orders", msg, "txn-001")

	// First attempt
	o.Publish("out-001")
	// Second attempt
	o.Publish("out-001")

	entry := o.GetEntry("out-001")
	if entry.State != EntryStateFailed {
		t.Errorf("expected FAILED, got %s", entry.State)
	}

	stats := o.StatsSnapshot()
	if stats.Failed != 1 {
		t.Errorf("expected 1 failed, got %d", stats.Failed)
	}
}

func TestOutboxPublishPending(t *testing.T) {
	publishCount := 0
	o := New(WithPublisher(func(topic string, msg *message.Message) error {
		publishCount++
		return nil
	}))

	for i := 0; i < 5; i++ {
		msg := message.New(fmt.Sprintf("msg-%d", i), []byte("data"))
		o.Save(fmt.Sprintf("out-%d", i), "orders", msg, "txn-001")
	}

	succeeded, failed := o.PublishPending()
	if succeeded != 5 {
		t.Errorf("expected 5 succeeded, got %d", succeeded)
	}
	if failed != 0 {
		t.Errorf("expected 0 failed, got %d", failed)
	}
	if publishCount != 5 {
		t.Errorf("expected 5 publishes, got %d", publishCount)
	}

	stats := o.StatsSnapshot()
	if stats.Pending != 0 {
		t.Errorf("expected 0 pending, got %d", stats.Pending)
	}
}

func TestOutboxGetByState(t *testing.T) {
	o := New(WithPublisher(func(topic string, msg *message.Message) error {
		return nil
	}))

	// Save 3 entries
	for i := 0; i < 3; i++ {
		msg := message.New(fmt.Sprintf("msg-%d", i), []byte("data"))
		o.Save(fmt.Sprintf("out-%d", i), "orders", msg, "txn-001")
	}

	// Publish one
	o.Publish("out-0")

	pending := o.GetPending()
	if len(pending) != 2 {
		t.Errorf("expected 2 pending, got %d", len(pending))
	}

	published := o.GetPublished()
	if len(published) != 1 {
		t.Errorf("expected 1 published, got %d", len(published))
	}

	failed := o.GetFailed()
	if len(failed) != 0 {
		t.Errorf("expected 0 failed, got %d", len(failed))
	}
}

func TestOutboxCallbacks(t *testing.T) {
	var publishCalled, failCalled bool

	o := New(
		WithPublisher(func(topic string, msg *message.Message) error {
			return errors.New("fail")
		}),
		WithMaxRetries(1),
		WithOnPublish(func(entry *OutboxEntry) { publishCalled = true }),
		WithOnFail(func(entry *OutboxEntry, err error) { failCalled = true }),
	)

	msg := message.New("msg-001", []byte("data"))
	o.Save("out-001", "orders", msg, "txn-001")

	o.Publish("out-001") // fails, retries exhausted

	if publishCalled {
		t.Error("publish callback should not be called for failed entry")
	}
	if !failCalled {
		t.Error("fail callback should be called for permanently failed entry")
	}
}

func TestOutboxEntryNotFound(t *testing.T) {
	o := New()

	err := o.Publish("nonexistent")
	if err == nil {
		t.Fatal("expected error for nonexistent entry")
	}

	entry := o.GetEntry("nonexistent")
	if entry != nil {
		t.Error("expected nil for nonexistent entry")
	}
}

func TestOutboxClear(t *testing.T) {
	o := New(WithPublisher(func(topic string, msg *message.Message) error {
		return nil
	}))

	msg := message.New("msg-001", []byte("data"))
	o.Save("out-001", "orders", msg, "txn-001")

	o.Clear()

	if o.Size() != 0 {
		t.Errorf("expected size 0, got %d", o.Size())
	}
	stats := o.StatsSnapshot()
	if stats.Created != 0 {
		t.Errorf("expected 0 created after clear, got %d", stats.Created)
	}
}

func TestOutboxNoPublisher(t *testing.T) {
	o := New()

	msg := message.New("msg-001", []byte("data"))
	o.Save("out-001", "orders", msg, "txn-001")

	err := o.Publish("out-001")
	if err == nil {
		t.Fatal("expected error with no publisher")
	}
}

func TestEntryStateString(t *testing.T) {
	tests := []struct {
		state    EntryState
		expected string
	}{
		{EntryStatePending, "PENDING"},
		{EntryStatePublishing, "PUBLISHING"},
		{EntryStatePublished, "PUBLISHED"},
		{EntryStateFailed, "FAILED"},
		{EntryState(99), "UNKNOWN(99)"},
	}

	for _, tt := range tests {
		if got := tt.state.String(); got != tt.expected {
			t.Errorf("EntryState(%d).String() = %q, want %q", int(tt.state), got, tt.expected)
		}
	}
}

func TestTransactionalOutbox(t *testing.T) {
	published := make(map[string]bool)
	o := New(WithPublisher(func(topic string, msg *message.Message) error {
		published[msg.ID] = true
		return nil
	}))

	to := NewTransactionalOutbox(o)

	// Begin transaction
	txn := to.Begin("txn-001")

	// Add business logic
	txn.Add(&transaction.Operation{
		Name: "update-order",
		Execute: func() (interface{}, error) {
			return "order-updated", nil
		},
	})

	// Save message to outbox
	msg := message.New("msg-001", []byte(`{"status":"confirmed"}`))
	to.SaveMessage("txn-001", "out-001", "order-events", msg)

	// Execute transaction
	err := txn.Execute()
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	// Publish outbox
	succeeded, _ := to.PublishOutbox()
	if succeeded != 1 {
		t.Errorf("expected 1 published, got %d", succeeded)
	}

	if !published["msg-001"] {
		t.Error("expected message to be published")
	}
}
