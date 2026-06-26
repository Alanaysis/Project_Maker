package mvcc

import (
	"fmt"
	"math/rand"
	"sync"
	"time"
)

// DemoBasicMVCC demonstrates basic MVCC operations:
// - Creating transactions
// - Reading from snapshots
// - Writing and committing
// - Observing version chains
func DemoBasicMVCC() {
	fmt.Println("\n===== Demo: Basic MVCC Operations =====\n")

	storage := NewMVCCStorage()
	tm := NewTransactionManager(storage)

	// Step 1: Initialize data
	fmt.Println("Step 1: Initialize data (direct writes)")
	storage.Write("account:A", []byte("1000"), 0, 0)
	storage.Write("account:B", []byte("2000"), 0, 0)
	storage.Write("account:C", []byte("500"), 0, 0)
	fmt.Println("  Initial state: A=1000, B=2000, C=500")
	fmt.Println()

	// Step 2: Transaction 1 reads snapshot and transfers from A to B
	fmt.Println("Step 2: Transaction T1 reads snapshot and transfers 300 from A to B")
	t1 := tm.Begin()
	fmt.Printf("  T1 started at timestamp %d\n", t1.StartTime)

	valA, _ := tm.Read(t1, "account:A")
	valB, _ := tm.Read(t1, "account:B")
	fmt.Printf("  T1 reads: A=%s, B=%s\n", string(valA), string(valB))

	tm.Write(t1, "account:A", []byte(fmt.Sprintf("%d", 1000-300)))
	tm.Write(t1, "account:B", []byte(fmt.Sprintf("%d", 2000+300)))
	fmt.Printf("  T1 writes: A=%s, B=%s (pending commit)\n", "700", "2300")

	// Step 3: Transaction 2 reads snapshot (should see original values!)
	fmt.Println("\nStep 3: Transaction T2 starts (snapshot isolation)")
	t2 := tm.Begin()
	fmt.Printf("  T2 started at timestamp %d\n", t2.StartTime)

	valA2, _ := tm.Read(t2, "account:A")
	valB2, _ := tm.Read(t2, "account:B")
	fmt.Printf("  T2 reads: A=%s, B=%s (UNCHANGED - snapshot isolation!)\n",
		string(valA2), string(valB2))

	// Step 4: T1 commits
	fmt.Println("\nStep 4: T1 commits")
	err := tm.Commit(t1)
	if err != nil {
		fmt.Printf("  T1 commit failed: %v\n", err)
	} else {
		fmt.Println("  T1 committed successfully")
	}

	// Step 5: T2 tries to commit (should detect conflict)
	fmt.Println("\nStep 5: T2 tries to commit (read-write conflict expected)")
	err = tm.Commit(t2)
	if err != nil {
		fmt.Printf("  T2 commit failed (expected): %v\n", err)
	} else {
		fmt.Println("  T2 committed (no conflict detected in this simple case)")
	}

	// Step 6: Show version chains
	fmt.Println("\nStep 6: Version chains after operations:")
	tm.PrintStorage()
}

// DemoSnapshotIsolation demonstrates snapshot isolation in detail.
func DemoSnapshotIsolation() {
	fmt.Println("\n===== Demo: Snapshot Isolation =====\n")

	storage := NewMVCCStorage()
	tm := NewTransactionManager(storage)

	// Initialize
	fmt.Println("Step 1: Initialize data")
	storage.Write("counter", []byte("0"), 0, 0)
	fmt.Println("  counter = 0")
	fmt.Println()

	// Concurrent reads see the same snapshot
	fmt.Println("Step 2: Multiple transactions read the same snapshot")
	t1 := tm.Begin()
	t2 := tm.Begin()
	t3 := tm.Begin()

	val1, _ := tm.Read(t1, "counter")
	val2, _ := tm.Read(t2, "counter")
	val3, _ := tm.Read(t3, "counter")

	fmt.Printf("  T1 reads counter = %s\n", string(val1))
	fmt.Printf("  T2 reads counter = %s\n", string(val2))
	fmt.Printf("  T3 reads counter = %s\n", string(val3))
	fmt.Println("  All transactions see the SAME value (consistent snapshot)")
	fmt.Println()

	// Each transaction writes independently
	fmt.Println("Step 3: Each transaction increments independently")
	tm.Write(t1, "counter", []byte("1"))
	tm.Write(t2, "counter", []byte("1"))
	tm.Write(t3, "counter", []byte("1"))
	fmt.Println("  T1 writes counter = 1")
	fmt.Println("  T2 writes counter = 1")
	fmt.Println("  T3 writes counter = 1")
	fmt.Println()

	// Commit T1 first
	fmt.Println("Step 4: T1 commits first")
	tm.Commit(t1)
	fmt.Println("  T1 committed. Storage now shows counter = 1")
	storage.PrintVersionChain("counter")
	fmt.Println()

	// T2 and T3 see different histories - demonstrates snapshot isolation
	fmt.Println("Step 5: T2 and T3 commit (may conflict)")
	tm.Commit(t2)
	fmt.Println("  T2 committed (no conflict with T1's read)")
	tm.Commit(t3)
	fmt.Println("  T3 committed (no conflict with T1's read)")

	// Show final version chain
	fmt.Println("\nStep 6: Final version chain:")
	storage.PrintVersionChain("counter")
}

