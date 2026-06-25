// Payment system example demonstrating exactly-once semantics.
//
// This example shows how to process payment transactions with exactly-once
// guarantees. Even if the same payment request is submitted multiple times
// (due to network retries, client retries, etc.), the customer is only
// charged once.
//
// Key techniques:
//   - Idempotency keys from payment requests
//   - Deduplication to detect duplicate payment attempts
//   - Transactional processing for atomic balance updates
//   - Outbox pattern for reliable event publishing
package main

import (
	"errors"
	"fmt"
	"log"
	"sync"
	"sync/atomic"

	"github.com/anthropic/exactly-once/internal/message"
	"github.com/anthropic/exactly-once/internal/outbox"
	"github.com/anthropic/exactly-once/internal/processor"
	"github.com/anthropic/exactly-once/internal/transaction"
)

// PaymentRequest represents an incoming payment request.
type PaymentRequest struct {
	OrderID    string `json:"order_id"`
	CustomerID string `json:"customer_id"`
	Amount     int64  `json:"amount"` // cents
	Currency   string `json:"currency"`
}

// PaymentResult represents the outcome of a payment.
type PaymentResult struct {
	TransactionID string `json:"transaction_id"`
	Status        string `json:"status"`
	BalanceAfter  int64  `json:"balance_after"`
}

// Account simulates a customer account with a balance.
type Account struct {
	mu      sync.Mutex
	ID      string
	Balance int64
}

func (a *Account) Debit(amount int64) error {
	a.mu.Lock()
	defer a.mu.Unlock()
	if a.Balance < amount {
		return fmt.Errorf("insufficient funds: have %d, need %d", a.Balance, amount)
	}
	a.Balance -= amount
	return nil
}

func (a *Account) Credit(amount int64) {
	a.mu.Lock()
	defer a.mu.Unlock()
	a.Balance += amount
}

// PaymentService processes payments with exactly-once semantics.
type PaymentService struct {
	processor *processor.Processor
	accounts  map[string]*Account
	outbox    *outbox.Outbox
	txnCounter int64
}

func NewPaymentService() *PaymentService {
	ps := &PaymentService{
		accounts: make(map[string]*Account),
	}

	// Create outbox for reliable event publishing
	ps.outbox = outbox.New(outbox.WithPublisher(func(topic string, msg *message.Message) error {
		log.Printf("[payment-event] published to %s: %s", topic, string(msg.Payload))
		return nil
	}))

	// Create processor with exactly-once guarantees
	ps.processor = processor.New(
		processor.WithOnSuccess(func(msg *message.Message) {
			log.Printf("[payment] SUCCESS: id=%s", msg.ID)
		}),
		processor.WithOnDuplicate(func(msg *message.Message) {
			log.Printf("[payment] DUPLICATE (skipped): id=%s", msg.ID)
		}),
		processor.WithOnFailure(func(msg *message.Message, err error) {
			log.Printf("[payment] FAILED: id=%s error=%v", msg.ID, err)
		}),
	)

	// Register the payment handler (must be idempotent)
	ps.processor.Register("process-payment", ps.handlePayment)

	return ps
}

