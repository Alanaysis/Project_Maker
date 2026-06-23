package test

import (
	"fmt"
	"sync"
	"testing"

	"mvcc/internal"
)

func TestMVSSEngineBasicReadWrite(t *testing.T) {
	engine := internal.NewMVSSEngine()

	// Begin transaction and write
	txn1 := engine.Begin()
	err := txn1.Write("key1", []byte("value1"))
	if err != nil {
		t.Fatalf("unexpected error writing: %v", err)
	}

	// Read within same transaction (read-your-own-writes)
	val, ok := txn1.Read("key1")
	if !ok || string(val) != "value1" {
		t.Fatalf("expected 'value1', got '%s', ok=%v", string(val), ok)
	}

	// Commit
	err = txn1.Commit()
	if err != nil {
		t.Fatalf("unexpected error committing: %v", err)
	}

	// Start new transaction and read committed value
	txn2 := engine.Begin()
	val, ok = txn2.Read("key1")
	if !ok || string(val) != "value1" {
		t.Fatalf("expected 'value1' in new txn, got '%s', ok=%v", string(val), ok)
	}
	txn2.Commit()
}

func TestMVSSEngineSnapshotIsolation(t *testing.T) {
	engine := internal.NewMVSSEngine()

	// Transaction 1 writes key1
	txn1 := engine.Begin()
	txn1.Write("key1", []byte("value1"))
	txn1.Commit()

	// Transaction 2 starts (snapshot at this point)
	txn2 := engine.Begin()

	// Transaction 3 starts and writes new value
	txn3 := engine.Begin()
	txn3.Write("key1", []byte("value2"))
	txn3.Commit()

	// Transaction 2 should still see old value (snapshot isolation)
	val, ok := txn2.Read("key1")
	if !ok || string(val) != "value1" {
		t.Fatalf("txn2 expected 'value1' (snapshot isolation), got '%s', ok=%v", string(val), ok)
	}

	// Transaction 4 starts after txn3 commit, should see new value
	txn4 := engine.Begin()
	val, ok = txn4.Read("key1")
	if !ok || string(val) != "value2" {
		t.Fatalf("txn4 expected 'value2', got '%s', ok=%v", string(val), ok)
	}

	txn2.Commit()
	txn4.Commit()
}

func TestMVSSEngineWriteWriteConflict(t *testing.T) {
	engine := internal.NewMVSSEngine()

	// Transaction 1 writes key1
	txn1 := engine.Begin()
	txn1.Write("key1", []byte("value1"))
	txn1.Commit()

	// Transaction 2 reads key1 (establishes read set)
	txn2 := engine.Begin()
	txn2.Read("key1")

	// Transaction 3 writes key1 (concurrent write)
	txn3 := engine.Begin()
	txn3.Write("key1", []byte("value3"))
	txn3.Commit()

	// Transaction 2 should fail to commit (write-write conflict)
	err := txn2.Write("key1", []byte("value2"))
	if err != nil {
		t.Fatalf("unexpected error writing: %v", err)
	}

	err = txn2.Commit()
	if err == nil {
		t.Fatal("expected write-write conflict error")
	}
}

func TestMVSSEngineReadYourOwnWrites(t *testing.T) {
	engine := internal.NewMVSSEngine()

	txn := engine.Begin()

	// Write multiple values
	txn.Write("key1", []byte("v1"))
	txn.Write("key2", []byte("v2"))

	// Read should see own writes
	val, ok := txn.Read("key1")
	if !ok || string(val) != "v1" {
		t.Fatalf("expected 'v1', got '%s'", string(val))
	}

	val, ok = txn.Read("key2")
	if !ok || string(val) != "v2" {
		t.Fatalf("expected 'v2', got '%s'", string(val))
	}

	// Overwrite and read again
	txn.Write("key1", []byte("v1_updated"))
	val, ok = txn.Read("key1")
	if !ok || string(val) != "v1_updated" {
		t.Fatalf("expected 'v1_updated', got '%s'", string(val))
	}

	txn.Commit()
}

