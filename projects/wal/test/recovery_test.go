package test

import (
	"fmt"
	"os"
	"path/filepath"
	"testing"

	"github.com/copyninja/wal/internal/storage"
	"github.com/copyninja/wal/internal/wal"
)

func TestRecoveryNormal(t *testing.T) {
	tmpDir := t.TempDir()
	walPath := filepath.Join(tmpDir, "test.wal")
	dataPath := filepath.Join(tmpDir, "data")

	// Create storage
	store, err := storage.NewFileStorage(dataPath)
	if err != nil {
		t.Fatalf("Failed to create storage: %v", err)
	}

	// Write some entries
	writer, err := wal.NewWALWriter(walPath, wal.SyncImmediate)
	if err != nil {
		t.Fatalf("Failed to create WAL writer: %v", err)
	}

	// Write put entries
	entry1 := &wal.LogEntry{TxID: 1, OpType: wal.OpPut, Key: "key1", Value: []byte("value1")}
	entry2 := &wal.LogEntry{TxID: 1, OpType: wal.OpPut, Key: "key2", Value: []byte("value2")}

	writer.Write(entry1)
	writer.Write(entry2)

	// Commit transaction
	commitEntry := &wal.LogEntry{TxID: 1, OpType: wal.OpCommit}
	writer.Write(commitEntry)
	writer.Close()

	// Recover
	recovery := wal.NewRecoveryManager(walPath, store)
	err = recovery.Recover()
	if err != nil {
		t.Fatalf("Failed to recover: %v", err)
	}

	// Verify data
	value, err := store.Get("key1")
	if err != nil {
		t.Fatalf("Failed to get key1: %v", err)
	}
	if string(value) != "value1" {
		t.Errorf("Expected value1, got %s", value)
	}

	value, err = store.Get("key2")
	if err != nil {
		t.Fatalf("Failed to get key2: %v", err)
	}
	if string(value) != "value2" {
		t.Errorf("Expected value2, got %s", value)
	}
}

func TestRecoveryCrash(t *testing.T) {
	tmpDir := t.TempDir()
	walPath := filepath.Join(tmpDir, "test.wal")
	dataPath := filepath.Join(tmpDir, "data")

	// Create storage
	store, err := storage.NewFileStorage(dataPath)
	if err != nil {
		t.Fatalf("Failed to create storage: %v", err)
	}

	// Write entries without commit (simulating crash)
	writer, err := wal.NewWALWriter(walPath, wal.SyncImmediate)
	if err != nil {
		t.Fatalf("Failed to create WAL writer: %v", err)
	}

	entry1 := &wal.LogEntry{TxID: 1, OpType: wal.OpPut, Key: "key1", Value: []byte("value1")}
	writer.Write(entry1)

	// Simulate crash: close without commit
	writer.Close()

	// Recover
	recovery := wal.NewRecoveryManager(walPath, store)
	err = recovery.Recover()
	if err != nil {
		t.Fatalf("Failed to recover: %v", err)
	}

	// Verify data is not present (transaction not committed)
	_, err = store.Get("key1")
	if err == nil {
		t.Error("Expected key1 to not exist (transaction not committed)")
	}
}

func TestRecoveryMultipleTransactions(t *testing.T) {
	tmpDir := t.TempDir()
	walPath := filepath.Join(tmpDir, "test.wal")
	dataPath := filepath.Join(tmpDir, "data")

	// Create storage
	store, err := storage.NewFileStorage(dataPath)
	if err != nil {
		t.Fatalf("Failed to create storage: %v", err)
	}

	// Write multiple transactions
	writer, err := wal.NewWALWriter(walPath, wal.SyncImmediate)
	if err != nil {
		t.Fatalf("Failed to create WAL writer: %v", err)
	}

	// Transaction 1 (committed)
	writer.Write(&wal.LogEntry{TxID: 1, OpType: wal.OpPut, Key: "key1", Value: []byte("value1")})
	writer.Write(&wal.LogEntry{TxID: 1, OpType: wal.OpCommit})

	// Transaction 2 (not committed - crash)
	writer.Write(&wal.LogEntry{TxID: 2, OpType: wal.OpPut, Key: "key2", Value: []byte("value2")})

	// Transaction 3 (committed)
	writer.Write(&wal.LogEntry{TxID: 3, OpType: wal.OpPut, Key: "key3", Value: []byte("value3")})
	writer.Write(&wal.LogEntry{TxID: 3, OpType: wal.OpCommit})

	writer.Close()

	// Recover
	recovery := wal.NewRecoveryManager(walPath, store)
	err = recovery.Recover()
	if err != nil {
		t.Fatalf("Failed to recover: %v", err)
	}

	// Verify committed transactions
	value, err := store.Get("key1")
	if err != nil {
		t.Fatalf("Failed to get key1: %v", err)
	}
	if string(value) != "value1" {
		t.Errorf("Expected value1, got %s", value)
	}

	value, err = store.Get("key3")
	if err != nil {
		t.Fatalf("Failed to get key3: %v", err)
	}
	if string(value) != "value3" {
		t.Errorf("Expected value3, got %s", value)
	}

	// Verify uncommitted transaction
	_, err = store.Get("key2")
	if err == nil {
		t.Error("Expected key2 to not exist (transaction not committed)")
	}
}