// DemoConflictDetection demonstrates write-write and read-write conflict detection.
func DemoConflictDetection() {
	fmt.Println("\n===== Demo: Conflict Detection =====\n")

	storage := NewMVCCStorage()
	detector := NewConflictDetector()
	tm := NewTransactionManager(storage)

	// Initialize
	storage.Write("balance", []byte("1000"), 0, 0)
	fmt.Println("Initial: balance = 1000")
	fmt.Println()

	// Scenario 1: Write-Write conflict
	fmt.Println("Scenario 1: Write-Write Conflict")
	fmt.Println("  Two transactions try to modify the same key")
	t1 := tm.Begin()
	t2 := tm.Begin()

	val, _ := tm.Read(t1, "balance")
	tm.Write(t1, "balance", []byte(fmt.Sprintf("%d", 1000-200)))
	detector.RecordWrite(t1.ID, "balance")

	// t2 also reads and writes
	_ = tm.Read(t2, "balance")
	tm.Write(t2, "balance", []byte(fmt.Sprintf("%d", 1000+100)))
	detector.RecordWrite(t2.ID, "balance")

	// Check for write-write conflict
	if conflict := detector.CheckWriteWrite(t1, t2); conflict != nil {
		fmt.Printf("  Conflict detected: %v\n", conflict)
		fmt.Println("  Resolution: Abort one transaction (typically the 'younger' one)")
	}
	fmt.Println()

	// Scenario 2: Read-Write conflict
	fmt.Println("Scenario 2: Read-Write Conflict")
	fmt.Println("  T1 reads a key, T2 writes to it and commits")
	t3 := tm.Begin()
	t4 := tm.Begin()

	val3, _ := tm.Read(t3, "balance")
	fmt.Printf("  T3 reads balance = %s\n", string(val3))
	tm.Write(t3, "balance", []byte("900"))
	detector.RecordWrite(t3.ID, "balance")

	tm.Read(t4, "balance")
	tm.Write(t4, "balance", []byte("1100"))
	detector.RecordWrite(t4.ID, "balance")

	if conflict := detector.CheckReadWrite(t3, t4); conflict != nil {
		fmt.Printf("  Conflict detected: %v\n", conflict)
		fmt.Println("  Resolution: Abort T3 (it read stale data)")
	}
	fmt.Println()

	// Scenario 3: Write-Write conflict (reversed order)
	fmt.Println("Scenario 3: Write-Write Conflict (reversed check)")
	if conflict := detector.CheckWriteWrite(t2, t1); conflict != nil {
		fmt.Printf("  Conflict detected: %v\n", conflict)
		fmt.Println("  Resolution: Abort one transaction")
	}
	fmt.Println()

	// Scenario 4: No conflict
	fmt.Println("Scenario 4: No Conflict")
	fmt.Println("  Two transactions modify different keys")
	t5 := tm.Begin()
	t6 := tm.Begin()
	tm.Write(t5, "key1", []byte("value1"))
	detector.RecordWrite(t5.ID, "key1")
	tm.Write(t6, "key2", []byte("value2"))
	detector.RecordWrite(t6.ID, "key2")

	if conflict := detector.CheckWriteWrite(t5, t6); conflict != nil {
		fmt.Printf("  Conflict: %v\n", conflict)
	} else {
		fmt.Println("  No conflict - both transactions can commit safely")
	}
}

