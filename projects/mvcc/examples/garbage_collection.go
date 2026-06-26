// Package main demonstrates MVCC garbage collection.
//
// This example shows:
// 1. How version chains grow over time
// 2. How garbage collection reclaims old versions
// 3. Why GC is safe (based on active snapshot timestamps)
// 4. The trade-off between GC aggressiveness and transaction safety
package main

import (
	"fmt"
	"mvcc/src"
)

func main() {
	fmt.Println("=== Garbage Collection Demo ===\n")

	storage := mvcc.NewMVCCStorage()
	tm := mvcc.NewTransactionManager(storage)
	gc := mvcc.NewGarbageCollector(storage)

	// Phase 1: Create many versions
	fmt.Println("Phase 1: Create versions over time")
	fmt.Println("-----------------------------------")

	for i := 1; i <= 10; i++ {
		ts := storage.NextTimestamp()
		tx := tm.Begin()
		tm.Write(tx, "config:version", []byte(fmt.Sprintf("v%d", i)))
		tm.Commit(tx)
		fmt.Printf("  Version %d created (writeTS=%d): config:version = v%d\n", i, ts, i)
	}
	fmt.Println()

	// Show version chain
	fmt.Println("Version chain BEFORE garbage collection:")
	storage.PrintVersionChain("config:version")
	fmt.Println()

	// Phase 2: Register active snapshot and GC
	fmt.Println("Phase 2: Active snapshot at timestamp 5")
	fmt.Println("-----------------------------------------")
	gc.RegisterSnapshot(5)
	fmt.Println("  Active snapshot registered: can see versions from timestamp 5 onwards")
	fmt.Println()

	fmt.Println("Running garbage collection...")
	reclaimed, cleaned := gc.Collect()
	fmt.Printf("  Reclaimed %d old versions\n", reclaimed)
	fmt.Printf("  Cleaned %d keys\n", cleaned)
	fmt.Println()

	fmt.Println("Version chain AFTER garbage collection (with active snapshot):")
	storage.PrintVersionChain("config:version")
	fmt.Println()

	// Phase 3: All transactions committed, GC again
	fmt.Println("Phase 3: All transactions committed, GC again")
	fmt.Println("------------------------------------------------")
	gc.UnregisterSnapshot(5)
	fmt.Println("  Active snapshot unregistered")
	fmt.Println()

	fmt.Println("Running garbage collection...")
	reclaimed, cleaned = gc.Collect()
	fmt.Printf("  Reclaimed %d old versions\n", reclaimed)
	fmt.Printf("  Cleaned %d keys\n", cleaned)
	fmt.Println()

	fmt.Println("Version chain AFTER garbage collection (no active snapshots):")
	storage.PrintVersionChain("config:version")
	fmt.Println()

	// Phase 4: Demonstrate GC safety
	fmt.Println("Phase 4: GC Safety Demonstration")
	fmt.Println("----------------------------------")
	fmt.Println()

	// Create fresh data with multiple versions
	storage.Write("data:key1", []byte("v1"), 1, 1)
	storage.Write("data:key1", []byte("v2"), 2, 2)
	storage.Write("data:key1", []byte("v3"), 3, 3)
	storage.Write("data:key1", []byte("v4"), 4, 4)
	storage.Write("data:key1", []byte("v5"), 5, 5)

	fmt.Println("Created 5 versions of 'data:key1' (timestamps 1-5)")
	fmt.Println()

	// Active transaction at timestamp 3
	fmt.Println("Active transaction reads snapshot at timestamp 3")
	gc.RegisterSnapshot(3)

	fmt.Println("Version chain before GC:")
	storage.PrintVersionChain("data:key1")
	fmt.Println()

	fmt.Println("Running GC...")
	reclaimed, cleaned = gc.Collect()
	fmt.Printf("  Reclaimed %d versions, cleaned %d keys\n", reclaimed, cleaned)
	fmt.Println()

	fmt.Println("Version chain after GC (snapshot at ts=3 is protected):")
	storage.PrintVersionChain("data:key1")
	fmt.Println()

	fmt.Println("  Note: Versions at timestamps 1 and 2 were removed")
	fmt.Println("  because no active transaction needs them (all started after ts=2)")
	fmt.Println()

	// Try to read with the active snapshot
	fmt.Println("Reading with active snapshot (ts=3):")
	activeTx := tm.Begin()
	activeTx.ReadTimestamp = 3
	val, exists, _ := storage.Read("data:key1", 3)
	if exists {
		fmt.Printf("  Found: %s (correct!)\n", string(val))
	} else {
		fmt.Println("  Not found (unexpected!)")
	}
	fmt.Println()

	gc.UnregisterSnapshot(3)

	// Summary
	fmt.Println("=== Garbage Collection Summary ===")
	fmt.Println("  Purpose: Reclaim memory from old, no-longer-needed versions")
	fmt.Println("  Safety:  Only remove versions older than oldest active snapshot")
	fmt.Println("  Trade-off:")
	fmt.Println("    - Aggressive GC: Less memory, but more frequent runs")
	fmt.Println("    - Conservative GC: More memory, but fewer runs")
	fmt.Println("  Key insight: GC must know all active snapshot timestamps")
}
