package gc

import (
	"testing"
	"time"

	"mvcc/internal/store"
	"mvcc/internal/transaction"
)

func TestGarbageCollectorRun(t *testing.T) {
	s := store.NewStore()
	txMgr := transaction.NewTransactionManager()
	gc := NewGarbageCollector(s, txMgr, time.Hour)

	// Create versions using the transaction manager to ensure timestamp alignment
	txn1 := txMgr.Begin()
	s.Put("key1", []byte("v1"), txn1.ID, txn1.StartTimestamp)
	txMgr.Commit(txn1.ID)

	txn2 := txMgr.Begin()
	s.Put("key1", []byte("v2"), txn2.ID, txn2.StartTimestamp)
	txMgr.Commit(txn2.ID)

	txn3 := txMgr.Begin()
	s.Put("key1", []byte("v3"), txn3.ID, txn3.StartTimestamp)
	txMgr.Commit(txn3.ID)

	// Start a new active transaction - this sets the SafePoint
	activeTxn := txMgr.Begin()

	// Run GC - versions before SafePoint that are superseded should be removed
	removed := gc.Run()

	// v1 and v2 are superseded by v3 and created before SafePoint
	// v3 is kept because it's the latest old version
	if removed != 2 {
		t.Fatalf("expected 2 versions removed, got %d", removed)
	}

	stats := gc.Stats()
	if stats.TotalRuns != 1 {
		t.Fatalf("expected 1 total run, got %d", stats.TotalRuns)
	}
	if stats.TotalRemoved != 2 {
		t.Fatalf("expected 2 total removed, got %d", stats.TotalRemoved)
	}

	// Verify remaining versions
	remaining := s.AllVersions("key1")
	if len(remaining) != 1 {
		t.Fatalf("expected 1 remaining version, got %d", len(remaining))
	}
	if string(remaining[0].Value) != "v3" {
		t.Fatalf("expected remaining version to be 'v3', got '%s'", string(remaining[0].Value))
	}

	_ = activeTxn
}

func TestGarbageCollectorNoActiveTransactions(t *testing.T) {
	s := store.NewStore()
	txMgr := transaction.NewTransactionManager()
	gc := NewGarbageCollector(s, txMgr, time.Hour)

	// Create versions using the transaction manager
	txn1 := txMgr.Begin()
	s.Put("key1", []byte("v1"), txn1.ID, txn1.StartTimestamp)
	txMgr.Commit(txn1.ID)

	txn2 := txMgr.Begin()
	s.Put("key1", []byte("v2"), txn2.ID, txn2.StartTimestamp)
	txMgr.Commit(txn2.ID)

	// No active transactions - GC should remove old versions
	removed := gc.Run()

	// v1 is superseded by v2, so it should be removed
	// v2 is the latest and should be kept
	if removed != 1 {
		t.Fatalf("expected 1 version removed, got %d", removed)
	}

	remaining := s.AllVersions("key1")
	if len(remaining) != 1 {
		t.Fatalf("expected 1 remaining version, got %d", len(remaining))
	}
}

func TestGarbageCollectorStartStop(t *testing.T) {
	s := store.NewStore()
	txMgr := transaction.NewTransactionManager()
	gc := NewGarbageCollector(s, txMgr, 10*time.Millisecond)

	gc.Start()

	// Add some data using the transaction manager
	txn1 := txMgr.Begin()
	s.Put("key1", []byte("v1"), txn1.ID, txn1.StartTimestamp)
	txMgr.Commit(txn1.ID)

	txn2 := txMgr.Begin()
	s.Put("key1", []byte("v2"), txn2.ID, txn2.StartTimestamp)
	txMgr.Commit(txn2.ID)

	// Wait for a few GC cycles
	time.Sleep(50 * time.Millisecond)

	gc.Stop()

	stats := gc.Stats()
	if stats.TotalRuns == 0 {
		t.Fatal("expected at least 1 GC run")
	}
}

func TestGarbageCollectorDeletedVersions(t *testing.T) {
	s := store.NewStore()
	txMgr := transaction.NewTransactionManager()
	gc := NewGarbageCollector(s, txMgr, time.Hour)

	// Create a version
	txn1 := txMgr.Begin()
	s.Put("key1", []byte("v1"), txn1.ID, txn1.StartTimestamp)
	txMgr.Commit(txn1.ID)

	// Delete the version
	txn2 := txMgr.Begin()
	s.Delete("key1", txn2.ID, txn2.StartTimestamp)
	txMgr.Commit(txn2.ID)

	// Start a new active transaction
	activeTxn := txMgr.Begin()

	// Run GC - the deleted version should be removed
	removed := gc.Run()

	if removed != 1 {
		t.Fatalf("expected 1 version removed, got %d", removed)
	}

	// The key should have no versions
	keys := s.Keys()
	if len(keys) != 0 {
		t.Fatalf("expected 0 keys, got %d", len(keys))
	}

	_ = activeTxn
}

func TestGarbageCollectorStats(t *testing.T) {
	s := store.NewStore()
	txMgr := transaction.NewTransactionManager()
	gc := NewGarbageCollector(s, txMgr, time.Hour)

	// Initial stats should be zero
	stats := gc.Stats()
	if stats.TotalRuns != 0 {
		t.Fatalf("expected 0 total runs, got %d", stats.TotalRuns)
	}

	// Run GC
	txn := txMgr.Begin()
	s.Put("key1", []byte("v1"), txn.ID, txn.StartTimestamp)
	txMgr.Commit(txn.ID)
	gc.Run()

	stats = gc.Stats()
	if stats.TotalRuns != 1 {
		t.Fatalf("expected 1 total run, got %d", stats.TotalRuns)
	}
	if stats.LastRunTime.IsZero() {
		t.Fatal("expected non-zero last run time")
	}
	if stats.LastRunDuration == 0 {
		t.Fatal("expected non-zero last run duration")
	}
}
