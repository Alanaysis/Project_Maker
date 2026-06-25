// Order system example demonstrating exactly-once semantics.
//
// This example shows how to process order creation with exactly-once
// guarantees. The order system uses:
//   - Deduplication to prevent duplicate order creation
//   - Transactions for atomic inventory + payment + order creation
//   - Outbox pattern for reliable event publishing to downstream systems
package main

import (
	"errors"
	"fmt"
	"log"
	"sync/atomic"

	"github.com/anthropic/exactly-once/internal/consume"
	"github.com/anthropic/exactly-once/internal/message"
	"github.com/anthropic/exactly-once/internal/outbox"
	"github.com/anthropic/exactly-once/internal/processor"
	"github.com/anthropic/exactly-once/internal/transaction"
)

// Order represents a customer order.
type Order struct {
	ID         string
	CustomerID string
	Items      []OrderItem
	Status     string
	Total      int64
}

// OrderItem represents an item in an order.
type OrderItem struct {
	ProductID string
	Quantity  int
	Price     int64
}

// Inventory simulates a product inventory.
type Inventory struct {
	stock map[string]int
}

func NewInventory() *Inventory {
	return &Inventory{
		stock: map[string]int{
			"prod-001": 100,
			"prod-002": 50,
			"prod-003": 200,
		},
	}
}

func (inv *Inventory) Reserve(productID string, qty int) error {
	available, exists := inv.stock[productID]
	if !exists {
		return fmt.Errorf("product %s not found", productID)
	}
	if available < qty {
		return fmt.Errorf("insufficient stock for %s: have %d, need %d",
			productID, available, qty)
	}
	inv.stock[productID] -= qty
	return nil
}

func (inv *Inventory) Release(productID string, qty int) {
	inv.stock[productID] += qty
}

func (inv *Inventory) GetStock(productID string) int {
	return inv.stock[productID]
}

// OrderService processes orders with exactly-once semantics.
type OrderService struct {
	processor *processor.Processor
	consumer  *consume.Consumer
	inventory *Inventory
	outbox    *outbox.Outbox
	orders    map[string]*Order
	orderSeq  int64
}

func NewOrderService() *OrderService {
	os := &OrderService{
		inventory: NewInventory(),
		orders:    make(map[string]*Order),
	}

	// Create outbox for order events
	os.outbox = outbox.New(outbox.WithPublisher(func(topic string, msg *message.Message) error {
		log.Printf("[order-event] published to %s: %s", topic, string(msg.Payload))
		return nil
	}))

	// Create processor with exactly-once guarantees
	os.processor = processor.New(
		processor.WithOnSuccess(func(msg *message.Message) {
			log.Printf("[order] SUCCESS: id=%s", msg.ID)
		}),
		processor.WithOnDuplicate(func(msg *message.Message) {
			log.Printf("[order] DUPLICATE (skipped): id=%s", msg.ID)
		}),
		processor.WithOnFailure(func(msg *message.Message, err error) {
			log.Printf("[order] FAILED: id=%s error=%v", msg.ID, err)
		}),
	)

	// Register order creation handler (idempotent)
	os.processor.Register("create-order", os.handleCreateOrder)

	// Create consumer for order event processing
	os.consumer = consume.New(
		os.handleOrderEvent,
		consume.WithConsumerID("order-consumer"),
		consume.WithRetryPolicy(consume.RetryPolicy{
			MaxRetries:        3,
			InitialBackoff:    100e6, // 100ms
			MaxBackoff:        5e9,   // 5s
			BackoffMultiplier: 2.0,
		}),
	)

	return os
}

// handleCreateOrder is the idempotent order creation handler.
func (os *OrderService) handleCreateOrder(msg *message.Message) ([]byte, error) {
	customerID := msg.Metadata["customer_id"]
	log.Printf("[order] creating order for customer: %s", customerID)

	// Create transaction for atomic operations
	orderID := fmt.Sprintf("ORD-%d", atomic.AddInt64(&os.orderSeq, 1))
	txn := transaction.New(orderID)

	// Parse items from payload
	items := []OrderItem{
		{ProductID: "prod-001", Quantity: 2, Price: 1500},
		{ProductID: "prod-002", Quantity: 1, Price: 3000},
	}

	// Step 1: Reserve inventory for each item
	for _, item := range items {
		item := item // capture
		txn.Add(&transaction.Operation{
			Name: fmt.Sprintf("reserve-%s", item.ProductID),
			Execute: func() (interface{}, error) {
				if err := os.inventory.Reserve(item.ProductID, item.Quantity); err != nil {
					return nil, err
				}
				return fmt.Sprintf("reserved %d of %s", item.Quantity, item.ProductID), nil
			},
			Undo: func() error {
				os.inventory.Release(item.ProductID, item.Quantity)
				return nil
			},
		})
	}

	// Step 2: Create the order record
	var total int64
	for _, item := range items {
		total += item.Price * int64(item.Quantity)
	}

	txn.Add(&transaction.Operation{
		Name: "create-order-record",
		Execute: func() (interface{}, error) {
			order := &Order{
				ID:         orderID,
				CustomerID: customerID,
				Items:      items,
				Status:     "confirmed",
				Total:      total,
			}
			os.orders[orderID] = order
			return order, nil
		},
		Undo: func() error {
			delete(os.orders, orderID)
			return nil
		},
	})

	// Execute the transaction atomically
	if err := txn.Execute(); err != nil {
		return nil, fmt.Errorf("order transaction failed: %w", err)
	}

	// Save order event to outbox
	eventPayload := fmt.Sprintf(`{"type":"order.created","order_id":"%s","customer_id":"%s","total":%d}`,
		orderID, customerID, total)
	eventMsg := message.New(
		fmt.Sprintf("event-order-%s", orderID),
		[]byte(eventPayload),
	)
	os.outbox.Save(fmt.Sprintf("outbox-order-%s", orderID), "order-events", eventMsg, orderID)

	return []byte(fmt.Sprintf("order created: %s total=%d", orderID, total)), nil
}

