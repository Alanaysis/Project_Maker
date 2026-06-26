// Package main demonstrates conflict detection in MVCC.
//
// This example shows:
// 1. Write-write conflicts (two transactions write the same key)
// 2. Read-write conflicts (one transaction reads what another writes)
// 3. Conflict resolution strategies
package main

import (
	"fmt"
	"mvcc/src"
)

func main() {
	fmt.Println("=== Conflict Detection Demo ===\n")

	storage := mvcc.NewMVCCStorage()
	detector := mvcc.NewConflictDetector()
	tm := mvcc.NewTransactionManager(storage)

	// Initialize
	storage.Write("inventory:item1", []byte("100"), 0, 0)
	storage.Write("inventory:item2", []byte("200"), 0, 0)
	storage.Write("inventory:item3", []byte("50"), 0, 0)

	fmt.Println("Initial inventory:")
	fmt.Println("  item1 = 100")
	fmt.Println("  item2 = 200")
	fmt.Println("  item3 = 50")
	fmt.Println()

	// Scenario 1: Write-Write Conflict
	fmt.Println("Scenario 1: Write-Write Conflict")
	fmt.Println("  Two transactions try to update the same item")
	fmt.Println()

	t1 := tm.Begin()
	t2 := tm.Begin()

	val1, _ := tm.Read(t1, "inventory:item1")
	fmt.Printf("  T1 reads item1 = %s\n", string(val1))

	val2, _ := tm.Read(t2, "inventory:item1")
	fmt.Printf("  T2 reads item1 = %s\n", string(val2))

	// Both write to item1
	tm.Write(t1, "inventory:item1", []byte("90"))  // T1: -10
	tm.Write(t2, "inventory:item1", []byte("110")) // T2: +10
	detector.RecordWrite(t1.ID, "inventory:item1")
	detector.RecordWrite(t2.ID, "inventory:item1")

	// Check for conflict
	if conflict := detector.CheckWriteWrite(t1, t2); conflict != nil {
		fmt.Printf("  CONFLICT: %v\n", conflict)
		fmt.Println("  Resolution: Abort T2 (younger transaction)")
		tm.Rollback(t2)
		fmt.Println("  T2 aborted, T1 can commit safely")
	}

	err := tm.Commit(t1)
	if err != nil {
		fmt.Printf("  T1 commit failed: %v\n", err)
	} else {
		fmt.Println("  T1 committed: item1 = 90")
	}
	fmt.Println()

	// Scenario 2: Read-Write Conflict (Write Skew)
	fmt.Println("Scenario 2: Write Skew (Read-Write Conflict)")
	fmt.Println("  Constraint: item1 + item2 >= 250")
	fmt.Println("  T1 reads both, T2 reads both, they each modify one")
	fmt.Println()

	t3 := tm.Begin()
	t4 := tm.Begin()

	item1Val, _ := tm.Read(t3, "inventory:item1")
	item2Val, _ := tm.Read(t3, "inventory:item2")
	fmt.Printf("  T3 reads: item1=%s, item2=%s\n", string(item1Val), string(item2Val))

	item1Val2, _ := tm.Read(t4, "inventory:item1")
	item2Val2, _ := tm.Read(t4, "inventory:item2")
	fmt.Printf("  T4 reads: item1=%s, item2=%s\n", string(item1Val2), string(item2Val2))

	// T3 reduces item1, T4 reduces item2
	tm.Write(t3, "inventory:item1", []byte("50")) // 90 - 40 = 50
	tm.Write(t4, "inventory:item2", []byte("100")) // 200 - 100 = 100
	detector.RecordWrite(t3.ID, "inventory:item1")
	detector.RecordWrite(t4.ID, "inventory:item2")

	// Check for read-write conflict
	if conflict := detector.CheckReadWrite(t3, t4); conflict != nil {
		fmt.Printf("  CONFLICT: %v\n", conflict)
		fmt.Println("  SSI detected: T3 read stale data")
		fmt.Println("  Resolution: Abort T3")
		tm.Rollback(t3)
	} else {
		fmt.Println("  No conflict detected by basic check")
		fmt.Println("  (Real SSI uses timestamp-based dependency tracking)")
	}

	err = tm.Commit(t4)
	if err != nil {
		fmt.Printf("  T4 commit failed: %v\n", err)
	} else {
		fmt.Println("  T4 committed: item2 = 100")
	}
	fmt.Println()

	// Scenario 3: No Conflict (Different Keys)
	fmt.Println("Scenario 3: No Conflict (Different Keys)")
	fmt.Println("  Two transactions modify different items")
	fmt.Println()

	t5 := tm.Begin()
	t6 := tm.Begin()

	tm.Write(t5, "inventory:item1", []byte("80"))
	detector.RecordWrite(t5.ID, "inventory:item1")

	tm.Write(t6, "inventory:item3", []byte("60"))
	detector.RecordWrite(t6.ID, "inventory:item3")

	if conflict := detector.CheckWriteWrite(t5, t6); conflict != nil {
		fmt.Printf("  CONFLICT: %v\n", conflict)
	} else {
		fmt.Println("  No conflict - both can commit safely!")
	}

	err = tm.Commit(t5)
	if err == nil {
		fmt.Println("  T5 committed: item1 = 80")
	}
	err = tm.Commit(t6)
	if err == nil {
		fmt.Println("  T6 committed: item3 = 60")
	}
	fmt.Println()

	// Summary
	fmt.Println("=== Conflict Detection Summary ===")
	fmt.Println("  Write-Write Conflict: Two txns write the same key")
	fmt.Println("    -> Abort one, retry")
	fmt.Println("  Read-Write Conflict: One txn reads what another writes")
	fmt.Println("    -> SSI detects, abort reader")
	fmt.Println("  No Conflict: Different keys or non-overlapping access")
	fmt.Println("    -> Both can commit safely")
	fmt.Println()

	// Show final storage state
	fmt.Println("Final storage state:")
	storage.PrintVersionChain("inventory:item1")
	storage.PrintVersionChain("inventory:item2")
	storage.PrintVersionChain("inventory:item3")
}
