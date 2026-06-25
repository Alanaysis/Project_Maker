package main

import (
	"fmt"
	"log"
	"os"
	"path/filepath"
	"time"

	"github.com/copyninja/wal/internal/storage"
	"github.com/copyninja/wal/internal/wal"
)

func main() {
	log.Println("WAL Usage Example")
	log.Println("=================")

	// Create temporary directory
	tmpDir := filepath.Join(os.TempDir(), "wal-example")
	os.MkdirAll(tmpDir, 0755)
	defer os.RemoveAll(tmpDir)

	// Example 1: Basic WAL Operations
	log.Println("\n1. Basic WAL Operations")
	basicWALExample(tmpDir)

	// Example 2: Transaction Management
	log.Println("\n2. Transaction Management")
	transactionExample(tmpDir)

	// Example 3: Crash Recovery
	log.Println("\n3. Crash Recovery")
	crashRecoveryExample(tmpDir)

	// Example 4: Checkpoint Mechanism
	log.Println("\n4. Checkpoint Mechanism")
	checkpointExample(tmpDir)

	log.Println("\nExample complete!")
}

func basicWALExample(tmpDir string) {
	walPath := filepath.Join(tmpDir, "basic.wal")
	_ = filepath.Join(tmpDir, "storage") // storageDir for future use

	// Create WAL writer
	writer, err := wal.NewWALWriter(walPath, wal.SyncImmediate)
	if err != nil {
		log.Fatalf("Failed to create WAL writer: %v", err)
	}
	defer writer.Close()

	// Write some entries
	entries := []*wal.LogEntry{
		{TxID: 1, OpType: wal.OpPut, Key: "name", Value: []byte("Alice")},
		{TxID: 2, OpType: wal.OpPut, Key: "age", Value: []byte("30")},
		{TxID: 3, OpType: wal.OpPut, Key: "city", Value: []byte("Beijing")},
	}

	for _, entry := range entries {
		if err := writer.Write(entry); err != nil {
			log.Printf("Failed to write entry: %v", err)
			continue
		}
		log.Printf("  Wrote: LSN=%d, Key=%s", entry.LSN, entry.Key)
	}

	// Read all entries
	reader, err := wal.NewWALReader(walPath)
	if err != nil {
		log.Fatalf("Failed to create WAL reader: %v", err)
	}
	defer reader.Close()

	readEntries, err := reader.ReadAll()
	if err != nil {
		log.Fatalf("Failed to read entries: %v", err)
	}

	log.Printf("  Read %d entries from WAL", len(readEntries))
	for _, entry := range readEntries {
		log.Printf("    LSN=%d, Key=%s, Value=%s", entry.LSN, entry.Key, entry.Value)
	}
}

func transactionExample(tmpDir string) {
	walPath := filepath.Join(tmpDir, "transaction.wal")
	storageDir := filepath.Join(tmpDir, "storage")

	// Create storage
	store := storage.NewMemStorage()
	defer store.Close()

	// Create WAL writer
	writer, err := wal.NewWALWriter(walPath, wal.SyncImmediate)
	if err != nil {
		log.Fatalf("Failed to create WAL writer: %v", err)
	}
	defer writer.Close()

	// Transaction 1: Transfer money
	log.Println("  Transaction 1: Transfer $100 from Alice to Bob")

	// Alice's balance: 1000 -> 900
	writer.Write(&wal.LogEntry{TxID: 1, OpType: wal.OpPut, Key: "alice:balance", Value: []byte("900")})
	store.Put("alice:balance", []byte("900"))

	// Bob's balance: 500 -> 600
	writer.Write(&wal.LogEntry{TxID: 1, OpType: wal.OpPut, Key: "bob:balance", Value: []byte("600")})
	store.Put("bob:balance", []byte("600"))

	// Commit transaction
	writer.Write(&wal.LogEntry{TxID: 1, OpType: wal.OpCommit})
	log.Println("    Transaction 1 committed")

	// Transaction 2: Failed transaction (simulated crash)
	log.Println("  Transaction 2: Failed transaction (simulated crash)")

	writer.Write(&wal.LogEntry{TxID: 2, OpType: wal.OpPut, Key: "alice:balance", Value: []byte("800")})
	// Transaction 2 not committed (simulating crash)

	// Show current state
	aliceBalance, _ := store.Get("alice:balance")
	bobBalance, _ := store.Get("bob:balance")
	log.Printf("    Alice: %s, Bob: %s", aliceBalance, bobBalance)
}

