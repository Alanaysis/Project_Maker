package examples

import (
	"context"
	"errors"
	"fmt"
	"log"
	"time"

	"github.com/example/distributed-lock/internal/lock"
)

var (
	ErrInsufficientStock = errors.New("insufficient stock")
	ErrLockTimeout       = errors.New("failed to acquire lock")
)

// InventoryManager demonstrates distributed inventory management using locks.
// Prevents overselling by ensuring only one process can modify inventory at a time.
type InventoryManager struct {
	lock      lock.Lock
	inventory map[string]int
}

// NewInventoryManager creates a new inventory manager.
func NewInventoryManager(lock lock.Lock) *InventoryManager {
	return &InventoryManager{
		lock:      lock,
		inventory: make(map[string]int),
	}
}

// SetStock sets the stock for a product.
func (m *InventoryManager) SetStock(productID string, quantity int) {
	m.inventory[productID] = quantity
}

// GetStock returns the current stock for a product.
func (m *InventoryManager) GetStock(productID string) int {
	return m.inventory[productID]
}

// DeductStock atomically deducts stock for a product.
// Uses distributed lock to prevent overselling.
func (m *InventoryManager) DeductStock(ctx context.Context, productID string, quantity int) error {
	// Acquire lock
	acquired, err := m.lock.Acquire(ctx)
	if err != nil {
		return fmt.Errorf("failed to acquire lock: %w", err)
	}
	if !acquired {
		return ErrLockTimeout
	}
	defer m.lock.Release(ctx)

	// Check stock
	currentStock := m.inventory[productID]
	if currentStock < quantity {
		return ErrInsufficientStock
	}

	// Simulate some processing time
	time.Sleep(10 * time.Millisecond)

	// Deduct stock
	m.inventory[productID] = currentStock - quantity

	log.Printf("Deducted %d units of %s, remaining: %d",
		quantity, productID, m.inventory[productID])

	return nil
}

// BatchDeductStock deducts stock for multiple products atomically.
func (m *InventoryManager) BatchDeductStock(ctx context.Context, items map[string]int) error {
	// Acquire lock
	acquired, err := m.lock.Acquire(ctx)
	if err != nil {
		return fmt.Errorf("failed to acquire lock: %w", err)
	}
	if !acquired {
		return ErrLockTimeout
	}
	defer m.lock.Release(ctx)

	// Check all items first
	for productID, quantity := range items {
		if m.inventory[productID] < quantity {
			return fmt.Errorf("insufficient stock for %s: need %d, have %d",
				productID, quantity, m.inventory[productID])
		}
	}

	// Deduct all items
	for productID, quantity := range items {
		m.inventory[productID] -= quantity
		log.Printf("Deducted %d units of %s, remaining: %d",
			quantity, productID, m.inventory[productID])
	}

	return nil
}

// RefundStock adds stock back for a product.
func (m *InventoryManager) RefundStock(ctx context.Context, productID string, quantity int) error {
	// Acquire lock
	acquired, err := m.lock.Acquire(ctx)
	if err != nil {
		return fmt.Errorf("failed to acquire lock: %w", err)
	}
	if !acquired {
		return ErrLockTimeout
	}
	defer m.lock.Release(ctx)

	m.inventory[productID] += quantity
	log.Printf("Refunded %d units of %s, total: %d",
		quantity, productID, m.inventory[productID])

	return nil
}

// ExampleInventory demonstrates inventory management with distributed locks.
func ExampleInventory() {
	fmt.Println("=== Distributed Inventory Management Example ===")
	fmt.Println()
	fmt.Println("Problem: Multiple servers processing orders simultaneously")
	fmt.Println("Risk: Overselling due to race conditions")
	fmt.Println()
	fmt.Println("Solution: Distributed lock ensures atomic stock operations")
	fmt.Println()
	fmt.Println("Without Lock:")
	fmt.Println("  Server A reads stock=1")
	fmt.Println("  Server B reads stock=1")
	fmt.Println("  Server A deducts, stock=0")
	fmt.Println("  Server B deducts, stock=-1 (OVERSOLD!)")
	fmt.Println()
	fmt.Println("With Lock:")
	fmt.Println("  Server A acquires lock")
	fmt.Println("  Server A reads stock=1")
	fmt.Println("  Server A deducts, stock=0")
	fmt.Println("  Server A releases lock")
	fmt.Println("  Server B acquires lock")
	fmt.Println("  Server B reads stock=0")
	fmt.Println("  Server B rejects order (OUT OF STOCK)")
	fmt.Println("  Server B releases lock")
}

// ExampleInventory_Code shows the code pattern.
func ExampleInventory_Code() {
	fmt.Println("=== Code Example ===")
	fmt.Println(`
  // Create Redis client and lock
  client := redis.NewClient(&redis.Options{Addr: "localhost:6379"})
  distLock := lock.NewRedisLock(client, "inventory:SKU001",
      lock.WithTTL(5*time.Second))

  // Create inventory manager
  manager := NewInventoryManager(distLock)
  manager.SetStock("SKU001", 100)

  // Process order
  err := manager.DeductStock(ctx, "SKU001", 1)
  if err == ErrInsufficientStock {
      // Return error to customer
      return errors.New("out of stock")
  }
`)
}
