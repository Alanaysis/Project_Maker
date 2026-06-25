package consume

import (
	"errors"
	"fmt"
	"sync/atomic"
	"testing"
	"time"

	"github.com/anthropic/exactly-once/internal/message"
)

func TestConsumerBasicAck(t *testing.T) {
	c := New(func(msg *ConsumedMessage) error {
		return nil
	})

	msg := message.New("msg-001", []byte("hello"))
	err := c.Process(msg)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	cm := c.GetConsumed("msg-001")
	if cm == nil {
		t.Fatal("expected consumed message to exist")
	}
	if cm.AckStatus != AckStatusAcked {
		t.Errorf("expected ACKED, got %s", cm.AckStatus)
	}

	stats := c.StatsSnapshot()
	if stats.Received != 1 {
		t.Errorf("expected 1 received, got %d", stats.Received)
	}
	if stats.Acked != 1 {
		t.Errorf("expected 1 acked, got %d", stats.Acked)
	}
}

func TestConsumerNack(t *testing.T) {
	c := New(func(msg *ConsumedMessage) error {
		return errors.New("processing failed")
	}, WithRetryPolicy(RetryPolicy{
		MaxRetries:        0,
		InitialBackoff:    time.Millisecond,
		MaxBackoff:        time.Millisecond,
		BackoffMultiplier: 1.0,
	}))

	msg := message.New("msg-001", []byte("hello"))
	err := c.Process(msg)
	if err == nil {
		t.Fatal("expected error, got nil")
	}

	stats := c.StatsSnapshot()
	if stats.Nacked != 1 {
		t.Errorf("expected 1 nacked, got %d", stats.Nacked)
	}
	if stats.Rejected != 1 {
		t.Errorf("expected 1 rejected, got %d", stats.Rejected)
	}
}

func TestConsumerRetryThenSuccess(t *testing.T) {
	var attempts int32
	c := New(func(msg *ConsumedMessage) error {
		count := atomic.AddInt32(&attempts, 1)
		if count < 3 {
			return errors.New("transient error")
		}
		return nil
	}, WithRetryPolicy(RetryPolicy{
		MaxRetries:        3,
		InitialBackoff:    time.Millisecond,
		MaxBackoff:        10 * time.Millisecond,
		BackoffMultiplier: 1.5,
	}))

	msg := message.New("msg-001", []byte("hello"))
	err := c.Process(msg)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	if count := atomic.LoadInt32(&attempts); count != 3 {
		t.Errorf("expected 3 attempts, got %d", count)
	}

	cm := c.GetConsumed("msg-001")
	if cm.AckStatus != AckStatusAcked {
		t.Errorf("expected ACKED, got %s", cm.AckStatus)
	}
}

func TestConsumerRetryExhausted(t *testing.T) {
	c := New(func(msg *ConsumedMessage) error {
		return errors.New("permanent failure")
	}, WithRetryPolicy(RetryPolicy{
		MaxRetries:        2,
		InitialBackoff:    time.Millisecond,
		MaxBackoff:        5 * time.Millisecond,
		BackoffMultiplier: 1.0,
	}))

	msg := message.New("msg-001", []byte("hello"))
	err := c.Process(msg)
	if err == nil {
		t.Fatal("expected error after retries exhausted")
	}

	cm := c.GetConsumed("msg-001")
	if cm.AckStatus != AckStatusRejected {
		t.Errorf("expected REJECTED, got %s", cm.AckStatus)
	}
	if cm.AttemptCount != 3 { // initial + 2 retries
		t.Errorf("expected 3 attempts, got %d", cm.AttemptCount)
	}
}

