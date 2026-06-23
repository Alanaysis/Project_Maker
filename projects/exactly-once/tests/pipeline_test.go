// Package tests provides integration tests for the exactly-once pipeline.
//
// These tests verify that all components (message, dedup, processor, tracker,
// transaction) work together correctly to achieve exactly-once semantics.
// Unlike the per-package unit tests, these tests exercise the full flow
// from message creation through deduplication, processing, and tracking.
package tests

import (
	"errors"
	"fmt"
	"strings"
	"sync"
	"sync/atomic"
	"testing"

	"github.com/anthropic/exactly-once/internal/dedup"
	"github.com/anthropic/exactly-once/internal/message"
	"github.com/anthropic/exactly-once/internal/processor"
)

// TestFullPipeline_BasicFlow tests the complete message processing pipeline:
// message -> dedup -> processor -> tracker -> completion.
func TestFullPipeline_BasicFlow(t *testing.T) {
	p := processor.New()

	p.Register("process-order", func(msg *message.Message) ([]byte, error) {
		return []byte(fmt.Sprintf("order-processed:%s", msg.Payload)), nil
	})

	msg := message.New("order-001", []byte("item-A"))
	err := p.Process(msg, "process-order")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	// Verify message state
	if msg.State != message.StateCompleted {
		t.Errorf("expected COMPLETED, got %s", msg.State)
	}
	if string(msg.Result) != "order-processed:item-A" {
		t.Errorf("unexpected result: %s", string(msg.Result))
	}

	// Verify dedup recorded completion
	d := p.Deduplicator()
	if !d.IsSeen(msg.IdempotencyKey) {
		t.Error("expected idempotency key to be seen in deduplicator")
	}
	entry := d.GetEntry(msg.IdempotencyKey)
	if entry == nil || entry.State != "completed" {
		t.Errorf("expected dedup entry state 'completed', got %v", entry)
	}

	// Verify tracker recorded the message
	tr := p.Tracker()
	record := tr.GetRecord(msg.ID)
	if record == nil {
		t.Fatal("expected tracker record to exist")
	}
	if record.CurrentState != message.StateCompleted {
		t.Errorf("expected tracker state COMPLETED, got %s", record.CurrentState)
	}
	if len(record.Events) < 2 {
		t.Errorf("expected at least 2 tracking events, got %d", len(record.Events))
	}

	// Verify stats
	stats := p.StatsSnapshot()
	if stats.Succeeded != 1 {
		t.Errorf("expected 1 succeeded, got %d", stats.Succeeded)
	}
}

// TestFullPipeline_DuplicateDetection verifies that when the same logical
// operation is submitted twice (same idempotency key), the handler is only
// called once and the second submission is marked as duplicate.
func TestFullPipeline_DuplicateDetection(t *testing.T) {
	p := processor.New()
	var handlerCalls int32

	p.Register("charge", func(msg *message.Message) ([]byte, error) {
		atomic.AddInt32(&handlerCalls, 1)
		return []byte("charged"), nil
	})

	// First submission
	msg1 := message.New("charge-001", []byte(`{"amount":100}`))
	err := p.Process(msg1, "charge")
	if err != nil {
		t.Fatalf("first submission failed: %v", err)
	}
	if msg1.State != message.StateCompleted {
		t.Fatalf("expected first message COMPLETED, got %s", msg1.State)
	}

	// Second submission with the same idempotency key (simulating re-delivery)
	msg2 := message.New("charge-002", []byte(`{"amount":100}`))
	msg2.IdempotencyKey = msg1.IdempotencyKey
	err = p.Process(msg2, "charge")
	if err != nil {
		t.Fatalf("second submission failed: %v", err)
	}
	if msg2.State != message.StateDuplicate {
		t.Errorf("expected second message DUPLICATE, got %s", msg2.State)
	}

	// Handler must have been called exactly once
	if count := atomic.LoadInt32(&handlerCalls); count != 1 {
		t.Errorf("expected handler called 1 time, got %d", count)
	}

	// Stats should reflect one success and one duplicate
	stats := p.StatsSnapshot()
	if stats.Succeeded != 1 {
		t.Errorf("expected 1 succeeded, got %d", stats.Succeeded)
	}
	if stats.Duplicated != 1 {
		t.Errorf("expected 1 duplicated, got %d", stats.Duplicated)
	}
}

