package main

import (
	"fmt"
	"log"
	"os"
	"os/signal"
	"path/filepath"
	"syscall"
	"time"

	"github.com/copyninja/wal/internal/storage"
	"github.com/copyninja/wal/internal/wal"
)

func main() {
	log.Println("Starting WAL Server...")

	// Setup directories
	dataDir := filepath.Join(".", "data")
	walDir := filepath.Join(dataDir, "wal")
	storageDir := filepath.Join(dataDir, "storage")

	// Create directories
	os.MkdirAll(walDir, 0755)
	os.MkdirAll(storageDir, 0755)

	// Initialize storage
	store, err := storage.NewFileStorage(storageDir)
	if err != nil {
		log.Fatalf("Failed to initialize storage: %v", err)
	}
	defer store.Close()

	// Initialize WAL
	walPath := filepath.Join(walDir, "wal.current.wal")
	writer, err := wal.NewWALWriter(walPath, wal.SyncImmediate)
	if err != nil {
		log.Fatalf("Failed to initialize WAL: %v", err)
	}
	defer writer.Close()

	// Initialize checkpoint manager
	checkpointMgr := wal.NewCheckpointManager(walDir, writer, 30*time.Second)
	checkpointMgr.StartPeriodicCheckpoint()
	defer checkpointMgr.Stop()

	// Perform crash recovery
	log.Println("Performing crash recovery...")
	recovery := wal.NewRecoveryManager(walPath, store)
	if err := recovery.Recover(); err != nil {
		log.Printf("Warning: recovery had issues: %v", err)
	}
	log.Println("Recovery complete")

	// Demo operations
	log.Println("Starting demo operations...")
	demoOperations(writer, store, checkpointMgr)

	// Wait for interrupt signal
	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)

	log.Println("WAL Server is running. Press Ctrl+C to stop.")
	<-sigCh

	log.Println("Shutting down WAL Server...")
}

func demoOperations(writer *wal.WALWriter, store storage.Storage, checkpointMgr *wal.CheckpointManager) {
	// Demo 1: Put operations
	log.Println("Demo 1: Put operations")
	for i := 0; i < 10; i++ {
		key := fmt.Sprintf("user:%d", i)
		value := fmt.Sprintf("User %d data", i)

		// Write to WAL
		entry := &wal.LogEntry{
			TxID:   uint64(i + 1),
			OpType: wal.OpPut,
			Key:    key,
			Value:  []byte(value),
		}
		if err := writer.Write(entry); err != nil {
			log.Printf("Failed to write WAL entry: %v", err)
			continue
		}

		// Commit
		commitEntry := &wal.LogEntry{
			TxID:   uint64(i + 1),
			OpType: wal.OpCommit,
		}
		if err := writer.Write(commitEntry); err != nil {
			log.Printf("Failed to write commit entry: %v", err)
			continue
		}

		// Update storage
		if err := store.Put(key, []byte(value)); err != nil {
			log.Printf("Failed to update storage: %v", err)
			continue
		}

		// Mark dirty
		checkpointMgr.MarkDirty(key)

		log.Printf("  Put: %s = %s", key, value)
	}

	// Demo 2: Get operations
	log.Println("Demo 2: Get operations")
	for i := 0; i < 5; i++ {
		key := fmt.Sprintf("user:%d", i)
		value, err := store.Get(key)
		if err != nil {
			log.Printf("Failed to get %s: %v", key, err)
			continue
		}
		log.Printf("  Get: %s = %s", key, value)
	}

	// Demo 3: Delete operations
	log.Println("Demo 3: Delete operations")
	for i := 8; i < 10; i++ {
		key := fmt.Sprintf("user:%d", i)

		// Write to WAL
		entry := &wal.LogEntry{
			TxID:   uint64(i + 100),
			OpType: wal.OpDelete,
			Key:    key,
		}
		if err := writer.Write(entry); err != nil {
			log.Printf("Failed to write WAL entry: %v", err)
			continue
		}

		// Commit
		commitEntry := &wal.LogEntry{
			TxID:   uint64(i + 100),
			OpType: wal.OpCommit,
		}
		if err := writer.Write(commitEntry); err != nil {
			log.Printf("Failed to write commit entry: %v", err)
			continue
		}

		// Update storage
		if err := store.Delete(key); err != nil {
			log.Printf("Failed to delete from storage: %v", err)
			continue
		}

		log.Printf("  Delete: %s", key)
	}

	// Demo 4: Create checkpoint
	log.Println("Demo 4: Create checkpoint")
	if err := checkpointMgr.CreateCheckpoint(); err != nil {
		log.Printf("Failed to create checkpoint: %v", err)
	} else {
		log.Println("  Checkpoint created successfully")
	}

	// Demo 5: List all keys
	log.Println("Demo 5: List all keys")
	keys, err := store.List()
	if err != nil {
		log.Printf("Failed to list keys: %v", err)
	} else {
		for _, key := range keys {
			log.Printf("  Key: %s", key)
		}
	}

	log.Println("Demo complete!")
}