// handlePayment is the idempotent payment handler.
func (ps *PaymentService) handlePayment(msg *message.Message) ([]byte, error) {
	// In a real system, you would deserialize the PaymentRequest from msg.Payload
	// and use the IdempotencyKey to check if this payment was already processed.

	orderID := msg.Metadata["order_id"]
	customerID := msg.Metadata["customer_id"]
	amountStr := msg.Metadata["amount"]
	var amount int64
	fmt.Sscanf(amountStr, "%d", &amount)

	log.Printf("[payment] processing: order=%s customer=%s amount=%d",
		orderID, customerID, amount)

	// Get or create account
	account := ps.getOrCreateAccount(customerID)

	// Create a transaction for atomic operations
	txnID := fmt.Sprintf("txn-%d", atomic.AddInt64(&ps.txnCounter, 1))
	txn := transaction.New(txnID)

	// Step 1: Validate the payment
	txn.Add(&transaction.Operation{
		Name: "validate",
		Execute: func() (interface{}, error) {
			if amount <= 0 {
				return nil, errors.New("invalid amount")
			}
			if account.Balance < amount {
				return nil, fmt.Errorf("insufficient funds")
			}
			return "valid", nil
		},
	})

	// Step 2: Debit the account
	txn.Add(&transaction.Operation{
		Name: "debit",
		Execute: func() (interface{}, error) {
			if err := account.Debit(amount); err != nil {
				return nil, err
			}
			return account.Balance, nil
		},
		Undo: func() error {
			account.Credit(amount)
			return nil
		},
	})

	// Step 3: Record the payment
	txn.Add(&transaction.Operation{
		Name: "record",
		Execute: func() (interface{}, error) {
			// In a real system: INSERT INTO payments (...)
			return fmt.Sprintf("payment-%s", txnID), nil
		},
	})

	// Execute the transaction atomically
	if err := txn.Execute(); err != nil {
		return nil, fmt.Errorf("payment transaction failed: %w", err)
	}

	// Save payment event to outbox (within the same logical transaction)
	eventMsg := message.New(
		fmt.Sprintf("event-%s", txnID),
		[]byte(fmt.Sprintf(`{"type":"payment.completed","order_id":"%s","amount":%d}`, orderID, amount)),
	)
	ps.outbox.Save(fmt.Sprintf("outbox-%s", txnID), "payment-events", eventMsg, txnID)

	result := PaymentResult{
		TransactionID: txnID,
		Status:        "completed",
		BalanceAfter:  account.Balance,
	}

	return []byte(fmt.Sprintf("%+v", result)), nil
}

func (ps *PaymentService) getOrCreateAccount(id string) *Account {
	if acc, exists := ps.accounts[id]; exists {
		return acc
	}
	acc := &Account{ID: id, Balance: 10000} // Start with $100.00
	ps.accounts[id] = acc
	return acc
}

func (ps *PaymentService) ProcessPayment(req PaymentRequest) error {
	msg := message.New(fmt.Sprintf("pay-%s", req.OrderID), []byte(fmt.Sprintf("%+v", req)))
	// Use order ID as idempotency key - same order = same payment
	msg.IdempotencyKey = fmt.Sprintf("payment-%s", req.OrderID)
	msg.WithMetadata("order_id", req.OrderID)
	msg.WithMetadata("customer_id", req.CustomerID)
	msg.WithMetadata("amount", fmt.Sprintf("%d", req.Amount))

	return ps.processor.Process(msg, "process-payment")
}

func main() {
	fmt.Println("=== Payment System - Exactly-Once Demo ===")
	fmt.Println()

	svc := NewPaymentService()

	// Show initial balance
	fmt.Println("--- Initial State ---")
	account := svc.getOrCreateAccount("customer-001")
	fmt.Printf("  Customer %s balance: $%.2f\n", account.ID, float64(account.Balance)/100)
	fmt.Println()

	// Process a payment
	fmt.Println("--- Process Payment ---")
	req := PaymentRequest{
		OrderID:    "order-001",
		CustomerID: "customer-001",
		Amount:     2500, // $25.00
		Currency:   "USD",
	}

	for i := 0; i < 3; i++ {
		fmt.Printf("  Attempt %d: ", i+1)
		err := svc.ProcessPayment(req)
		if err != nil {
			fmt.Printf("error: %v\n", err)
		} else {
			fmt.Println("success")
		}
	}

	fmt.Printf("\n  Final balance: $%.2f\n", float64(account.Balance)/100)
	fmt.Println("  (Should be $75.00 - only charged once despite 3 attempts)")
	fmt.Println()

	// Publish outbox events
	fmt.Println("--- Outbox Events ---")
	succeeded, failed := svc.outbox.PublishPending()
	fmt.Printf("  Published: %d, Failed: %d\n", succeeded, failed)
	fmt.Println()

	// Show stats
	fmt.Println("--- Statistics ---")
	stats := svc.processor.StatsSnapshot()
	fmt.Printf("  Processed: %d\n", stats.Processed)
	fmt.Printf("  Succeeded: %d\n", stats.Succeeded)
	fmt.Printf("  Duplicated: %d\n", stats.Duplicated)
	fmt.Printf("  Failed: %d\n", stats.Failed)

	outboxStats := svc.outbox.StatsSnapshot()
	fmt.Printf("  Outbox Published: %d\n", outboxStats.Published)

	fmt.Println("\n=== Demo Complete ===")
}