// TestFullPipeline_MultipleRetriesThenSuccess verifies that a flaky handler
// is retried and eventually succeeds, with the final result persisted.
func TestFullPipeline_MultipleRetriesThenSuccess(t *testing.T) {
	p := processor.New()
	var attempts int32

	p.Register("flaky-save", func(msg *message.Message) ([]byte, error) {
		n := atomic.AddInt32(&attempts, 1)
		if n < 3 {
			return nil, fmt.Errorf("transient error on attempt %d", n)
		}
		return []byte("saved"), nil
	})

	msg := message.New("save-001", []byte("data"))
	msg.MaxRetries = 3

	err := p.Process(msg, "flaky-save")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	if msg.State != message.StateCompleted {
		t.Errorf("expected COMPLETED, got %s", msg.State)
	}
	if msg.RetryCount != 2 {
		t.Errorf("expected 2 retries, got %d", msg.RetryCount)
	}

	// Verify dedup has the completed result
	d := p.Deduplicator()
	entry := d.GetEntry(msg.IdempotencyKey)
	if entry == nil || entry.State != "completed" {
		t.Errorf("expected dedup entry state 'completed', got %v", entry)
	}

	// Sending the same key again should return as duplicate with cached result
	msg2 := message.New("save-002", []byte("data"))
	msg2.IdempotencyKey = msg.IdempotencyKey
	err = p.Process(msg2, "flaky-save")
	if err != nil {
		t.Fatalf("re-delivery should not error: %v", err)
	}
	if msg2.State != message.StateDuplicate {
		t.Errorf("expected DUPLICATE on re-delivery, got %s", msg2.State)
	}
}

// TestFullPipeline_RetryExhausted verifies that when all retries fail,
// the message ends in FAILED state and the dedup marks it as failed.
func TestFullPipeline_RetryExhausted(t *testing.T) {
	p := processor.New()

	p.Register("always-fail", func(msg *message.Message) ([]byte, error) {
		return nil, errors.New("permanent failure")
	})

	msg := message.New("fail-001", []byte("data"))
	msg.MaxRetries = 2

	err := p.Process(msg, "always-fail")
	if err == nil {
		t.Fatal("expected error after retries exhausted")
	}
	if !strings.Contains(err.Error(), "failed after") {
		t.Errorf("error should mention retries: %v", err)
	}
	if msg.State != message.StateFailed {
		t.Errorf("expected FAILED, got %s", msg.State)
	}

	// Verify dedup marks it as failed
	d := p.Deduplicator()
	entry := d.GetEntry(msg.IdempotencyKey)
	if entry == nil || entry.State != "failed" {
		t.Errorf("expected dedup entry state 'failed', got %v", entry)
	}

	// Verify tracker has the failure
	tr := p.Tracker()
	record := tr.GetRecord(msg.ID)
	if record == nil {
		t.Fatal("expected tracker record to exist")
	}
	if record.Error == "" {
		t.Error("expected tracker record to have an error message")
	}
}

// TestFullPipeline_Callbacks verifies that success, duplicate, and failure
// callbacks are invoked at the correct times during pipeline processing.
func TestFullPipeline_Callbacks(t *testing.T) {
	var successID, duplicateID, failureID string

	p := processor.New(
		processor.WithOnSuccess(func(msg *message.Message) {
			successID = msg.ID
		}),
		processor.WithOnDuplicate(func(msg *message.Message) {
			duplicateID = msg.ID
		}),
		processor.WithOnFailure(func(msg *message.Message, err error) {
			failureID = msg.ID
		}),
	)

	p.Register("ok", func(msg *message.Message) ([]byte, error) {
		return []byte("ok"), nil
	})
	p.Register("fail", func(msg *message.Message) ([]byte, error) {
		return nil, errors.New("oops")
	})

	// Success callback
	msg1 := message.New("cb-001", []byte("data"))
	p.Process(msg1, "ok")
	if successID != "cb-001" {
		t.Errorf("expected successID 'cb-001', got '%s'", successID)
	}

	// Duplicate callback
	msg2 := message.New("cb-002", []byte("data"))
	msg2.IdempotencyKey = msg1.IdempotencyKey
	p.Process(msg2, "ok")
	if duplicateID != "cb-002" {
		t.Errorf("expected duplicateID 'cb-002', got '%s'", duplicateID)
	}

	// Failure callback
	msg3 := message.New("cb-003", []byte("data"))
	msg3.MaxRetries = 0
	p.Process(msg3, "fail")
	if failureID != "cb-003" {
		t.Errorf("expected failureID 'cb-003', got '%s'", failureID)
	}
}

// TestFullPipeline_ConcurrentProcessing submits many messages concurrently
// and verifies that no data races or inconsistencies occur.
func TestFullPipeline_ConcurrentProcessing(t *testing.T) {
	p := processor.New()

	p.Register("increment", func(msg *message.Message) ([]byte, error) {
		return []byte("ok"), nil
	})

	const numMessages = 100
	var wg sync.WaitGroup
	errs := make(chan error, numMessages)

	for i := 0; i < numMessages; i++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			msg := message.New(fmt.Sprintf("concurrent-%d", id), []byte("payload"))
			if err := p.Process(msg, "increment"); err != nil {
				errs <- fmt.Errorf("msg %d: %w", id, err)
			}
		}(i)
	}

	wg.Wait()
	close(errs)

	for err := range errs {
		t.Errorf("concurrent processing error: %v", err)
	}

	stats := p.StatsSnapshot()
	if stats.Succeeded != numMessages {
		t.Errorf("expected %d succeeded, got %d", numMessages, stats.Succeeded)
	}
	if stats.Failed != 0 {
		t.Errorf("expected 0 failed, got %d", stats.Failed)
	}
}