func crashRecoveryExample(tmpDir string) {
	walPath := filepath.Join(tmpDir, "recovery.wal")
	storageDir := filepath.Join(tmpDir, "recovery-storage")

	// Create storage
	store, err := storage.NewMemStorage()
	if err != nil {
		log.Fatalf("Failed to create storage: %v", err)
	}

	// Simulate a crash scenario
	log.Println("  Simulating crash scenario...")

	// Write some entries without commit
	writer, err := wal.NewWALWriter(walPath, wal.SyncImmediate)
	if err != nil {
		log.Fatalf("Failed to create WAL writer: %v", err)
	}

	writer.Write(&wal.LogEntry{TxID: 1, OpType: wal.OpPut, Key: "key1", Value: []byte("value1")})
	writer.Write(&wal.LogEntry{TxID: 2, OpType: wal.OpPut, Key: "key2", Value: []byte("value2")})
	writer.Write(&wal.LogEntry{TxID: 1, OpType: wal.OpCommit}) // Only tx1 committed
	writer.Close()

	// Recover
	log.Println("  Performing recovery...")
	recovery := wal.NewRecoveryManager(walPath, store)
	if err := recovery.Recover(); err != nil {
		log.Fatalf("Failed to recover: %v", err)
	}

	// Show recovered state
	keys, _ := store.List()
	log.Printf("  Recovered %d keys:", len(keys))
	for _, key := range keys {
		value, _ := store.Get(key)
		log.Printf("    %s = %s", key, value)
	}

	// Verify uncommitted transaction was not applied
	_, err = store.Get("key2")
	if err != nil {
		log.Println("  ✓ Uncommitted transaction (key2) was correctly rolled back")
	} else {
		log.Println("  ✗ Uncommitted transaction (key2) was incorrectly applied")
	}
}

func checkpointExample(tmpDir string) {
	walPath := filepath.Join(tmpDir, "checkpoint.wal")
	storageDir := filepath.Join(tmpDir, "checkpoint-storage")

	// Create storage
	store, err := storage.NewMemStorage()
	if err != nil {
		log.Fatalf("Failed to create storage: %v", err)
	}

	// Create WAL writer
	writer, err := wal.NewWALWriter(walPath, wal.SyncImmediate)
	if err != nil {
		log.Fatalf("Failed to create WAL writer: %v", err)
	}
	defer writer.Close()

	// Create checkpoint manager
	checkpointMgr := wal.NewCheckpointManager(tmpDir, writer, time.Second)

	// Write some data
	log.Println("  Writing data...")
	for i := 0; i < 10; i++ {
		key := fmt.Sprintf("key:%d", i)
		value := fmt.Sprintf("value:%d", i)

		writer.Write(&wal.LogEntry{TxID: uint64(i), OpType: wal.OpPut, Key: key, Value: []byte(value)})
		writer.Write(&wal.LogEntry{TxID: uint64(i), OpType: wal.OpCommit})
		store.Put(key, []byte(value))
		checkpointMgr.MarkDirty(key)
	}

	// Create checkpoint
	log.Println("  Creating checkpoint...")
	if err := checkpointMgr.CreateCheckpoint(); err != nil {
		log.Printf("Failed to create checkpoint: %v", err)
	} else {
		log.Println("  ✓ Checkpoint created successfully")
	}

	// Load checkpoint
	checkpoint, err := checkpointMgr.LoadLastCheckpoint()
	if err != nil {
		log.Printf("Failed to load checkpoint: %v", err)
	} else if checkpoint != nil {
		log.Printf("  ✓ Loaded checkpoint at LSN: %d", checkpoint.LSN)
	}

	// Show dirty pages before checkpoint
	dirtyPages := checkpointMgr.GetDirtyPages()
	log.Printf("  Dirty pages before checkpoint: %d", len(dirtyPages))

	// Show dirty pages after checkpoint
	dirtyPages = checkpointMgr.GetDirtyPages()
	log.Printf("  Dirty pages after checkpoint: %d", len(dirtyPages))
}