func TestMVSSEngineDelete(t *testing.T) {
	engine := internal.NewMVSSEngine()

	// Write a value
	txn1 := engine.Begin()
	txn1.Write("key1", []byte("value1"))
	txn1.Commit()

	// Delete the value
	txn2 := engine.Begin()
	txn2.Delete("key1")
	txn2.Commit()

	// Should not be visible in new transaction
	txn3 := engine.Begin()
	_, ok := txn3.Read("key1")
	if ok {
		t.Fatal("expected key1 to be deleted")
	}
	txn3.Commit()
}

func TestMVSSEngineDeleteSnapshotIsolation(t *testing.T) {
	engine := internal.NewMVSSEngine()

	// Write a value
	txn1 := engine.Begin()
	txn1.Write("key1", []byte("value1"))
	txn1.Commit()

	// Transaction 2 starts (snapshot before delete)
	txn2 := engine.Begin()

	// Transaction 3 deletes key1
	txn3 := engine.Begin()
	txn3.Delete("key1")
	txn3.Commit()

	// Transaction 2 should still see the value
	val, ok := txn2.Read("key1")
	if !ok || string(val) != "value1" {
		t.Fatalf("txn2 expected 'value1' (snapshot), got ok=%v", ok)
	}
	txn2.Commit()
}

func TestMVSSEngineAbort(t *testing.T) {
	engine := internal.NewMVSSEngine()

	txn := engine.Begin()
	txn.Write("key1", []byte("value1"))
	txn.Abort()

	// Aborted transaction's writes should not be visible
	txn2 := engine.Begin()
	_, ok := txn2.Read("key1")
	if ok {
		t.Fatal("expected aborted write to not be visible")
	}
	txn2.Commit()
}

func TestMVSSEngineConcurrentTransactions(t *testing.T) {
	engine := internal.NewMVSSEngine()

	// Write initial values
	txn := engine.Begin()
	for i := 0; i < 10; i++ {
		key := fmt.Sprintf("key%d", i)
		txn.Write(key, []byte(fmt.Sprintf("initial%d", i)))
	}
	txn.Commit()

	// Concurrent reads and writes
	var wg sync.WaitGroup
	for i := 0; i < 50; i++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			txn := engine.Begin()

			// Read a key
			key := fmt.Sprintf("key%d", id%10)
			txn.Read(key)

			// Write to a unique key
			writeKey := fmt.Sprintf("unique_%d", id)
			txn.Write(writeKey, []byte(fmt.Sprintf("value_%d", id)))

			txn.Commit()
		}(i)
	}
	wg.Wait()

	// Verify unique keys were written
	txn2 := engine.Begin()
	for i := 0; i < 50; i++ {
		key := fmt.Sprintf("unique_%d", i)
		_, ok := txn2.Read(key)
		if !ok {
			t.Fatalf("expected to find %s", key)
		}
	}
	txn2.Commit()
}

func TestMVSSEngineReadWriteSkew(t *testing.T) {
	engine := internal.NewMVSSEngine()

	// Initial state: key1=100, key2=200
	txn0 := engine.Begin()
	txn0.Write("key1", []byte("100"))
	txn0.Write("key2", []byte("200"))
	txn0.Commit()

	// Transaction A reads key1 and key2
	txnA := engine.Begin()
	valA1, _ := txnA.Read("key1")
	valA2, _ := txnA.Read("key2")
	t.Logf("TxnA reads: key1=%s, key2=%s", string(valA1), string(valA2))

	// Transaction B updates key1 and key2
	txnB := engine.Begin()
	txnB.Write("key1", []byte("150"))
	txnB.Write("key2", []byte("150"))
	txnB.Commit()

	// Transaction A should still see consistent snapshot
	valA1Again, _ := txnA.Read("key1")
	valA2Again, _ := txnA.Read("key2")
	if string(valA1Again) != "100" || string(valA2Again) != "200" {
		t.Fatalf("TxnA should see consistent snapshot: key1=%s, key2=%s", string(valA1Again), string(valA2Again))
	}

	txnA.Commit()
}

