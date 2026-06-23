package transaction

import (
	"sync"
	"testing"
)

func TestTransactionManagerBegin(t *testing.T) {
	tm := NewTransactionManager()

	txn := tm.Begin()
	if txn == nil {
		t.Fatal("expected non-nil transaction")
	}
	if txn.Status != TxnActive {
		t.Fatalf("expected status Active, got %s", txn.Status)
	}
	if txn.ID == 0 {
		t.Fatal("expected non-zero transaction ID")
	}
	if txn.StartTimestamp == 0 {
		t.Fatal("expected non-zero start timestamp")
	}
}

func TestTransactionManagerMultipleTransactions(t *testing.T) {
	tm := NewTransactionManager()

	txn1 := tm.Begin()
	txn2 := tm.Begin()

	if txn1.ID == txn2.ID {
		t.Fatal("expected different transaction IDs")
	}
	if tm.ActiveCount() != 2 {
		t.Fatalf("expected 2 active transactions, got %d", tm.ActiveCount())
	}
}

func TestTransactionManagerCommit(t *testing.T) {
	tm := NewTransactionManager()

	txn := tm.Begin()
	txnID := txn.ID

	commitTS, err := tm.Commit(txnID)
	if err != nil {
		t.Fatalf("unexpected error committing: %v", err)
	}
	if commitTS <= txn.StartTimestamp {
		t.Fatalf("commit timestamp (%d) should be > start timestamp (%d)", commitTS, txn.StartTimestamp)
	}
	if txn.Status != TxnCommitted {
		t.Fatalf("expected status Committed, got %s", txn.Status)
	}
	if tm.ActiveCount() != 0 {
		t.Fatalf("expected 0 active transactions, got %d", tm.ActiveCount())
	}
}

func TestTransactionManagerAbort(t *testing.T) {
	tm := NewTransactionManager()

	txn := tm.Begin()
	txnID := txn.ID

	err := tm.Abort(txnID)
	if err != nil {
		t.Fatalf("unexpected error aborting: %v", err)
	}
	if txn.Status != TxnAborted {
		t.Fatalf("expected status Aborted, got %s", txn.Status)
	}
	if tm.ActiveCount() != 0 {
		t.Fatalf("expected 0 active transactions, got %d", tm.ActiveCount())
	}
}

func TestTransactionManagerCommitNonExistent(t *testing.T) {
	tm := NewTransactionManager()

	_, err := tm.Commit(999)
	if err == nil {
		t.Fatal("expected error committing non-existent transaction")
	}
}

func TestTransactionManagerAbortNonExistent(t *testing.T) {
	tm := NewTransactionManager()

	err := tm.Abort(999)
	if err == nil {
		t.Fatal("expected error aborting non-existent transaction")
	}
}

func TestTransactionManagerActiveTransactions(t *testing.T) {
	tm := NewTransactionManager()

	txn1 := tm.Begin()
	txn2 := tm.Begin()
	tm.Begin() // txn3

	active := tm.ActiveTransactions()
	if len(active) != 3 {
		t.Fatalf("expected 3 active transactions, got %d", len(active))
	}

	tm.Commit(txn1.ID)
	tm.Abort(txn2.ID)

	active = tm.ActiveTransactions()
	if len(active) != 1 {
		t.Fatalf("expected 1 active transaction, got %d", len(active))
	}
}

func TestTransactionManagerMinActiveTimestamp(t *testing.T) {
	tm := NewTransactionManager()

	txn1 := tm.Begin()
	txn2 := tm.Begin()

	minTS := tm.MinActiveTimestamp()
	if minTS != txn1.StartTimestamp {
		t.Fatalf("expected min active TS %d, got %d", txn1.StartTimestamp, minTS)
	}

	// Commit the first transaction
	tm.Commit(txn1.ID)

	minTS = tm.MinActiveTimestamp()
	if minTS != txn2.StartTimestamp {
		t.Fatalf("expected min active TS %d, got %d", txn2.StartTimestamp, minTS)
	}

	// Abort the second transaction
	tm.Abort(txn2.ID)

	// No active transactions - minTS should be current clock
	minTS = tm.MinActiveTimestamp()
	if minTS == 0 {
		t.Fatal("expected non-zero min active TS when no active transactions")
	}
}

func TestTransactionManagerGetTransaction(t *testing.T) {
	tm := NewTransactionManager()

	txn := tm.Begin()
	txnID := txn.ID

	// Should find active transaction
	found, ok := tm.GetTransaction(txnID)
	if !ok || found.ID != txnID {
		t.Fatal("expected to find active transaction")
	}

	// Commit and find committed transaction
	tm.Commit(txnID)
	found, ok = tm.GetTransaction(txnID)
	if !ok || found.ID != txnID {
		t.Fatal("expected to find committed transaction")
	}
}

func TestTransactionAddReadAndWrite(t *testing.T) {
	txn := NewTransaction(1, 1)

	txn.AddRead("key1", 1)
	if _, ok := txn.ReadSet["key1"]; !ok {
		t.Fatal("expected key1 in read set")
	}

	txn.AddWrite("key1", []byte("value1"))
	if wr, ok := txn.WriteSet["key1"]; !ok {
		t.Fatal("expected key1 in write set")
	} else if string(wr.Value) != "value1" {
		t.Fatalf("expected 'value1', got '%s'", string(wr.Value))
	}
}

func TestTransactionAddDelete(t *testing.T) {
	txn := NewTransaction(1, 1)

	txn.AddDelete("key1")
	if wr, ok := txn.WriteSet["key1"]; !ok {
		t.Fatal("expected key1 in write set")
	} else if !wr.IsDelete {
		t.Fatal("expected IsDelete to be true")
	}
}

func TestTransactionConcurrentAccess(t *testing.T) {
	tm := NewTransactionManager()

	var wg sync.WaitGroup
	for i := 0; i < 100; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			txn := tm.Begin()
			txn.AddRead("key", 1)
			txn.AddWrite("key", []byte("value"))
			tm.Commit(txn.ID)
		}()
	}
	wg.Wait()

	if tm.ActiveCount() != 0 {
		t.Fatalf("expected 0 active transactions, got %d", tm.ActiveCount())
	}
}
