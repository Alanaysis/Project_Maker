// Package tests: semantics_test.go verifies exactly-once guarantees under
// various real-world scenarios including transactional operations, idempotent
// transfers, and edge cases.
package tests

import (
	"errors"
	"fmt"
	"sync"
	"sync/atomic"
	"testing"

	"github.com/anthropic/exactly-once/internal/message"
	"github.com/anthropic/exactly-once/internal/processor"
	"github.com/anthropic/exactly-once/internal/transaction"
)

// TestExactlyOnce_IdempotentTransfer simulates a money transfer scenario.
// The same transfer request is delivered multiple times (at-least-once),
// but the side effect (balance change) must occur exactly once.
func TestExactlyOnce_IdempotentTransfer(t *testing.T) {
	var balance int64 = 1000

	p := processor.New()
	p.Register("transfer", func(msg *message.Message) ([]byte, error) {
		// Idempotent: the handler checks whether this transfer has already
		// been applied by using a deterministic operation.
		// In a real system this would use an idempotency key lookup in the DB.
		newBalance := atomic.AddInt64(&balance, -100)
		return []byte(fmt.Sprintf("balance=%d", newBalance)), nil
	})

	// Simulate 10 deliveries of the same logical transfer
	for i := 0; i < 10; i++ {
		msg := message.New(fmt.Sprintf("delivery-%d", i), []byte(`{"to":"B","amount":100}`))
		msg.IdempotencyKey = "transfer-abc-123" // Same logical operation
		err := p.Process(msg, "transfer")
		if err != nil {
			t.Fatalf("delivery %d unexpected error: %v", i, err)
		}
	}

	// The balance should only be deducted once (-100), not 10 times
	if balance != 900 {
		t.Errorf("expected balance 900, got %d (exactly-once violated!)", balance)
	}

	stats := p.StatsSnapshot()
	if stats.Succeeded != 1 {
		t.Errorf("expected 1 succeeded, got %d", stats.Succeeded)
	}
	if stats.Duplicated != 9 {
		t.Errorf("expected 9 duplicated, got %d", stats.Duplicated)
	}
}

// TestExactlyOnce_TransactionAtomicity uses a Transaction to group multiple
// operations. If one fails, all are rolled back, ensuring no partial effects.
func TestExactlyOnce_TransactionAtomicity(t *testing.T) {
	var dbUpdated, emailSent bool

	txn := transaction.New("order-txn")

	txn.Add(&transaction.Operation{
		Name: "update-inventory",
		Execute: func() (interface{}, error) {
			dbUpdated = true
			return "inventory-updated", nil
		},
		Undo: func() error {
			dbUpdated = false
			return nil
		},
	})
	txn.Add(&transaction.Operation{
		Name: "charge-payment",
		Execute: func() (interface{}, error) {
			return nil, errors.New("payment gateway timeout")
		},
		Undo: func() error {
			return nil
		},
	})
	txn.Add(&transaction.Operation{
		Name: "send-confirmation",
		Execute: func() (interface{}, error) {
			emailSent = true
			return "email-sent", nil
		},
		Undo: func() error {
			emailSent = false
			return nil
		},
	})

	err := txn.Execute()
	if err == nil {
		t.Fatal("expected error from transaction")
	}

	// Transaction should be aborted
	if txn.State != transaction.StateAborted {
		t.Errorf("expected ABORTED, got %s", txn.State)
	}

	// Inventory update should have been rolled back
	if dbUpdated {
		t.Error("expected inventory update to be rolled back")
	}
	// Email should never have been sent (operation 2 failed before 3 ran)
	if emailSent {
		t.Error("expected email to not be sent (payment failed first)")
	}
}

