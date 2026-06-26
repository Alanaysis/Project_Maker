package mvcc

import (
	"testing"
)

// TestSnapshotManager tests the SnapshotManager's transaction lifecycle.
func TestSnapshotManagerBasic(t *testing.T) {
	storage := NewMVCCStorage()
	sm := NewSnapshotManager(storage)

	// Begin a transaction
	tx := sm.BeginTransaction()
	if tx.ID != 1 {
		t.Errorf("expected transaction ID 1, got %d", tx.ID)
	}
	if tx.State != StateSnapshotRead {
		t.Errorf("expected StateSnapshotRead, got %v", tx.State)
	}
	if tx.ReadTimestamp == 0 {
		t.Error("expected non-zero ReadTimestamp")
	}

	// Begin another transaction
	tx2 := sm.BeginTransaction()
	if tx2.ID != 2 {
		t.Errorf("expected transaction ID 2, got %d", tx2.ID)
	}
	if tx2.ReadTimestamp <= tx.ReadTimestamp {
		t.Error("second transaction should have later ReadTimestamp")
	}
}

// TestSnapshotManagerWriteRead tests write and read operations.
func TestSnapshotManagerWriteRead(t *testing.T) {
	storage := NewMVCCStorage()
	sm := NewSnapshotManager(storage)

	// Initialize data
	storage.Write("key1", []byte("initial"), 0, 0)

	// Begin transaction
	tx := sm.BeginTransaction()

	// Read
	val, err := sm.Read(tx, "key1")
	if err != nil {
		t.Errorf("unexpected error: %v", err)
	}
	if string(val) != "initial" {
		t.Errorf("expected 'initial', got %q", string(val))
	}

	// Write (buffered)
	sm.Write(tx, "key1", []byte("modified"))

	// Read again - should still see original (snapshot isolation)
	val, err = sm.Read(tx, "key1")
	if err != nil {
		t.Errorf("unexpected error: %v", err)
	}
	if string(val) != "initial" {
		t.Errorf("expected 'initial' (snapshot), got %q", string(val))
	}
}

// TestSnapshotManagerCommit tests transaction commit.
func TestSnapshotManagerCommit(t *testing.T) {
	storage := NewMVCCStorage()
	sm := NewSnapshotManager(storage)

	// Initialize
	storage.Write("key1", []byte("initial"), 0, 0)

	tx := sm.BeginTransaction()
	sm.Write(tx, "key1", []byte("modified"))

	err := sm.CommitTransaction(tx, NewConflictDetector())
	if err != nil {
		t.Errorf("commit should succeed: %v", err)
	}

	if tx.State != StateCommitted {
		t.Errorf("expected StateCommitted, got %v", tx.State)
	}

	// Verify the write is visible
	val, exists, _ := storage.Read("key1", tx.CommitTime)
	if !exists {
		t.Error("committed write should be visible")
	}
	if string(val) != "modified" {
		t.Errorf("expected 'modified', got %q", string(val))
	}
}

// TestSnapshotManagerRollback tests transaction rollback.
func TestSnapshotManagerRollback(t *testing.T) {
	storage := NewMVCCStorage()
	sm := NewSnapshotManager(storage)

	// Initialize
	storage.Write("key1", []byte("initial"), 0, 0)

	tx := sm.BeginTransaction()
	sm.Write(tx, "key1", []byte("modified"))

	// Rollback
	sm.RollbackTransaction(tx)

	if tx.State != StateAborted {
		t.Errorf("expected StateAborted, got %v", tx.State)
	}

	// Verify the write is NOT visible
	val, exists, _ := storage.Read("key1", tx.ReadTimestamp)
	if exists {
		t.Error("rolled-back write should not be visible")
	}
	if string(val) != "initial" {
		t.Errorf("expected 'initial', got %q", string(val))
	}
}

// TestSnapshotManagerActiveTransactions tests ActiveTransactions.
func TestSnapshotManagerActiveTransactions(t *testing.T) {
	storage := NewMVCCStorage()
	sm := NewSnapshotManager(storage)

	tx1 := sm.BeginTransaction()
	tx2 := sm.BeginTransaction()

	active := sm.ActiveTransactions()
	if len(active) != 2 {
		t.Errorf("expected 2 active transactions, got %d", len(active))
	}

	// Commit tx1
	sm.CommitTransaction(tx1, NewConflictDetector())
	active = sm.ActiveTransactions()
	if len(active) != 1 {
		t.Errorf("expected 1 active transaction after commit, got %d", len(active))
	}

	// Rollback tx2
	sm.RollbackTransaction(tx2)
	active = sm.ActiveTransactions()
	if len(active) != 0 {
		t.Errorf("expected 0 active transactions after rollback, got %d", len(active))
	}
}

// TestSnapshotManagerReadAbortedTx tests reading with an aborted transaction.
func TestSnapshotManagerReadAbortedTx(t *testing.T) {
	storage := NewMVCCStorage()
	sm := NewSnapshotManager(storage)

	tx := sm.BeginTransaction()
	sm.RollbackTransaction(tx)

	_, err := sm.Read(tx, "key1")
	if err == nil {
		t.Error("expected error when reading with aborted transaction")
	}
}