// DemoGarbageCollection demonstrates MVCC garbage collection.
func DemoGarbageCollection() {
	fmt.Println("\n===== Demo: Garbage Collection =====\n")

	storage := NewMVCCStorage()
	tm := NewTransactionManager(storage)
	gc := NewGarbageCollector(storage)

	// Create multiple versions of the same key
	fmt.Println("Step 1: Create multiple versions of 'account:A'")
	for i := 1; i <= 10; i++ {
		ts := storage.NextTimestamp()
		storage.Write("account:A", []byte(fmt.Sprintf("version_%d", i)), ts, i)
		fmt.Printf("  Version %d: account:A = version_%d (writeTS=%d)\n", i, i, ts)
	}
	fmt.Println()

	// Show version chain before GC
	fmt.Println("Step 2: Version chain BEFORE garbage collection:")
	storage.PrintVersionChain("account:A")
	fmt.Println()

	// Register an active snapshot
	fmt.Println("Step 3: Register an active snapshot at timestamp 5")
	gc.RegisterSnapshot(5)

	// Run garbage collection
	fmt.Println("Step 4: Run garbage collection")
	reclaimed, cleaned := gc.Collect()
	fmt.Printf("  Reclaimed %d old versions, cleaned %d keys\n", reclaimed, cleaned)
	fmt.Println()

	// Show version chain after GC
	fmt.Println("Step 5: Version chain AFTER garbage collection:")
	storage.PrintVersionChain("account:A")
	fmt.Println()

	// Unregister snapshot and collect again
	fmt.Println("Step 6: Unregister snapshot and collect again")
	gc.UnregisterSnapshot(5)
	reclaimed, cleaned = gc.Collect()
	fmt.Printf("  Reclaimed %d old versions, cleaned %d keys\n", reclaimed, cleaned)
	fmt.Println()

	fmt.Println("Step 7: Final version chain:")
	storage.PrintVersionChain("account:A")
}

// DemoDeadlockDetection demonstrates deadlock detection using wait-for graphs.
func DemoDeadlockDetection() {
	fmt.Println("\n===== Demo: Deadlock Detection =====\n")

	detector := NewConflictDetector()

	fmt.Println("Step 1: Build a wait-for graph")
	fmt.Println("  T1 waits for T2 (T1 needs a key held by T2)")
	fmt.Println("  T2 waits for T3 (T2 needs a key held by T3)")
	fmt.Println("  T3 waits for T1 (T3 needs a key held by T1)")
	fmt.Println()

	detector.AddWaitEdge(1, 2)
	detector.AddWaitEdge(2, 3)
	detector.AddWaitEdge(3, 1)

	fmt.Println("Step 2: Check for cycles in the wait-for graph")
	cycle := detector.DetectCycle()
	if cycle != nil {
		fmt.Printf("  DEADLOCK DETECTED! Cycle: %v\n", cycle)
		fmt.Println("  Resolution: Abort the youngest transaction in the cycle")
	} else {
		fmt.Println("  No deadlock detected")
	}
	fmt.Println()

	// Scenario without deadlock
	fmt.Println("Step 3: Clear graph and add non-cyclic edges")
	detector.RemoveTransaction(1)
	detector.RemoveTransaction(2)
	detector.RemoveTransaction(3)

	detector.AddWaitEdge(4, 5)
	detector.AddWaitEdge(5, 6)

	fmt.Println("  T4 waits for T5")
	fmt.Println("  T5 waits for T6")
	fmt.Println()

	cycle = detector.DetectCycle()
	if cycle != nil {
		fmt.Printf("  DEADLOCK DETECTED! Cycle: %v\n", cycle)
	} else {
		fmt.Println("  No deadlock detected (no cycle: T4->T5->T6)")
	}
}