// TestExactlyOnce_TransactionCommit verifies that a successful transaction
// commits all operations atomically.
func TestExactlyOnce_TransactionCommit(t *testing.T) {
	var (
		inventoryReserved bool
		paymentCharged    bool
		receiptGenerated  bool
	)

	txn := transaction.New("checkout-txn")

	txn.Add(&transaction.Operation{
		Name: "reserve-inventory",
		Execute: func() (interface{}, error) {
			inventoryReserved = true
			return "reserved", nil
		},
	})
	txn.Add(&transaction.Operation{
		Name: "charge-payment",
		Execute: func() (interface{}, error) {
			paymentCharged = true
			return "charged", nil
		},
	})
	txn.Add(&transaction.Operation{
		Name: "generate-receipt",
		Execute: func() (interface{}, error) {
			receiptGenerated = true
			return "receipt-id-001", nil
		},
	})

	err := txn.Execute()
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	if txn.State != transaction.StateCommitted {
		t.Errorf("expected COMMITTED, got %s", txn.State)
	}
	if !inventoryReserved {
		t.Error("expected inventory to be reserved")
	}
	if !paymentCharged {
		t.Error("expected payment to be charged")
	}
	if !receiptGenerated {
		t.Error("expected receipt to be generated")
	}

	// Verify results are accessible
	result, found := txn.GetResult("generate-receipt")
	if !found || result != "receipt-id-001" {
		t.Errorf("expected receipt result 'receipt-id-001', got %v", result)
	}
}

// TestExactlyOnce_TransactionalProcessing combines the Processor with a
// Transaction inside a handler to achieve atomic multi-step processing.
func TestExactlyOnce_TransactionalProcessing(t *testing.T) {
	p := processor.New()
	var sideEffect int32

	p.Register("order", func(msg *message.Message) ([]byte, error) {
		txn := transaction.New(msg.ID)

		txn.Add(&transaction.Operation{
			Name: "validate",
			Execute: func() (interface{}, error) {
				return "valid", nil
			},
		})
		txn.Add(&transaction.Operation{
			Name: "execute",
			Execute: func() (interface{}, error) {
				atomic.AddInt32(&sideEffect, 1)
				return "executed", nil
			},
		})

		if err := txn.Execute(); err != nil {
			return nil, err
		}
		return []byte("order-complete"), nil
	})

	// Process the same order 5 times
	for i := 0; i < 5; i++ {
		msg := message.New(fmt.Sprintf("retry-%d", i), []byte("order-data"))
		msg.IdempotencyKey = "order-xyz"
		p.Process(msg, "order")
	}

	// Side effect should only happen once
	if count := atomic.LoadInt32(&sideEffect); count != 1 {
		t.Errorf("expected exactly 1 side effect, got %d", count)
	}
}

// TestExactlyOnce_DeadLetterScenario simulates a message that permanently
// fails all retries and verifies the final state is consistent across
// message, dedup, and tracker.
func TestExactlyOnce_DeadLetterScenario(t *testing.T) {
	p := processor.New()
	var onFailureCalled int32

	p.Register("broken", func(msg *message.Message) ([]byte, error) {
		return nil, errors.New("unrecoverable error")
	})

	msg := message.New("dlq-001", []byte("payload"))
	msg.MaxRetries = 2

	err := p.Process(msg, "broken")
	if err == nil {
		t.Fatal("expected error")
	}

	// Message is in failed state
	if msg.State != message.StateFailed {
		t.Errorf("expected FAILED, got %s", msg.State)
	}
	if msg.RetryCount != 2 {
		t.Errorf("expected 2 retries, got %d", msg.RetryCount)
	}

	// Dedup marks it as failed
	d := p.Deduplicator()
	entry := d.GetEntry(msg.IdempotencyKey)
	if entry == nil || entry.State != "failed" {
		t.Error("expected dedup to mark entry as failed")
	}

	// Tracker has full event history
	tr := p.Tracker()
	events := tr.GetEvents(msg.ID)
	if len(events) < 3 {
		t.Errorf("expected at least 3 tracking events (register + processing attempts), got %d", len(events))
	}

	// Failed messages appear in the failed list
	failed := tr.GetFailedMessages()
	found := false
	for _, id := range failed {
		if id == msg.ID {
			found = true
			break
		}
	}
	if !found {
		t.Error("expected message to appear in GetFailedMessages()")
	}

	_ = onFailureCalled // available for future callback tests
}

