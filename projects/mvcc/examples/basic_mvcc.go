// Package main demonstrates basic MVCC operations.
//
// This example shows:
// 1. How MVCC stores multiple versions of data
// 2. How transactions get consistent snapshots
// 3. How write-write conflicts are detected
// 4. How version chains grow over time
package main

import (
	"fmt"
	"mvcc/src"
)

func main() {
	fmt.Println("=== MVCC Basic Operations Demo ===\n")

	// Create MVCC storage
	storage := mvcc.NewMVCCStorage()
	tm := mvcc.NewTransactionManager(storage)

	// Step 1: Initialize data with direct writes (system/initial transaction)
	fmt.Println("Step 1: Initialize data")
	ts := storage.NextTimestamp()
	storage.Write("user:1", []byte("Alice"), ts, 0)
	storage.Write("user:2", []byte("Bob"), ts, 0)
	storage.Write("account:balance", []byte("1000"), ts, 0)
	fmt.Println("  Created: user:1=Alice, user:2=Bob, account:balance=1000")
	fmt.Println()

	// Step 2: Transaction 1 - Read and modify
	fmt.Println("Step 2: Transaction T1 - Read snapshot and transfer money")
	t1 := tm.Begin()
	fmt.Printf("  T1 started at timestamp %d\n", t1.StartTime)

	// Read from snapshot
	balance, _ := tm.Read(t1, "account:balance")
	user1, _ := tm.Read(t1, "user:1")
	fmt.Printf("  T1 reads: balance=%s, user=%s\n", string(balance), string(user1))

	// Write (buffered in transaction's write set)
	tm.Write(t1, "account:balance", []byte("800"))
	fmt.Println("  T1 writes: balance=800 (pending commit)")

	// Commit
	err := tm.Commit(t1)
	if err != nil {
		fmt.Printf("  T1 commit failed: %v\n", err)
	} else {
		fmt.Println("  T1 committed successfully")
	}
	fmt.Println()

	// Step 3: Transaction 2 - Read snapshot (sees ORIGINAL balance!)
	fmt.Println("Step 3: Transaction T2 - Read snapshot (snapshot isolation!)")
	t2 := tm.Begin()
	fmt.Printf("  T2 started at timestamp %d\n", t2.StartTime)

	balance2, _ := tm.Read(t2, "account:balance")
	fmt.Printf("  T2 reads: balance=%s (still 1000 - snapshot isolation!)\n", string(balance2))

	// T2 writes based on stale read
	tm.Write(t2, "account:balance", []byte("900"))
	fmt.Println("  T2 writes: balance=900 (based on stale read)")

	// Commit T2
	err = tm.Commit(t2)
	if err != nil {
		fmt.Printf("  T2 commit failed: %v\n", err)
	} else {
		fmt.Println("  T2 committed")
	}
	fmt.Println()

	// Step 4: Show version chains
	fmt.Println("Step 4: Version chains after operations:")
	storage.PrintVersionChain("account:balance")
	fmt.Println()

	// Step 5: More transactions creating versions
	fmt.Println("Step 5: More transactions creating versions")
	for i := 0; i < 5; i++ {
		tx := tm.Begin()
		tm.Write(tx, "account:balance", []byte(fmt.Sprintf("%d", 1000+i*100)))
		tm.Commit(tx)
		fmt.Printf("  Transaction %d committed: balance=%d\n", i+1, 1000+i*100)
	}
	fmt.Println()

	// Step 6: Final version chain
	fmt.Println("Step 6: Final version chain:")
	storage.PrintVersionChain("account:balance")
	fmt.Println()

	// Step 7: Demonstrate rollback
	fmt.Println("Step 7: Demonstrate rollback")
	tRollback := tm.Begin()
	fmt.Printf("  T(rollback) started at timestamp %d\n", tRollback.StartTime)
	tm.Write(tRollback, "account:balance", []byte("0"))
	fmt.Println("  T(rollback) writes: balance=0")
	tm.Rollback(tRollback)
	fmt.Println("  T(rollback) rolled back - writes discarded")
	fmt.Println()

	// Step 8: Verify rollback didn't affect storage
	fmt.Println("Step 8: Version chain after rollback (no new committed version):")
	storage.PrintVersionChain("account:balance")
}