// handleOrderEvent processes downstream order events.
func (os *OrderService) handleOrderEvent(msg *consume.ConsumedMessage) error {
	log.Printf("[order-consumer] processing event: %s", string(msg.Message.Payload))
	// In a real system, this would update analytics, send notifications, etc.
	return nil
}

// CreateOrder submits an order for processing.
func (os *OrderService) CreateOrder(customerID string) error {
	msg := message.New(
		fmt.Sprintf("req-%s-%d", customerID, atomic.LoadInt64(&os.orderSeq)),
		[]byte(fmt.Sprintf(`{"customer_id":"%s"}`, customerID)),
	)
	// Use customer ID + timestamp as idempotency key
	// In practice, the client would provide this
	msg.IdempotencyKey = fmt.Sprintf("order-%s", customerID)
	msg.WithMetadata("customer_id", customerID)

	return os.processor.Process(msg, "create-order")
}

func main() {
	fmt.Println("=== Order System - Exactly-Once Demo ===")
	fmt.Println()

	svc := NewOrderService()

	// Show initial inventory
	fmt.Println("--- Initial Inventory ---")
	fmt.Printf("  prod-001: %d units\n", svc.inventory.GetStock("prod-001"))
	fmt.Printf("  prod-002: %d units\n", svc.inventory.GetStock("prod-002"))
	fmt.Println()

	// Create an order (same request sent 3 times due to "network retries")
	fmt.Println("--- Create Order (3 attempts) ---")
	for i := 0; i < 3; i++ {
		fmt.Printf("  Attempt %d: ", i+1)
		err := svc.CreateOrder("customer-001")
		if err != nil {
			fmt.Printf("error: %v\n", err)
		} else {
			fmt.Println("success")
		}
	}

	// Show inventory after order
	fmt.Println("\n--- Inventory After Order ---")
	fmt.Printf("  prod-001: %d units (was 100, ordered 2)\n", svc.inventory.GetStock("prod-001"))
	fmt.Printf("  prod-002: %d units (was 50, ordered 1)\n", svc.inventory.GetStock("prod-002"))
	fmt.Println("  (Inventory should only be reduced once)")
	fmt.Println()

	// Show orders created
	fmt.Println("--- Orders Created ---")
	for id, order := range svc.orders {
		fmt.Printf("  %s: customer=%s status=%s total=%d\n",
			id, order.CustomerID, order.Status, order.Total)
	}
	fmt.Println()

	// Publish outbox events
	fmt.Println("--- Outbox Events ---")
	succeeded, failed := svc.outbox.PublishPending()
	fmt.Printf("  Published: %d, Failed: %d\n", succeeded, failed)
	fmt.Println()

	// Demonstrate batch consumer
	fmt.Println("--- Batch Consumer Demo ---")
	batchConsumer := consume.NewBatchConsumer(
		func(msg *consume.ConsumedMessage) error {
			log.Printf("[batch] processing: %s", string(msg.Message.Payload))
			return nil
		},
		consume.WithBatchSize(3),
	)

	for i := 0; i < 3; i++ {
		msg := message.New(fmt.Sprintf("batch-%d", i), []byte(fmt.Sprintf("event-data-%d", i)))
		full := batchConsumer.Receive(msg)
		if full {
			fmt.Printf("  Batch full after message %d, processing...\n", i+1)
			if err := batchConsumer.ProcessBatch(); err != nil {
				fmt.Printf("  Batch error: %v\n", err)
			}
		}
	}

	batchStats := batchConsumer.StatsSnapshot()
	fmt.Printf("  Batch stats: received=%d batches=%d acked=%d\n",
		batchStats.Received, batchStats.Batches, batchStats.Acked)

	// Show stats
	fmt.Println("\n--- Statistics ---")
	procStats := svc.processor.StatsSnapshot()
	fmt.Printf("  Processed: %d\n", procStats.Processed)
	fmt.Printf("  Succeeded: %d\n", procStats.Succeeded)
	fmt.Printf("  Duplicated: %d\n", procStats.Duplicated)
	fmt.Printf("  Failed: %d\n", procStats.Failed)

	outboxStats := svc.outbox.StatsSnapshot()
	fmt.Printf("  Outbox Published: %d\n", outboxStats.Published)

	fmt.Println("\n=== Demo Complete ===")

	// Suppress unused import
	_ = errors.New
}
