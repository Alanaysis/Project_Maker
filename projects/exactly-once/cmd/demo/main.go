// Demo demonstrates exactly-once message processing.
//
// This program simulates a message processing pipeline that guarantees
// exactly-once semantics, even when messages are delivered multiple times
// (at-least-once delivery).
//
// The demo shows:
// 1. Message deduplication - detecting and skipping duplicates
// 2. Idempotent processing - same message produces same result
// 3. Transactional operations - atomic multi-step processing
// 4. State tracking - complete audit trail of message lifecycle
// 5. Retry handling - automatic retry with backoff for failures
package main

import (
	"fmt"
	"log"
	"sync/atomic"
	"time"

	"github.com/anthropic/exactly-once/internal/dedup"
	"github.com/anthropic/exactly-once/internal/message"
	"github.com/anthropic/exactly-once/internal/processor"
	"github.com/anthropic/exactly-once/internal/tracker"
	"github.com/anthropic/exactly-once/internal/transaction"
)

func main() {
	fmt.Println("=== Exactly-Once Semantics Demo ===")
	fmt.Println()

	demoDeduplication()
	demoIdempotentProcessing()
	demoTransactionalProcessing()
	demoRetryHandling()
	demoStateTracking()

	fmt.Println("=== All demos completed ===")
}

// demoDeduplication shows how duplicate messages are detected and skipped.
func demoDeduplication() {
	fmt.Println("--- Demo 1: Message Deduplication ---")

	d := dedup.New(dedup.WithTTL(5 * time.Minute))

	// Simulate a message being delivered 5 times (at-least-once delivery)
	idempotencyKey := "order-create-12345"
	for i := 0; i < 5; i++ {
		result := d.Check(idempotencyKey)
		fmt.Printf("  Delivery %d: %s\n", i+1, result)
	}

	stats := d.StatsSnapshot()
	fmt.Printf("  Stats: %d new, %d duplicates\n\n", stats.NewMessages, stats.Duplicates)
}

// demoIdempotentProcessing shows how the same message produces the same result.
func demoIdempotentProcessing() {
	fmt.Println("--- Demo 2: Idempotent Processing ---")

	p := processor.New()

	// Register an idempotent handler (e.g., setting a value)
	var dbValue string
	p.Register("set-value", func(msg *message.Message) ([]byte, error) {
		// Idempotent: setting the same value multiple times is safe
		dbValue = string(msg.Payload)
		return []byte(fmt.Sprintf("value set to: %s", dbValue)), nil
	})

	// Process the same logical operation 3 times
	for i := 0; i < 3; i++ {
		msg := message.New(fmt.Sprintf("delivery-%d", i), []byte("hello-world"))
		msg.IdempotencyKey = "set-key-1" // Same logical operation

		err := p.Process(msg, "set-value")
		if err != nil {
			log.Printf("Error: %v", err)
			continue
		}
		fmt.Printf("  Attempt %d: state=%s result=%s\n", i+1, msg.State, string(msg.Result))
	}

	fmt.Printf("  DB value: %s (set only once)\n\n", dbValue)
}

// demoTransactionalProcessing shows atomic multi-step operations.
func demoTransactionalProcessing() {
	fmt.Println("--- Demo 3: Transactional Processing ---")

	// Simulate a bank transfer as a transaction
	balanceA, balanceB := 1000, 500
	fmt.Printf("  Initial: Account A=%d, Account B=%d\n", balanceA, balanceB)

	txn := transaction.New("transfer-001")

	// Step 1: Debit Account A
	transferAmount := 100
	txn.Add(&transaction.Operation{
		Name: "debit-a",
		Execute: func() (interface{}, error) {
			if balanceA < transferAmount {
				return nil, fmt.Errorf("insufficient funds")
			}
			balanceA -= transferAmount
			return balanceA, nil
		},
		Undo: func() error {
			balanceA += transferAmount
			return nil
		},
	})

	// Step 2: Credit Account B
	txn.Add(&transaction.Operation{
		Name: "credit-b",
		Execute: func() (interface{}, error) {
			balanceB += transferAmount
			return balanceB, nil
		},
		Undo: func() error {
			balanceB -= transferAmount
			return nil
		},
	})

	if err := txn.Execute(); err != nil {
		log.Printf("Transaction failed: %v", err)
	} else {
		fmt.Printf("  After transfer: Account A=%d, Account B=%d\n", balanceA, balanceB)
		fmt.Printf("  Transaction state: %s, duration: %v\n", txn.State, txn.Duration())
	}

	// Now simulate a failed transaction (should roll back)
	fmt.Println("\n  Simulating failed transfer (insufficient funds)...")
	txn2 := transaction.New("transfer-002")
	txn2.Add(&transaction.Operation{
		Name: "debit-a",
		Execute: func() (interface{}, error) {
			return nil, fmt.Errorf("insufficient funds: need 9999, have %d", balanceA)
		},
		Undo: func() error {
			return nil
		},
	})

	if err := txn2.Execute(); err != nil {
		fmt.Printf("  Transaction failed (expected): %v\n", err)
		fmt.Printf("  Balances unchanged: A=%d, B=%d\n\n", balanceA, balanceB)
	}
}

// demoRetryHandling shows automatic retry with eventual success.
func demoRetryHandling() {
	fmt.Println("--- Demo 4: Retry Handling ---")

	p := processor.New()
	var attempts int32

	p.Register("flaky-service", func(msg *message.Message) ([]byte, error) {
		count := atomic.AddInt32(&attempts, 1)
		if count <= 2 {
			return nil, fmt.Errorf("service unavailable (attempt %d)", count)
		}
		return []byte("success"), nil
	})

	msg := message.New("msg-retry-001", []byte("process-me"))
	msg.MaxRetries = 3

	fmt.Printf("  Processing message with flaky handler (max retries: %d)...\n", msg.MaxRetries)
	err := p.Process(msg, "flaky-service")
	if err != nil {
		fmt.Printf("  Failed: %v\n", err)
	} else {
		fmt.Printf("  Succeeded after %d retries\n", msg.RetryCount)
	}

	stats := p.StatsSnapshot()
	fmt.Printf("  Stats: %d processed, %d succeeded, %d retried\n\n",
		stats.Processed, stats.Succeeded, stats.Retried)
}

// demoStateTracking shows the complete message lifecycle audit trail.
func demoStateTracking() {
	fmt.Println("--- Demo 5: State Tracking ---")

	tr := tracker.New()
	msg := message.New("msg-track-001", []byte("track-me"))

	// Track the full lifecycle
	tr.Track(msg)
	fmt.Printf("  Tracked: state=%s\n", msg.State)

	msg.MarkProcessing()
	tr.Update(msg)
	fmt.Printf("  Processing: state=%s\n", msg.State)

	msg.MarkCompleted([]byte("result-data"))
	tr.Update(msg)
	fmt.Printf("  Completed: state=%s\n", msg.State)

	// Show the audit trail
	events := tr.GetEvents("msg-track-001")
	fmt.Printf("  Audit trail (%d events):\n", len(events))
	for i, event := range events {
		fmt.Printf("    %d. [%s] %s -> %s: %s\n",
			i+1, event.Timestamp.Format("15:04:05.000"),
			event.FromState, event.ToState, event.Message)
	}

	// Show statistics
	stats := tr.StatsSnapshot()
	fmt.Printf("  Tracker stats: %d tracked, %d completed, %d failed\n\n",
		stats.TotalTracked, stats.Completed, stats.Failed)
}