func TestRecoveryDeleteOperation(t *testing.T) {
	tmpDir := t.TempDir()
	walPath := filepath.Join(tmpDir, "test.wal")
	dataPath := filepath.Join(tmpDir, "data")

	// Create storage and populate it
	store, err := storage.NewFileStorage(dataPath)
	if err != nil {
		t.Fatalf("Failed to create storage: %v", err)
	}

	// Pre-populate storage
	store.Put("key1", []byte("old-value"))

	// Write delete operation
	writer, err := wal.NewWALWriter(walPath, wal.SyncImmediate)
	if err != nil {
		t.Fatalf("Failed to create WAL writer: %v", err)
	}

	writer.Write(&wal.LogEntry{TxID: 1, OpType: wal.OpDelete, Key: "key1"})
	writer.Write(&wal.LogEntry{TxID: 1, OpType: wal.OpCommit})
	writer.Close()

	// Recover
	recovery := wal.NewRecoveryManager(walPath, store)
	err = recovery.Recover()
	if err != nil {
		t.Fatalf("Failed to recover: %v", err)
	}

	// Verify key is deleted
	_, err = store.Get("key1")
	if err == nil {
		t.Error("Expected key1 to be deleted")
	}
}

func TestRecoveryMultipleOperations(t *testing.T) {
	tmpDir := t.TempDir()
	walPath := filepath.Join(tmpDir, "test.wal")
	dataPath := filepath.Join(tmpDir, "data")

	// Create storage
	store, err := storage.NewFileStorage(dataPath)
	if err != nil {
		t.Fatalf("Failed to create storage: %v", err)
	}

	// Write multiple operations in one transaction
	writer, err := wal.NewWALWriter(walPath, wal.SyncImmediate)
	if err != nil {
		t.Fatalf("Failed to create WAL writer: %v", err)
	}

	// Put key1
	writer.Write(&wal.LogEntry{TxID: 1, OpType: wal.OpPut, Key: "key1", Value: []byte("value1")})
	// Put key2
	writer.Write(&wal.LogEntry{TxID: 1, OpType: wal.OpPut, Key: "key2", Value: []byte("value2")})
	// Update key1
	writer.Write(&wal.LogEntry{TxID: 1, OpType: wal.OpPut, Key: "key1", Value: []byte("value1-updated")})
	// Commit
	writer.Write(&wal.LogEntry{TxID: 1, OpType: wal.OpCommit})
	writer.Close()

	// Recover
	recovery := wal.NewRecoveryManager(walPath, store)
	err = recovery.Recover()
	if err != nil {
		t.Fatalf("Failed to recover: %v", err)
	}

	// Verify final state
	value, err := store.Get("key1")
	if err != nil {
		t.Fatalf("Failed to get key1: %v", err)
	}
	if string(value) != "value1-updated" {
		t.Errorf("Expected value1-updated, got %s", value)
	}

	value, err = store.Get("key2")
	if err != nil {
		t.Fatalf("Failed to get key2: %v", err)
	}
	if string(value) != "value2" {
		t.Errorf("Expected value2, got %s", value)
	}
}

