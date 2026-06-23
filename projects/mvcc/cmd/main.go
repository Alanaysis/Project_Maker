package main

import (
	"fmt"
	"log"
	"sync"
	"time"

	"mvcc/internal"
	"mvcc/internal/gc"
	"mvcc/internal/store"
	"mvcc/internal/transaction"
)

func main() {
	fmt.Println("=== MVCC (Multi-Version Concurrency Control) Demo ===")
	fmt.Println()

	// Demo 1: Basic MVCC operations
	demoBasicOperations()

	// Demo 2: Snapshot Isolation
	demoSnapshotIsolation()

	// Demo 3: Write-Write Conflict Detection
	demoWriteWriteConflict()

	// Demo 4: Concurrent Transactions
	demoConcurrentTransactions()

	// Demo 5: Garbage Collection
	demoGarbageCollection()

	fmt.Println("\n=== All demos completed ===")
}

func demoBasicOperations() {
	fmt.Println("--- Demo 1: Basic MVCC Operations ---")

	engine := internal.NewMVSSEngine()

	// Write data
	txn := engine.Begin()
	fmt.Printf("Transaction %d started (snapshot ts=%d)\n", txn.ID(), txn.StartTimestamp())

	txn.Write("name", []byte("Alice"))
	txn.Write("age", []byte("30"))
	txn.Write("city", []byte("Beijing"))

	err := txn.Commit()
	if err != nil {
		log.Fatalf("Commit failed: %v", err)
	}
	fmt.Println("Committed: name=Alice, age=30, city=Beijing")

	// Read data
	txn2 := engine.Begin()
	name, _ := txn2.Read("name")
	age, _ := txn2.Read("age")
	city, _ := txn2.Read("city")
	fmt.Printf("Read: name=%s, age=%s, city=%s\n", string(name), string(age), string(city))
	txn2.Commit()

	// Update data
	txn3 := engine.Begin()
	txn3.Write("age", []byte("31"))
	txn3.Commit()
	fmt.Println("Updated: age=31")

	// Verify update
	txn4 := engine.Begin()
	age, _ = txn4.Read("age")
	fmt.Printf("Read after update: age=%s\n", string(age))
	txn4.Commit()

	// Delete data
	txn5 := engine.Begin()
	txn5.Delete("city")
	txn5.Commit()
	fmt.Println("Deleted: city")

	// Verify delete
	txn6 := engine.Begin()
	_, ok := txn6.Read("city")
	fmt.Printf("Read after delete: found=%v\n", ok)
	txn6.Commit()

	// Show version history
	fmt.Println("\nVersion history for 'age':")
	versions := engine.Store().AllVersions("age")
	for i, v := range versions {
		fmt.Printf("  Version %d: value=%s, createdBy=%d, createdAt=%d\n",
			i+1, string(v.Value), v.CreatedBy, v.CreatedAt)
	}

	fmt.Println()
}

func demoSnapshotIsolation() {
	fmt.Println("--- Demo 2: Snapshot Isolation ---")

	engine := internal.NewMVSSEngine()

	// Initial data
	txn := engine.Begin()
	txn.Write("balance", []byte("1000"))
	txn.Commit()
	fmt.Println("Initial: balance=1000")

	// T1 starts (snapshot before T2's write)
	t1 := engine.Begin()
	fmt.Printf("T1 started at ts=%d\n", t1.StartTimestamp())

	// T2 starts and modifies balance
	t2 := engine.Begin()
	t2.Write("balance", []byte("1500"))
	t2.Commit()
	fmt.Println("T2 committed: balance=1500")

	// T1 reads - should see old value (snapshot isolation)
	balance, _ := t1.Read("balance")
	fmt.Printf("T1 reads balance=%s (snapshot isolation: sees old value)\n", string(balance))

	// T1 writes - should succeed (no conflict yet)
	t1.Write("balance", []byte("1200"))

	// T1 commits - but T2 already committed, so this will fail
	err := t1.Commit()
	if err != nil {
		fmt.Printf("T1 commit failed: %v\n", err)
	} else {
		fmt.Println("T1 committed successfully")
	}

	// New transaction sees T2's value
	t3 := engine.Begin()
	balance, _ = t3.Read("balance")
	fmt.Printf("T3 reads balance=%s (sees T2's committed value)\n", string(balance))
	t3.Commit()

	fmt.Println()
}

