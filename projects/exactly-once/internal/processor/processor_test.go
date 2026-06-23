package processor

import (
	"errors"
	"fmt"
	"sync/atomic"
	"testing"

	"github.com/anthropic/exactly-once/internal/message"
)

func TestProcessorBasicProcessing(t *testing.T) {
	p := New()

	p.Register("uppercase", func(msg *message.Message) ([]byte, error) {
		return []byte("PROCESSED"), nil
	})

	msg := message.New("msg-001", []byte("hello"))
	err := p.Process(msg, "uppercase")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	if msg.State != message.StateCompleted {
		t.Errorf("expected COMPLETED, got %s", msg.State)
	}
	if string(msg.Result) != "PROCESSED" {
		t.Errorf("expected result 'PROCESSED', got '%s'", string(msg.Result))
	}
}

func TestProcessorDuplicateDetection(t *testing.T) {
	p := New()
	var processCount int32

	p.Register("counting", func(msg *message.Message) ([]byte, error) {
		atomic.AddInt32(&processCount, 1)
		return []byte("done"), nil
	})

	// Process same message twice
	msg1 := message.New("msg-001", []byte("hello"))
	p.Process(msg1, "counting")

	msg2 := message.New("msg-002", []byte("hello"))
	msg2.IdempotencyKey = msg1.IdempotencyKey
	err := p.Process(msg2, "counting")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	if msg2.State != message.StateDuplicate {
		t.Errorf("expected DUPLICATE, got %s", msg2.State)
	}

	// Handler should only have been called once
	if count := atomic.LoadInt32(&processCount); count != 1 {
		t.Errorf("expected handler called 1 time, got %d", count)
	}

	stats := p.StatsSnapshot()
	if stats.Duplicated != 1 {
		t.Errorf("expected 1 duplicated, got %d", stats.Duplicated)
	}
}

func TestProcessorHandlerError(t *testing.T) {
	p := New()

	p.Register("failing", func(msg *message.Message) ([]byte, error) {
		return nil, errors.New("processing failed")
	})

	msg := message.New("msg-001", []byte("hello"))
	msg.MaxRetries = 0 // No retries for this test

	err := p.Process(msg, "failing")
	if err == nil {
		t.Fatal("expected error, got nil")
	}

	if msg.State != message.StateFailed {
		t.Errorf("expected FAILED, got %s", msg.State)
	}
}

func TestProcessorRetry(t *testing.T) {
	p := New()
	var attempts int32

	p.Register("flaky", func(msg *message.Message) ([]byte, error) {
		count := atomic.AddInt32(&attempts, 1)
		if count < 3 {
			return nil, fmt.Errorf("attempt %d failed", count)
		}
		return []byte("success"), nil
	})

	msg := message.New("msg-001", []byte("hello"))
	msg.MaxRetries = 3

	err := p.Process(msg, "flaky")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	if msg.State != message.StateCompleted {
		t.Errorf("expected COMPLETED, got %s", msg.State)
	}

	if msg.RetryCount != 2 {
		t.Errorf("expected 2 retries, got %d", msg.RetryCount)
	}

	stats := p.StatsSnapshot()
	if stats.Retried != 2 {
		t.Errorf("expected 2 retries in stats, got %d", stats.Retried)
	}
}

func TestProcessorRetryExhausted(t *testing.T) {
	p := New()

	p.Register("always-fail", func(msg *message.Message) ([]byte, error) {
		return nil, errors.New("permanent failure")
	})

	msg := message.New("msg-001", []byte("hello"))
	msg.MaxRetries = 2

	err := p.Process(msg, "always-fail")
	if err == nil {
		t.Fatal("expected error, got nil")
	}

	if msg.State != message.StateFailed {
		t.Errorf("expected FAILED, got %s", msg.State)
	}
}

func TestProcessorUnregisteredHandler(t *testing.T) {
	p := New()

	msg := message.New("msg-001", []byte("hello"))
	err := p.Process(msg, "nonexistent")
	if err == nil {
		t.Fatal("expected error for unregistered handler")
	}
}

