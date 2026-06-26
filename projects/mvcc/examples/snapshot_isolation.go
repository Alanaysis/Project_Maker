// Package main demonstrates snapshot isolation in action.
//
// This example shows how snapshot isolation:
// 1. Gives each transaction a consistent view of the database
// 2. Allows concurrent reads without blocking
// 3. Prevents dirty reads (uncommitted data)
// 4. Prevents non-repeatable reads (consistent reads within a transaction)
package main

import (
	"fmt"
	"mvcc/src"
)

func main() {
	fmt.Println("=== Snapshot Isolation Demo ===\n")

	storage := mvcc.NewMVCCStorage()
	tm := mvcc.NewTransactionManager(storage)

	// Initialize
	fmt.Println("Step 1: Initialize data")
	storage.Write("product:price", []byte("100"), 0, 0)
	storage.Write("product:stock", []byte("50"), 0, 0)
	storage.Write("product:discount", []byte("0"), 0, 0)
	fmt.Println("  product:price = 100")
	fmt.Println("  product:stock = 50")
	fmt.Println("  product:discount = 0")
	fmt.Println()

	// Scenario: Multiple readers see the same snapshot
	fmt.Println("Step 2: Multiple concurrent readers (snapshot isolation)")
	fmt.Println("  All readers see the SAME consistent view:")

	readers := make([]*mvcc.Transaction, 3)
	for i := 0; i < 3; i++ {
		readers[i] = tm.Begin()
		price, _ := tm.Read(readers[i], "product:price")
		stock, _ := tm.Read(readers[i], "product:stock")
		fmt.Printf("  Reader %d: price=%s, stock=%s\n", i+1, string(price), string(stock))
	}
	fmt.Println()

	// Scenario: A writer commits while readers are active
	fmt.Println("Step 3: Writer commits a new price while readers are active")
	fmt.Println("  Writer updates price from 100 to 120")
	ts := storage.NextTimestamp()
	storage.Write("product:price", []byte("120"), ts, 999)
	storage.Commit(&mvcc.Transaction{ID: 999}) // Commit the writer
	fmt.Println("  Writer committed.")
	fmt.Println()

	// Readers still see old price (snapshot isolation!)
	fmt.Println("Step 4: Readers still see the OLD price (snapshot isolation!)")
	for i := 0; i < 3; i++ {
		price, _ := tm.Read(readers[i], "product:price")
		fmt.Printf("  Reader %d still sees: price=%s\n", i+1, string(price))
	}
	fmt.Println()

	// Scenario: New reader sees the updated price
	fmt.Println("Step 5: New reader sees the UPDATED price")
	newReader := tm.Begin()
	price, _ := tm.Read(newReader, "product:price")
	fmt.Printf("  New reader sees: price=%s (updated value!)\n", string(price))
	fmt.Println()

	// Scenario: Non-repeatable read prevention
	fmt.Println("Step 6: Non-repeatable read prevention")
	fmt.Println("  Transaction reads the same key twice:")
	tx := tm.Begin()
	firstRead, _ := tm.Read(tx, "product:price")
	fmt.Printf("  First read: price=%s\n", string(firstRead))

	// External write happens
	storage.Write("product:price", []byte("150"), storage.NextTimestamp(), 1000)
	tm.Commit(&mvcc.Transaction{ID: 1000})

	// Same transaction reads again - sees the same value!
	secondRead, _ := tm.Read(tx, "product:price")
	fmt.Printf("  Second read: price=%s (same as first!)\n", string(secondRead))
	fmt.Println("  Snapshot isolation guarantees consistent reads within a transaction")
	fmt.Println()

	// Summary
	fmt.Println("=== Snapshot Isolation Summary ===")
	fmt.Println("  1. Each transaction gets a consistent snapshot at start time")
	fmt.Println("  2. Readers never block writers, writers never block readers")
	fmt.Println("  3. Transactions see data as of their snapshot timestamp")
	fmt.Println("  4. No dirty reads, no non-repeatable reads")
	fmt.Println("  5. Phantom reads may still occur (SSI addresses this)")
}