func TestRecoveryLargeDataset(t *testing.T) {
	tmpDir := t.TempDir()
	walPath := filepath.Join(tmpDir, "test.wal")
	dataPath := filepath.Join(tmpDir, "data")

	// Create storage
	store, err := storage.NewFileStorage(dataPath)
	if err != nil {
		t.Fatalf("Failed to create storage: %v", err)
	}

	// Write many entries
	writer, err := wal.NewWALWriter(walPath, wal.SyncImmediate)
	if err != nil {
		t.Fatalf("Failed to create WAL writer: %v", err)
	}

	numEntries := 1000
	for i := 0; i < numEntries; i++ {
		writer.Write(&wal.LogEntry{
			TxID:   uint64(i),
			OpType: wal.OpPut,
			Key:    fmt.Sprintf("key%d", i),
			Value:  []byte(fmt.Sprintf("value%d", i)),
		})
		writer.Write(&wal.LogEntry{
			TxID:   uint64(i),
			OpType: wal.OpCommit,
		})
	}
	writer.Close()

	// Recover
	recovery := wal.NewRecoveryManager(walPath, store)
	err = recovery.Recover()
	if err != nil {
		t.Fatalf("Failed to recover: %v", err)
	}

	// Verify all entries
	for i := 0; i < numEntries; i++ {
		key := fmt.Sprintf("key%d", i)
		expectedValue := fmt.Sprintf("value%d", i)

		value, err := store.Get(key)
		if err != nil {
			t.Fatalf("Failed to get %s: %v", key, err)
		}
		if string(value) != expectedValue {
			t.Errorf("Expected %s, got %s", expectedValue, value)
		}
	}
}

func TestValidateWAL(t *testing.T) {
	tmpDir := t.TempDir()
	walPath := filepath.Join(tmpDir, "test.wal")

	// Create a valid WAL file
	writer, err := wal.NewWALWriter(walPath, wal.SyncImmediate)
	if err != nil {
		t.Fatalf("Failed to create WAL writer: %v", err)
	}

	writer.Write(&wal.LogEntry{TxID: 1, OpType: wal.OpPut, Key: "key", Value: []byte("value")})
	writer.Close()

	// Validate
	err = wal.ValidateWAL(walPath)
	if err != nil {
		t.Fatalf("WAL validation failed: %v", err)
	}
}

func TestValidateWALCorrupted(t *testing.T) {
	tmpDir := t.TempDir()
	walPath := filepath.Join(tmpDir, "test.wal")

	// Create a WAL file
	writer, err := wal.NewWALWriter(walPath, wal.SyncImmediate)
	if err != nil {
		t.Fatalf("Failed to create WAL writer: %v", err)
	}

	writer.Write(&wal.LogEntry{TxID: 1, OpType: wal.OpPut, Key: "key", Value: []byte("value")})
	writer.Close()

	// Corrupt the file
	data, err := os.ReadFile(walPath)
	if err != nil {
		t.Fatalf("Failed to read WAL file: %v", err)
	}

	// Corrupt some bytes in the middle
	if len(data) > 20 {
		data[20] ^= 0xFF
	}

	err = os.WriteFile(walPath, data, 0644)
	if err != nil {
		t.Fatalf("Failed to write corrupted WAL file: %v", err)
	}

	// Validate should fail
	err = wal.ValidateWAL(walPath)
	if err == nil {
		t.Error("Expected validation to fail for corrupted WAL")
	}
}

func TestListWALFiles(t *testing.T) {
	tmpDir := t.TempDir()

	// Create multiple WAL files
	for i := 0; i < 5; i++ {
		walPath := filepath.Join(tmpDir, fmt.Sprintf("wal.%d.wal", i))
		writer, err := wal.NewWALWriter(walPath, wal.SyncImmediate)
		if err != nil {
			t.Fatalf("Failed to create WAL writer: %v", err)
		}
		writer.Write(&wal.LogEntry{TxID: uint64(i), OpType: wal.OpPut, Key: "key", Value: []byte("value")})
		writer.Close()
	}

	// List files
	files, err := wal.ListWALFiles(tmpDir)
	if err != nil {
		t.Fatalf("Failed to list WAL files: %v", err)
	}

	if len(files) != 5 {
		t.Errorf("Expected 5 WAL files, got %d", len(files))
	}
}