func TestConsumerCallbacks(t *testing.T) {
	var ackCalled, nackCalled, rejectCalled bool

	c := New(func(msg *ConsumedMessage) error {
		return errors.New("fail")
	},
		WithRetryPolicy(RetryPolicy{
			MaxRetries:        0,
			InitialBackoff:    time.Millisecond,
			MaxBackoff:        time.Millisecond,
			BackoffMultiplier: 1.0,
		}),
		WithOnAck(func(msg *ConsumedMessage) { ackCalled = true }),
		WithOnNack(func(msg *ConsumedMessage, err error) { nackCalled = true }),
		WithOnReject(func(msg *ConsumedMessage) { rejectCalled = true }),
	)

	msg := message.New("msg-001", []byte("hello"))
	c.Process(msg)

	if !nackCalled {
		t.Error("expected nack callback to be called")
	}
	if !rejectCalled {
		t.Error("expected reject callback to be called")
	}
	if ackCalled {
		t.Error("ack callback should not be called for failed message")
	}
}

func TestConsumerGetByStatus(t *testing.T) {
	c := New(func(msg *ConsumedMessage) error {
		return nil
	})

	// Process 3 messages
	for i := 0; i < 3; i++ {
		msg := message.New(msgID(i), []byte("data"))
		c.Process(msg)
	}

	acked := c.GetAcked()
	if len(acked) != 3 {
		t.Errorf("expected 3 acked, got %d", len(acked))
	}

	pending := c.GetPending()
	if len(pending) != 0 {
		t.Errorf("expected 0 pending, got %d", len(pending))
	}
}

func TestConsumerManualAck(t *testing.T) {
	c := New(func(msg *ConsumedMessage) error {
		return nil
	})

	msg := message.New("msg-001", []byte("hello"))
	cm := c.Receive(msg)

	if cm.AckStatus != AckStatusPending {
		t.Errorf("expected PENDING, got %s", cm.AckStatus)
	}

	c.Ack(cm)
	if cm.AckStatus != AckStatusAcked {
		t.Errorf("expected ACKED, got %s", cm.AckStatus)
	}
}

func TestRetryPolicyBackoff(t *testing.T) {
	policy := RetryPolicy{
		InitialBackoff:    100 * time.Millisecond,
		MaxBackoff:        5 * time.Second,
		BackoffMultiplier: 2.0,
	}

	// Attempt 0: 100ms
	if got := policy.Backoff(0); got != 100*time.Millisecond {
		t.Errorf("expected 100ms, got %v", got)
	}

	// Attempt 1: 200ms
	if got := policy.Backoff(1); got != 200*time.Millisecond {
		t.Errorf("expected 200ms, got %v", got)
	}

	// Attempt 2: 400ms
	if got := policy.Backoff(2); got != 400*time.Millisecond {
		t.Errorf("expected 400ms, got %v", got)
	}

	// Attempt 10: capped at MaxBackoff
	if got := policy.Backoff(10); got != 5*time.Second {
		t.Errorf("expected 5s, got %v", got)
	}
}

func TestAckStatusString(t *testing.T) {
	tests := []struct {
		status   AckStatus
		expected string
	}{
		{AckStatusPending, "PENDING"},
		{AckStatusAcked, "ACKED"},
		{AckStatusNacked, "NACKED"},
		{AckStatusRejected, "REJECTED"},
		{AckStatus(99), "UNKNOWN(99)"},
	}

	for _, tt := range tests {
		if got := tt.status.String(); got != tt.expected {
			t.Errorf("AckStatus(%d).String() = %q, want %q", int(tt.status), got, tt.expected)
		}
	}
}

func TestConsumerAverageProcessTime(t *testing.T) {
	c := New(func(msg *ConsumedMessage) error {
		time.Sleep(time.Millisecond)
		return nil
	})

	msg := message.New("msg-001", []byte("hello"))
	c.Process(msg)

	avg := c.AverageProcessTime()
	if avg <= 0 {
		t.Error("expected positive average process time")
	}
}

func TestConsumerClear(t *testing.T) {
	c := New(func(msg *ConsumedMessage) error {
		return nil
	})

	msg := message.New("msg-001", []byte("hello"))
	c.Process(msg)

	c.Clear()

	if c.Size() != 0 {
		t.Errorf("expected size 0, got %d", c.Size())
	}
	stats := c.StatsSnapshot()
	if stats.Received != 0 {
		t.Errorf("expected 0 received after clear, got %d", stats.Received)
	}
}

func msgID(i int) string {
	return fmt.Sprintf("msg-%d", i)
}