// TestSnapshotManagerCommitAbortedTx tests committing an aborted transaction.
func TestSnapshotManagerCommitAbortedTx(t *testing.T) {
	storage := NewMVCCStorage()
	sm := NewSnapshotManager(storage)

	tx := sm.BeginTransaction()
	sm.RollbackTransaction(tx)

	err := sm.CommitTransaction(tx, NewConflictDetector())
	if err == nil {
		t.Error("expected error when committing aborted transaction")
	}
}

// TestSnapshotManagerMultipleWrites tests multiple writes in one transaction.
func TestSnapshotManagerMultipleWrites(t *testing.T) {
	storage := NewMVCCStorage()
	sm := NewSnapshotManager(storage)

	tx := sm.BeginTransaction()

	sm.Write(tx, "key1", []byte("val1"))
	sm.Write(tx, "key2", []byte("val2"))
	sm.Write(tx, "key3", []byte("val3"))

	writeSet := tx.GetWriteSet()
	if len(writeSet) != 3 {
		t.Errorf("expected 3 writes in write set, got %d", len(writeSet))
	}

	err := sm.CommitTransaction(tx, NewConflictDetector())
	if err != nil {
		t.Errorf("commit should succeed: %v", err)
	}

	// Verify all writes are visible
	for _, key := range []string{"key1", "key2", "key3"} {
		val, exists, _ := storage.Read(key, tx.CommitTime)
		if !exists {
			t.Errorf("key %s should be visible after commit", key)
		}
		_ = val
	}
}

// TestSnapshotManagerSnapshotIsolation tests that concurrent reads see consistent snapshots.
func TestSnapshotManagerSnapshotIsolation(t *testing.T) {
	storage := NewMVCCStorage()
	sm := NewSnapshotManager(storage)

	// Initialize
	storage.Write("counter", []byte("0"), 0, 0)

	// Start multiple transactions with the same snapshot
	tx1 := sm.BeginTransaction()
	tx2 := sm.BeginTransaction()
	tx3 := sm.BeginTransaction()

	// All should see the same value
	val1, _ := sm.Read(tx1, "counter")
	val2, _ := sm.Read(tx2, "counter")
	val3, _ := sm.Read(tx3, "counter")

	if string(val1) != "0" || string(val2) != "0" || string(val3) != "0" {
		t.Error("all transactions should see the same initial value")
	}

	// Each writes independently
	sm.Write(tx1, "counter", []byte("1"))
	sm.Write(tx2, "counter", []byte("2"))
	sm.Write(tx3, "counter", []byte("3"))

	// Commit tx1
	sm.CommitTransaction(tx1, NewConflictDetector())

	// tx2 and tx3 should still see the same snapshot
	val2After, _ := sm.Read(tx2, "counter")
	if string(val2After) != "0" {
		t.Error("tx2 should still see original snapshot value")
	}
}

// TestSnapshotManagerTimestampProgression tests timestamp progression.
func TestSnapshotManagerTimestampProgression(t *testing.T) {
	storage := NewMVCCStorage()
	sm := NewSnapshotManager(storage)

	var prevTS Timestamp
	for i := 0; i < 10; i++ {
		tx := sm.BeginTransaction()
		if tx.ReadTimestamp <= prevTS {
			t.Errorf("ReadTimestamp should increase: %d <= %d", tx.ReadTimestamp, prevTS)
		}
		prevTS = tx.ReadTimestamp
		sm.RollbackTransaction(tx)
	}
}

// TestTransactionManager tests the high-level TransactionManager API.
func TestTransactionManager(t *testing.T) {
	storage := NewMVCCStorage()
	tm := NewTransactionManager(storage)

	// Initialize
	storage.Write("key1", []byte("initial"), 0, 0)

	// Use the high-level API
	tx := tm.Begin()
	val, err := tm.Read(tx, "key1")
	if err != nil {
		t.Errorf("unexpected error: %v", err)
	}
	if string(val) != "initial" {
		t.Errorf("expected 'initial', got %q", string(val))
	}

	tm.Write(tx, "key1", []byte("modified"))
	err = tm.Commit(tx)
	if err != nil {
		t.Errorf("commit should succeed: %v", err)
	}

	// Verify
	val, err = tm.Read(tm.Begin(), "key1")
	if err != nil {
		t.Errorf("unexpected error: %v", err)
	}
	if string(val) != "modified" {
		t.Errorf("expected 'modified', got %q", string(val))
	}
}

// TestTransactionManagerRollback tests rollback via high-level API.
func TestTransactionManagerRollback(t *testing.T) {
	storage := NewMVCCStorage()
	tm := NewTransactionManager(storage)

	storage.Write("key1", []byte("initial"), 0, 0)

	tx := tm.Begin()
	tm.Write(tx, "key1", []byte("modified"))
	tm.Rollback(tx)

	val, _ := tm.Read(tm.Begin(), "key1")
	if string(val) != "initial" {
		t.Errorf("expected 'initial' after rollback, got %q", string(val))
	}
}