func TestMVSSEngineMultipleKeys(t *testing.T) {
	engine := internal.NewMVSSEngine()

	// Write to multiple keys
	txn1 := engine.Begin()
	data := map[string]string{
		"name":  "Alice",
		"age":   "30",
		"email": "alice@example.com",
	}
	for k, v := range data {
		txn1.Write(k, []byte(v))
	}
	txn1.Commit()

	// Read all keys in new transaction
	txn2 := engine.Begin()
	for k, v := range data {
		val, ok := txn2.Read(k)
		if !ok || string(val) != v {
			t.Fatalf("expected %s=%s, got ok=%v", k, v, ok)
		}
	}
	txn2.Commit()
}

func TestMVSSEngineUpdateOverwrite(t *testing.T) {
	engine := internal.NewMVSSEngine()

	// Write initial value
	txn1 := engine.Begin()
	txn1.Write("counter", []byte("0"))
	txn1.Commit()

	// Update multiple times
	for i := 1; i <= 5; i++ {
		txn := engine.Begin()
		txn.Write("counter", []byte(fmt.Sprintf("%d", i)))
		txn.Commit()
	}

	// Should see latest value
	txn := engine.Begin()
	val, ok := txn.Read("counter")
	if !ok || string(val) != "5" {
		t.Fatalf("expected '5', got '%s'", string(val))
	}
	txn.Commit()
}

func TestMVSSEngineVersionHistory(t *testing.T) {
	engine := internal.NewMVSSEngine()

	// Create multiple versions
	for i := 1; i <= 5; i++ {
		txn := engine.Begin()
		txn.Write("key1", []byte(fmt.Sprintf("v%d", i)))
		txn.Commit()
	}

	// Check version count
	store := engine.Store()
	versions := store.AllVersions("key1")
	if len(versions) != 5 {
		t.Fatalf("expected 5 versions, got %d", len(versions))
	}

	// Verify each version is visible at its creation time
	for i, v := range versions {
		expected := fmt.Sprintf("v%d", i+1)
		if string(v.Value) != expected {
			t.Fatalf("version %d: expected '%s', got '%s'", i, expected, string(v.Value))
		}
	}
}

func TestMVSSEngineTransactionIsolation(t *testing.T) {
	engine := internal.NewMVSSEngine()

	// Two transactions start concurrently
	txn1 := engine.Begin()
	txn2 := engine.Begin()

	// Both write to the same key
	txn1.Write("shared", []byte("from_txn1"))
	txn2.Write("shared", []byte("from_txn2"))

	// Commit txn1 first
	err := txn1.Commit()
	if err != nil {
		t.Fatalf("txn1 commit failed: %v", err)
	}

	// txn2 should fail due to conflict
	err = txn2.Commit()
	if err == nil {
		t.Fatal("expected txn2 to fail with conflict")
	}
}

func TestMVSSEngineIsolationLevelSummary(t *testing.T) {
	engine := internal.NewMVSSEngine()

	t.Log("=== MVCC Snapshot Isolation Demo ===")

	// Initial data
	txn := engine.Begin()
	txn.Write("x", []byte("100"))
	txn.Write("y", []byte("200"))
	txn.Commit()

	// T1 starts (snapshot at ts=2)
	t1 := engine.Begin()
	t.Logf("T1 started at ts=%d", t1.StartTimestamp())

	// T2 starts and modifies x
	t2 := engine.Begin()
	t2.Write("x", []byte("150"))
	t2.Commit()
	t.Log("T2 committed: x=150")

	// T1 reads x - should see old value
	val, _ := t1.Read("x")
	t.Logf("T1 reads x=%s (snapshot isolation: sees old value)", string(val))

	// T3 starts and modifies y
	t3 := engine.Begin()
	t3.Write("y", []byte("250"))
	t3.Commit()
	t.Log("T3 committed: y=250")

	// T1 reads y - should see old value
	val, _ = t1.Read("y")
	t.Logf("T1 reads y=%s (snapshot isolation: sees old value)", string(val))

	t1.Commit()
	t.Log("T1 committed successfully (consistent snapshot)")
}