// TestExactlyOnce_DedupResetForRetry verifies that after a failure, the
// dedup key can be reset to allow reprocessing (manual retry).
func TestExactlyOnce_DedupResetForRetry(t *testing.T) {
	p := processor.New()
	var attempts int32

	p.Register("retriable", func(msg *message.Message) ([]byte, error) {
		n := atomic.AddInt32(&attempts, 1)
		if n == 1 {
			return nil, errors.New("first attempt fails")
		}
		return []byte("success"), nil
	})

	msg1 := message.New("retry-001", []byte("data"))
	msg1.MaxRetries = 0 // No automatic retries
	p.Process(msg1, "retriable")

	// Verify it failed
	if msg1.State != message.StateFailed {
		t.Fatalf("expected FAILED, got %s", msg1.State)
	}

	// Reset the dedup key to allow reprocessing
	p.Deduplicator().Reset(msg1.IdempotencyKey)

	// Simulate manual retry with a new message using the same key
	msg2 := message.New("retry-002", []byte("data"))
	msg2.IdempotencyKey = msg1.IdempotencyKey
	msg2.MaxRetries = 0
	err := p.Process(msg2, "retriable")
	if err != nil {
		t.Fatalf("retry should succeed: %v", err)
	}

	if msg2.State != message.StateCompleted {
		t.Errorf("expected COMPLETED after retry, got %s", msg2.State)
	}
	if attempts := atomic.LoadInt32(&attempts); attempts != 2 {
		t.Errorf("expected 2 total attempts, got %d", attempts)
	}
}

// TestExactlyOnce_ProcessMultipleHandlers verifies that the processor can
// handle messages routed to different registered handlers.
func TestExactlyOnce_ProcessMultipleHandlers(t *testing.T) {
	p := processor.New()

	p.Register("validate", func(msg *message.Message) ([]byte, error) {
		return []byte("valid"), nil
	})
	p.Register("enrich", func(msg *message.Message) ([]byte, error) {
		return []byte(fmt.Sprintf("enriched:%s", msg.Payload)), nil
	})
	p.Register("persist", func(msg *message.Message) ([]byte, error) {
		return []byte("persisted"), nil
	})

	handlers := []string{"validate", "enrich", "persist"}
	for i, h := range handlers {
		msg := message.New(fmt.Sprintf("multi-%d", i), []byte("data"))
		err := p.Process(msg, h)
		if err != nil {
			t.Errorf("handler '%s' failed: %v", h, err)
		}
		if msg.State != message.StateCompleted {
			t.Errorf("handler '%s': expected COMPLETED, got %s", h, msg.State)
		}
	}

	stats := p.StatsSnapshot()
	if stats.Succeeded != 3 {
		t.Errorf("expected 3 succeeded, got %d", stats.Succeeded)
	}
}

// TestExactlyOnce_ConcurrentDuplicateDelivery simulates concurrent delivery
// of the same message (same idempotency key). Only one should succeed.
func TestExactlyOnce_ConcurrentDuplicateDelivery(t *testing.T) {
	p := processor.New()
	var sideEffects int32

	p.Register("deposit", func(msg *message.Message) ([]byte, error) {
		atomic.AddInt32(&sideEffects, 1)
		return []byte("deposited"), nil
	})

	const concurrency = 50
	var wg sync.WaitGroup
	states := make([]message.State, concurrency)
	errs := make([]error, concurrency)

	for i := 0; i < concurrency; i++ {
		wg.Add(1)
		go func(idx int) {
			defer wg.Done()
			msg := message.New(fmt.Sprintf("dup-%d", idx), []byte("deposit-$500"))
			msg.IdempotencyKey = "deposit-order-789" // All same key
			err := p.Process(msg, "deposit")
			states[idx] = msg.State
			errs[idx] = err
		}(i)
	}

	wg.Wait()

	// Count outcomes: completed, duplicate, or in-progress (returned error)
	var completedCount, duplicateCount, inProgressCount int
	for i, state := range states {
		switch {
		case state == message.StateCompleted:
			completedCount++
		case state == message.StateDuplicate:
			duplicateCount++
		case errs[i] != nil:
			// "already being processed" is expected in concurrent scenarios
			inProgressCount++
		default:
			inProgressCount++
		}
	}

	// Exactly one should complete, rest should be duplicates or in-progress errors
	if completedCount != 1 {
		t.Errorf("expected exactly 1 completed, got %d", completedCount)
	}
	if completedCount+duplicateCount+inProgressCount != concurrency {
		t.Errorf("expected total %d, got %d", concurrency, completedCount+duplicateCount+inProgressCount)
	}

	// Side effect should occur exactly once
	if count := atomic.LoadInt32(&sideEffects); count != 1 {
		t.Errorf("expected exactly 1 side effect, got %d", count)
	}
}