// DemoSSI demonstrates Serializable Snapshot Isolation.
func DemoSSI() {
	fmt.Println("\n===== Demo: Serializable Snapshot Isolation (SSI) =====\n")

	storage := NewMVCCStorage()
	detector := NewConflictDetector()
	tm := NewTransactionManager(storage)

	// Initialize two accounts with a constraint: total must be 3000
	fmt.Println("Step 1: Initialize data with constraint: A + B = 3000")
	storage.Write("account:A", []byte("1500"), 0, 0)
	storage.Write("account:B", []byte("1500"), 0, 0)
	fmt.Println("  account:A = 1500")
	fmt.Println("  account:B = 1500")
	fmt.Println("  Total = 3000 (constraint satisfied)")
	fmt.Println()

	// Write skew scenario (classic SSI anomaly)
	fmt.Println("Step 2: Write Skew Scenario")
	fmt.Println("  T1 reads A and B, then writes only A")
	fmt.Println("  T2 reads A and B, then writes only B")
	fmt.Println("  Each transaction individually sees valid state")
	fmt.Println("  But together they violate the constraint!")
	fmt.Println()

	t1 := tm.Begin()
	t2 := tm.Begin()

	valA1, _ := tm.Read(t1, "account:A")
	valB1, _ := tm.Read(t1, "account:B")
	fmt.Printf("  T1 reads: A=%s, B=%s\n", string(valA1), string(valB1))

	valA2, _ := tm.Read(t2, "account:A")
	valB2, _ := tm.Read(t2, "account:B")
	fmt.Printf("  T2 reads: A=%s, B=%s\n", string(valA2), string(valB2))

	// T1 writes A (but not B)
	tm.Write(t1, "account:A", []byte("500"))
	fmt.Println("  T1 writes: A = 500 (skipping B)")

	// T2 writes B (but not A)
	tm.Write(t2, "account:B", []byte("500"))
	fmt.Println("  T2 writes: B = 500 (skipping A)")

	// Commit T1
	fmt.Println("\nStep 3: T1 commits")
	err := tm.Commit(t1)
	if err != nil {
		fmt.Printf("  T1 commit failed: %v\n", err)
	} else {
		fmt.Println("  T1 committed")
	}

	// Try to commit T2 - SSI should detect the serialization anomaly
	fmt.Println("\nStep 4: T2 tries to commit")
	err = tm.Commit(t2)
	if err != nil {
		fmt.Printf("  T2 commit failed (SSI detected anomaly): %v\n", err)
		fmt.Println("  SSI correctly prevented the write skew anomaly!")
	} else {
		fmt.Println("  T2 committed (SSI did not detect anomaly in this simple case)")
		fmt.Println("  Note: Real SSI implementations use timestamp-based dependency tracking")
	}

	// Show the result
	fmt.Println("\nStep 5: Final state")
	finalA, _ := tm.snapshotMgr.Read(t1, "account:A")
	finalB, _ := tm.snapshotMgr.Read(t2, "account:B")
	fmt.Printf("  account:A = %s\n", string(finalA))
	fmt.Printf("  account:B = %s\n", string(finalB))
	total := 0
	if finalA != nil {
		fmt.Sscanf(string(finalA), "%d", &total)
	}
	fmt.Printf("  Total = %d (constraint: %s)\n", total, "violated" + " (if no anomaly detected)")
}

// DemoConcurrentTransactions demonstrates concurrent transaction processing.
func DemoConcurrentTransactions() {
	fmt.Println("\n===== Demo: Concurrent Transactions =====\n")

	storage := NewMVCCStorage()
	tm := NewTransactionManager(storage)

	// Initialize
	storage.Write("counter", []byte("0"), 0, 0)
	fmt.Println("Initial counter = 0")
	fmt.Println()

	// Simulate concurrent transactions
	var wg sync.WaitGroup
	results := make([]string, 0)
	var resultsMu sync.Mutex

	numTxns := 5
	increments := 10

	fmt.Printf("Launching %d concurrent transactions, each incrementing %d times\n", numTxns, increments)
	fmt.Println()

	for i := 0; i < numTxns; i++ {
		wg.Add(1)
		go func(txnNum int) {
			defer wg.Done()

			tx := tm.Begin()
			fmt.Printf("  [T%d] Started at timestamp %d\n", txnNum+1, tx.StartTime)

			for j := 0; j < increments; j++ {
				val, _ := tm.Read(tx, "counter")
				current := 0
				if val != nil {
					fmt.Sscanf(string(val), "%d", &current)
				}
				tm.Write(tx, "counter", []byte(fmt.Sprintf("%d", current+1)))
			}

			err := tm.Commit(tx)
			resultsMu.Lock()
			if err != nil {
				results = append(results, fmt.Sprintf("  [T%d] Aborted due to: %v", txnNum+1, err))
			} else {
				results = append(results, fmt.Sprintf("  [T%d] Committed successfully", txnNum+1))
			}
			resultsMu.Unlock()
		}(i)
	}

	wg.Wait()

	fmt.Println()
	for _, r := range results {
		fmt.Println(r)
	}

	// Show final state
	fmt.Println("\nFinal version chain for 'counter':")
	storage.PrintVersionChain("counter")
}

// RunAllDemos runs all MVCC demos.
func RunAllDemos() {
	rand.Seed(time.Now().UnixNano())

	fmt.Println("╔═══════════════════════════════════════════════════════════╗")
	fmt.Println("║          MVCC Learning Project - Demo Suite               ║")
	fmt.Println("║          Multi-Version Concurrency Control                ║")
	fmt.Println("╚═══════════════════════════════════════════════════════════╝")

	DemoBasicMVCC()
	DemoSnapshotIsolation()
	DemoConflictDetection()
	DemoGarbageCollection()
	DemoDeadlockDetection()
	DemoSSI()
	DemoConcurrentTransactions()

	fmt.Println("\n╔═══════════════════════════════════════════════════════════╗")
	fmt.Println("║                    Demo Complete!                         ║")
	fmt.Println("╚═══════════════════════════════════════════════════════════╝")
}