func demoWriteWriteConflict() {
	fmt.Println("--- Demo 3: Write-Write Conflict Detection ---")

	engine := internal.NewMVSSEngine()

	// Initial data
	txn := engine.Begin()
	txn.Write("account", []byte("1000"))
	txn.Commit()
	fmt.Println("Initial: account=1000")

	// Two transactions try to update the same key
	t1 := engine.Begin()
	t2 := engine.Begin()

	fmt.Printf("T1 started at ts=%d\n", t1.StartTimestamp())
	fmt.Printf("T2 started at ts=%d\n", t2.StartTimestamp())

	// Both read the same value
	t1.Read("account")
	t2.Read("account")

	// T1 writes first
	t1.Write("account", []byte("1100"))
	fmt.Println("T1 writes: account=1100")

	// T1 commits first
	err := t1.Commit()
	if err != nil {
		log.Fatalf("T1 commit failed: %v", err)
	}
	fmt.Println("T1 committed successfully")

	// T2 tries to write and commit
	t2.Write("account", []byte("900"))
	fmt.Println("T2 writes: account=900")

	err = t2.Commit()
	if err != nil {
		fmt.Printf("T2 commit failed (conflict detected): %v\n", err)
	} else {
		fmt.Println("T2 committed successfully")
	}

	// Final state
	t3 := engine.Begin()
	account, _ := t3.Read("account")
	fmt.Printf("Final state: account=%s\n", string(account))
	t3.Commit()

	fmt.Println()
}

func demoConcurrentTransactions() {
	fmt.Println("--- Demo 4: Concurrent Transactions ---")

	engine := internal.NewMVSSEngine()

	// Initialize shared data
	txn := engine.Begin()
	for i := 0; i < 5; i++ {
		key := fmt.Sprintf("counter_%d", i)
		txn.Write(key, []byte("0"))
	}
	txn.Commit()
	fmt.Println("Initialized 5 counters to 0")

	// Concurrent updates
	var wg sync.WaitGroup
	successCount := 0
	var mu sync.Mutex

	for i := 0; i < 20; i++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()

			txn := engine.Begin()
			key := fmt.Sprintf("counter_%d", id%5)

			// Read current value
			val, _ := txn.Read(key)
			current := 0
			fmt.Sscanf(string(val), "%d", &current)

			// Increment
			txn.Write(key, []byte(fmt.Sprintf("%d", current+1)))

			// Small delay to increase chance of conflicts
			time.Sleep(time.Millisecond)

			err := txn.Commit()
			mu.Lock()
			if err == nil {
				successCount++
			}
			mu.Unlock()
		}(i)
	}
	wg.Wait()

	fmt.Printf("Completed: %d/20 transactions succeeded\n", successCount)

	// Show final counter values
	fmt.Println("Final counter values:")
	for i := 0; i < 5; i++ {
		txn := engine.Begin()
		key := fmt.Sprintf("counter_%d", i)
		val, _ := txn.Read(key)
		fmt.Printf("  %s = %s\n", key, string(val))
		txn.Commit()
	}

	fmt.Println()
}

func demoGarbageCollection() {
	fmt.Println("--- Demo 5: Garbage Collection ---")

	s := store.NewStore()
	txMgr := transaction.NewTransactionManager()
	gcCollector := gc.NewGarbageCollector(s, txMgr, 100*time.Millisecond)

	// Create many versions
	fmt.Println("Creating 100 versions of 'data'...")
	for i := 1; i <= 100; i++ {
		txn := txMgr.Begin()
		s.Put("data", []byte(fmt.Sprintf("version_%d", i)), txn.ID, txn.StartTimestamp)
		txMgr.Commit(txn.ID)
	}

	fmt.Printf("Total versions before GC: %d\n", s.VersionCount())

	// Start GC
	gcCollector.Start()
	time.Sleep(300 * time.Millisecond) // Let GC run a few times
	gcCollector.Stop()

	fmt.Printf("Total versions after GC: %d\n", s.VersionCount())

	stats := gcCollector.Stats()
	fmt.Printf("GC stats: runs=%d, totalRemoved=%d\n", stats.TotalRuns, stats.TotalRemoved)

	fmt.Println()
}