func TestProcessorCallbacks(t *testing.T) {
	p := New()
	var successCalled, duplicateCalled, failureCalled bool

	p.Register("test", func(msg *message.Message) ([]byte, error) {
		return []byte("ok"), nil
	})

	successMsg := message.New("msg-001", []byte("hello"))

	p2 := New(
		WithOnSuccess(func(msg *message.Message) { successCalled = true }),
		WithOnDuplicate(func(msg *message.Message) { duplicateCalled = true }),
		WithOnFailure(func(msg *message.Message, err error) { failureCalled = true }),
	)
	p2.Register("test", func(msg *message.Message) ([]byte, error) {
		return []byte("ok"), nil
	})

	// Process first message - should trigger success
	p2.Process(successMsg, "test")
	if !successCalled {
		t.Error("expected success callback to be called")
	}

	// Process duplicate - should trigger duplicate callback
	dupMsg := message.New("msg-002", []byte("hello"))
	dupMsg.IdempotencyKey = successMsg.IdempotencyKey
	p2.Process(dupMsg, "test")
	if !duplicateCalled {
		t.Error("expected duplicate callback to be called")
	}

	// Process with failure
	p2.Register("fail", func(msg *message.Message) ([]byte, error) {
		return nil, errors.New("fail")
	})
	failMsg := message.New("msg-003", []byte("hello"))
	failMsg.MaxRetries = 0
	p2.Process(failMsg, "fail")
	if !failureCalled {
		t.Error("expected failure callback to be called")
	}
}

func TestProcessorProcessWithHandler(t *testing.T) {
	p := New()

	msg := message.New("msg-001", []byte("hello"))
	err := p.ProcessWithHandler(msg, func(msg *message.Message) ([]byte, error) {
		return []byte("inline-result"), nil
	})

	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if string(msg.Result) != "inline-result" {
		t.Errorf("expected 'inline-result', got '%s'", string(msg.Result))
	}
}

func TestProcessorStats(t *testing.T) {
	p := New()

	p.Register("ok", func(msg *message.Message) ([]byte, error) {
		return []byte("ok"), nil
	})
	p.Register("fail", func(msg *message.Message) ([]byte, error) {
		return nil, errors.New("fail")
	})

	// Process 3 successful messages
	for i := 0; i < 3; i++ {
		msg := message.New(fmt.Sprintf("msg-%d", i), []byte("data"))
		p.Process(msg, "ok")
	}

	// Process 1 failed message
	msg := message.New("msg-fail", []byte("data"))
	msg.MaxRetries = 0
	p.Process(msg, "fail")

	stats := p.StatsSnapshot()
	if stats.Succeeded != 3 {
		t.Errorf("expected 3 succeeded, got %d", stats.Succeeded)
	}
	if stats.Failed != 1 {
		t.Errorf("expected 1 failed, got %d", stats.Failed)
	}
}

func TestProcessorAverageProcessingTime(t *testing.T) {
	p := New()

	p.Register("ok", func(msg *message.Message) ([]byte, error) {
		return []byte("ok"), nil
	})

	msg := message.New("msg-001", []byte("data"))
	p.Process(msg, "ok")

	avg := p.AverageProcessingTime()
	if avg <= 0 {
		t.Error("expected positive average processing time")
	}
}

func TestProcessorGetHandler(t *testing.T) {
	p := New()

	p.Register("test", func(msg *message.Message) ([]byte, error) {
		return nil, nil
	})

	handler := p.GetHandler("test")
	if handler == nil {
		t.Error("expected non-nil handler")
	}

	handler = p.GetHandler("nonexistent")
	if handler != nil {
		t.Error("expected nil for unregistered handler")
	}
}

func TestProcessorIdempotency(t *testing.T) {
	// This test demonstrates the core exactly-once guarantee:
	// even with at-least-once delivery, the effect is exactly once.
	p := New()
	var sideEffectCount int32

	p.Register("transfer", func(msg *message.Message) ([]byte, error) {
		// This simulates a side effect (e.g., bank transfer)
		// In a real system, this would be wrapped in a transaction
		atomic.AddInt32(&sideEffectCount, 1)
		return []byte("transferred"), nil
	})

	// Simulate at-least-once delivery: same message delivered 5 times
	for i := 0; i < 5; i++ {
		msg := message.New(fmt.Sprintf("delivery-%d", i), []byte("transfer-$100"))
		// All have the same idempotency key (same logical operation)
		msg.IdempotencyKey = "transfer-order-123"
		p.Process(msg, "transfer")
	}

	// Side effect should only occur once
	if count := atomic.LoadInt32(&sideEffectCount); count != 1 {
		t.Errorf("expected exactly 1 side effect, got %d (exactly-once violated!)", count)
	}
}