// TestFullPipeline_DedupAfterTTLExpiration verifies that after the dedup
// TTL expires, the same idempotency key can be processed again.
func TestFullPipeline_DedupAfterTTLExpiration(t *testing.T) {
	d := dedup.New(dedup.WithTTL(1)) // 1 nanosecond TTL for testing
	p := processor.New(processor.WithDeduplicator(d))

	var callCount int32
	p.Register("ttl-test", func(msg *message.Message) ([]byte, error) {
		atomic.AddInt32(&callCount, 1)
		return []byte("ok"), nil
	})

	msg1 := message.New("ttl-001", []byte("data"))
	p.Process(msg1, "ttl-test")

	// After TTL expiration the key should be treated as new
	msg2 := message.New("ttl-002", []byte("data"))
	msg2.IdempotencyKey = msg1.IdempotencyKey
	p.Process(msg2, "ttl-test")

	if count := atomic.LoadInt32(&callCount); count != 2 {
		t.Errorf("expected 2 handler calls after TTL expiration, got %d", count)
	}
}

// TestFullPipeline_InlineHandler verifies ProcessWithHandler for one-off
// inline processing without pre-registering a handler.
func TestFullPipeline_InlineHandler(t *testing.T) {
	p := processor.New()

	msg := message.New("inline-001", []byte("hello"))
	err := p.ProcessWithHandler(msg, func(msg *message.Message) ([]byte, error) {
		return []byte(strings.ToUpper(string(msg.Payload))), nil
	})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	if string(msg.Result) != "HELLO" {
		t.Errorf("expected 'HELLO', got '%s'", string(msg.Result))
	}
	if msg.State != message.StateCompleted {
		t.Errorf("expected COMPLETED, got %s", msg.State)
	}
}

// TestFullPipeline_StatsAccumulation verifies that processor stats are
// correctly accumulated across multiple processing operations.
func TestFullPipeline_StatsAccumulation(t *testing.T) {
	p := processor.New()

	p.Register("ok", func(msg *message.Message) ([]byte, error) {
		return []byte("ok"), nil
	})
	p.Register("fail", func(msg *message.Message) ([]byte, error) {
		return nil, errors.New("fail")
	})

	// 3 successful
	for i := 0; i < 3; i++ {
		msg := message.New(fmt.Sprintf("stat-%d", i), []byte("data"))
		p.Process(msg, "ok")
	}

	// 1 duplicate (re-process stat-0 with same key)
	dup := message.New("stat-dup", []byte("data"))
	dup.IdempotencyKey = message.GenerateIdempotencyKey("stat-0", []byte("data"))
	p.Process(dup, "ok")

	// 1 failure
	failMsg := message.New("stat-fail", []byte("data"))
	failMsg.MaxRetries = 0
	p.Process(failMsg, "fail")

	stats := p.StatsSnapshot()
	if stats.Succeeded != 3 {
		t.Errorf("expected 3 succeeded, got %d", stats.Succeeded)
	}
	if stats.Duplicated != 1 {
		t.Errorf("expected 1 duplicated, got %d", stats.Duplicated)
	}
	if stats.Failed != 1 {
		t.Errorf("expected 1 failed, got %d", stats.Failed)
	}
	if stats.Processed != 4 {
		t.Errorf("expected 4 processed, got %d", stats.Processed)
	}
}

// TestFullPipeline_MessageMetadataPropagation verifies that metadata set on
// the message is accessible within the handler and preserved after processing.
func TestFullPipeline_MessageMetadataPropagation(t *testing.T) {
	p := processor.New()
	var capturedSource string

	p.Register("meta-handler", func(msg *message.Message) ([]byte, error) {
		capturedSource = msg.Metadata["source"]
		return []byte("ok"), nil
	})

	msg := message.New("meta-001", []byte("data")).
		WithMetadata("source", "kafka").
		WithMetadata("topic", "orders")

	p.Process(msg, "meta-handler")

	if capturedSource != "kafka" {
		t.Errorf("expected handler to see metadata source=kafka, got '%s'", capturedSource)
	}
	if msg.Metadata["topic"] != "orders" {
		t.Errorf("expected metadata topic=orders, got '%s'", msg.Metadata["topic"])
	}
}