// TestTransactionManager_Lifecycle tests the transaction manager's ability
// to track committed, aborted, and active transactions.
func TestTransactionManager_Lifecycle(t *testing.T) {
	mgr := transaction.NewManager()

	// Committed transaction
	txn1 := mgr.Begin("txn-ok")
	txn1.Add(&transaction.Operation{
		Name:     "op1",
		Execute:  func() (interface{}, error) { return "ok", nil },
	})
	txn1.Execute()

	// Aborted transaction
	txn2 := mgr.Begin("txn-fail")
	txn2.Add(&transaction.Operation{
		Name:     "op1",
		Execute:  func() (interface{}, error) { return nil, errors.New("fail") },
	})
	txn2.Execute()

	// Active (not yet executed)
	mgr.Begin("txn-pending")

	if mgr.CommittedCount() != 1 {
		t.Errorf("expected 1 committed, got %d", mgr.CommittedCount())
	}
	if mgr.AbortedCount() != 1 {
		t.Errorf("expected 1 aborted, got %d", mgr.AbortedCount())
	}
	if mgr.Size() != 3 {
		t.Errorf("expected 3 total, got %d", mgr.Size())
	}

	// Retrieve by ID
	txn := mgr.Get("txn-ok")
	if txn == nil || txn.State != transaction.StateCommitted {
		t.Error("expected to retrieve committed transaction")
	}
}

// TestExactlyOnce_HandlerPanicRecovery verifies that a handler panic does
// not leave the system in an inconsistent state.
func TestExactlyOnce_HandlerPanicRecovery(t *testing.T) {
	p := processor.New()

	p.Register("panicky", func(msg *message.Message) ([]byte, error) {
		panic("handler panic!")
	})

	msg := message.New("panic-001", []byte("data"))
	msg.MaxRetries = 0

	// The processor should propagate the panic (this is expected behavior
	// for unrecoverable errors). The caller is responsible for recovery.
	defer func() {
		r := recover()
		if r == nil {
			t.Error("expected panic to propagate")
		}
		// After a panic, the message should still be trackable
		tr := p.Tracker()
		record := tr.GetRecord(msg.ID)
		if record == nil {
			t.Error("expected tracker to have recorded the message before panic")
		}
	}()

	p.Process(msg, "panicky")
}

// TestExactlyOnce_EmptyPayload verifies that messages with empty payloads
// are handled correctly.
func TestExactlyOnce_EmptyPayload(t *testing.T) {
	p := processor.New()

	p.Register("echo", func(msg *message.Message) ([]byte, error) {
		return msg.Payload, nil
	})

	msg := message.New("empty-001", nil)
	err := p.Process(msg, "echo")
	if err != nil {
		t.Fatalf("unexpected error with nil payload: %v", err)
	}
	if msg.State != message.StateCompleted {
		t.Errorf("expected COMPLETED, got %s", msg.State)
	}
}

// TestExactlyOnce_LargePayload verifies that the pipeline handles large
// payloads without issues.
func TestExactlyOnce_LargePayload(t *testing.T) {
	p := processor.New()

	p.Register("large", func(msg *message.Message) ([]byte, error) {
		return []byte(fmt.Sprintf("size=%d", len(msg.Payload))), nil
	})

	// 1 MB payload
	payload := make([]byte, 1024*1024)
	for i := range payload {
		payload[i] = byte(i % 256)
	}

	msg := message.New("large-001", payload)
	err := p.Process(msg, "large")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if string(msg.Result) != "size=1048576" {
		t.Errorf("unexpected result: %s", string(msg.Result))
	}
}
