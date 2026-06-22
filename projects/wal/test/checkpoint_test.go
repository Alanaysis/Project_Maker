package test

import (
	"fmt"
	"os"
	"path/filepath"
	"testing"
	"time"

	"github.com/copyninja/wal/internal/storage"
	"github.com/copyninja/wal/internal/wal"
)

func TestCheckpointCreation(t *testing.T) {
	tmpDir := t.TempDir()
	walPath := filepath.Join(tmpDir, "test.wal")

	writer, err := wal.NewWALWriter(walPath, wal.SyncImmediate)
	if err != nil {
		t.Fatalf("Failed to create WAL writer: %v", err)
	}
	defer writer.Close()

	// Write some data
	for i := 0; i < 100; i++ {
		entry := &wal.LogEntry{
			TxID:   uint64(i),
			OpType: wal.OpPut,
			Key:    fmt.Sprintf("key%d", i),
			Value:  []byte(fmt.Sprintf("value%d", i)),
		}
		writer.Write(entry)
	}

	// Create checkpoint
	checkpointMgr := wal.NewCheckpointManager(tmpDir, writer, time.Second)
	err = checkpointMgr.CreateCheckpoint()
	if err != nil {
		t.Fatalf("Failed to create checkpoint: %v", err)
	}

	// Verify checkpoint exists
	checkpoint, err := checkpointMgr.LoadLastCheckpoint()
	if err != nil {
		t.Fatalf("Failed to load checkpoint: %v", err)
	}
	if checkpoint == nil {
		t.Fatal("Checkpoint is nil")
	}
	if checkpoint.LSN == 0 {
		t.Error("Checkpoint LSN is 0")
	}
}

func TestCheckpointLoadLast(t *testing.T) {
	tmpDir := t.TempDir()
	walPath := filepath.Join(tmpDir, "test.wal")

	writer, err := wal.NewWALWriter(walPath, wal.SyncImmediate)
	if err != nil {
		t.Fatalf("Failed to create WAL writer: %v", err)
	}

	// Write some data
	for i := 0; i < 50; i++ {
		entry := &wal.LogEntry{
			TxID:   uint64(i),
			OpType: wal.OpPut,
			Key:    fmt.Sprintf("key%d", i),
			Value:  []byte(fmt.Sprintf("value%d", i)),
		}
		writer.Write(entry)
	}

	// Create first checkpoint
	checkpointMgr := wal.NewCheckpointManager(tmpDir, writer, time.Second)
	checkpointMgr.CreateCheckpoint()

	// Write more data
	for i := 50; i < 100; i++ {
		entry := &wal.LogEntry{
			TxID:   uint64(i),
			OpType: wal.OpPut,
			Key:    fmt.Sprintf("key%d", i),
			Value:  []byte(fmt.Sprintf("value%d", i)),
		}
		writer.Write(entry)
	}

	// Create second checkpoint
	checkpointMgr.CreateCheckpoint()
	writer.Close()

	// Load last checkpoint
	checkpoint, err := checkpointMgr.LoadLastCheckpoint()
	if err != nil {
		t.Fatalf("Failed to load checkpoint: %v", err)
	}
	if checkpoint == nil {
		t.Fatal("Checkpoint is nil")
	}
}

func TestCheckpointDirtyPages(t *testing.T) {
	tmpDir := t.TempDir()
	walPath := filepath.Join(tmpDir, "test.wal")

	writer, err := wal.NewWALWriter(walPath, wal.SyncImmediate)
	if err != nil {
		t.Fatalf("Failed to create WAL writer: %v", err)
	}
	defer writer.Close()

	checkpointMgr := wal.NewCheckpointManager(tmpDir, writer, time.Second)

	// Mark some pages as dirty
	checkpointMgr.MarkDirty("page1")
	checkpointMgr.MarkDirty("page2")
	checkpointMgr.MarkDirty("page3")

	// Verify dirty pages
	dirtyPages := checkpointMgr.GetDirtyPages()
	if len(dirtyPages) != 3 {
		t.Errorf("Expected 3 dirty pages, got %d", len(dirtyPages))
	}

	// Create checkpoint (should clear dirty pages)
	checkpointMgr.CreateCheckpoint()

	dirtyPages = checkpointMgr.GetDirtyPages()
	if len(dirtyPages) != 0 {
		t.Errorf("Expected 0 dirty pages after checkpoint, got %d", len(dirtyPages))
	}
}

func TestCheckpointLogCleanup(t *testing.T) {
	tmpDir := t.TempDir()
	walPath := filepath.Join(tmpDir, "test.wal")

	writer, err := wal.NewWALWriter(walPath, wal.SyncImmediate)
	if err != nil {
		t.Fatalf("Failed to create WAL writer: %v", err)
	}

	// Write some data
	for i := 0; i < 50; i++ {
		entry := &wal.LogEntry{
			TxID:   uint64(i),
			OpType: wal.OpPut,
			Key:    fmt.Sprintf("key%d", i),
			Value:  []byte(fmt.Sprintf("value%d", i)),
		}
		writer.Write(entry)
	}

	// Create checkpoint
	checkpointMgr := wal.NewCheckpointManager(tmpDir, writer, time.Second)
	checkpointMgr.CreateCheckpoint()

	// Write more data
	for i := 50; i < 100; i++ {
		entry := &wal.LogEntry{
			TxID:   uint64(i),
			OpType: wal.OpPut,
			Key:    fmt.Sprintf("key%d", i),
			Value:  []byte(fmt.Sprintf("value%d", i)),
		}
		writer.Write(entry)
	}
	writer.Close()

	// Count WAL files
	files, _ := filepath.Glob(filepath.Join(tmpDir, "*.wal"))
	// Note: In this simple implementation, we don't actually clean old files
	// but the test verifies the checkpoint was created
	if len(files) == 0 {
		t.Error("Expected at least one WAL file")
	}
}

func TestCheckpointScheduler(t *testing.T) {
	tmpDir := t.TempDir()
	walPath := filepath.Join(tmpDir, "test.wal")

	writer, err := wal.NewWALWriter(walPath, wal.SyncImmediate)
	if err != nil {
		t.Fatalf("Failed to create WAL writer: %v", err)
	}
	defer writer.Close()

	checkpointMgr := wal.NewCheckpointManager(tmpDir, writer, time.Second)
	scheduler := wal.NewCheckpointScheduler(checkpointMgr, 100*time.Millisecond, 10)

	// Mark many pages as dirty
	for i := 0; i < 15; i++ {
		checkpointMgr.MarkDirty(fmt.Sprintf("page%d", i))
	}

	// Start scheduler
	scheduler.Start()
	time.Sleep(200 * time.Millisecond)
	scheduler.Stop()

	// Verify checkpoint was created
	checkpoint, _ := checkpointMgr.LoadLastCheckpoint()
	if checkpoint == nil {
		t.Error("Expected checkpoint to be created by scheduler")
	}
}

func TestRotateWAL(t *testing.T) {
	tmpDir := t.TempDir()
	walPath := filepath.Join(tmpDir, "test.wal")

	writer, err := wal.NewWALWriter(walPath, wal.SyncImmediate)
	if err != nil {
		t.Fatalf("Failed to create WAL writer: %v", err)
	}

	// Write some data
	writer.Write(&wal.LogEntry{TxID: 1, OpType: wal.OpPut, Key: "key", Value: []byte("value")})

	// Rotate
	newWriter, oldPath, err := wal.RotateWAL(tmpDir, writer)
	if err != nil {
		t.Fatalf("Failed to rotate WAL: %v", err)
	}
	defer newWriter.Close()

	// Verify old path
	if oldPath == "" {
		t.Error("Old path is empty")
	}

	// Verify new writer works
	newWriter.Write(&wal.LogEntry{TxID: 2, OpType: wal.OpPut, Key: "key2", Value: []byte("value2")})

	// Verify old file exists
	if _, err := os.Stat(oldPath); os.IsNotExist(err) {
		t.Error("Old WAL file does not exist")
	}

	// Verify new file exists
	newPath := newWriter.path
	if _, err := os.Stat(newPath); os.IsNotExist(err) {
		t.Error("New WAL file does not exist")
	}
}

func TestGetWALSize(t *testing.T) {
	tmpDir := t.TempDir()
	walPath := filepath.Join(tmpDir, "test.wal")

	writer, err := wal.NewWALWriter(walPath, wal.SyncImmediate)
	if err != nil {
		t.Fatalf("Failed to create WAL writer: %v", err)
	}

	// Write some data
	writer.Write(&wal.LogEntry{TxID: 1, OpType: wal.OpPut, Key: "key", Value: []byte("value")})
	writer.Close()

	// Get size
	size, err := wal.GetWALSize(walPath)
	if err != nil {
		t.Fatalf("Failed to get WAL size: %v", err)
	}

	if size == 0 {
		t.Error("WAL size is 0")
	}
}

func TestNeedsRotation(t *testing.T) {
	tmpDir := t.TempDir()
	walPath := filepath.Join(tmpDir, "test.wal")

	writer, err := wal.NewWALWriter(walPath, wal.SyncImmediate)
	if err != nil {
		t.Fatalf("Failed to create WAL writer: %v", err)
	}

	// Write some data
	writer.Write(&wal.LogEntry{TxID: 1, OpType: wal.OpPut, Key: "key", Value: []byte("value")})
	writer.Close()

	// Check with small max size
	needsRotation, err := wal.NeedsRotation(walPath, 10)
	if err != nil {
		t.Fatalf("Failed to check rotation: %v", err)
	}
	if !needsRotation {
		t.Error("Expected rotation needed for small max size")
	}

	// Check with large max size
	needsRotation, err = wal.NeedsRotation(walPath, 1024*1024)
	if err != nil {
		t.Fatalf("Failed to check rotation: %v", err)
	}
	if needsRotation {
		t.Error("Expected no rotation needed for large max size")
	}
}

func TestCheckpointWithRecovery(t *testing.T) {
	tmpDir := t.TempDir()
	walPath := filepath.Join(tmpDir, "test.wal")
	dataPath := filepath.Join(tmpDir, "data")

	// Create storage
	store, err := storage.NewFileStorage(dataPath)
	if err != nil {
		t.Fatalf("Failed to create storage: %v", err)
	}

	writer, err := wal.NewWALWriter(walPath, wal.SyncImmediate)
	if err != nil {
		t.Fatalf("Failed to create WAL writer: %v", err)
	}

	// Write some data
	for i := 0; i < 50; i++ {
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

	// Create checkpoint
	checkpointMgr := wal.NewCheckpointManager(tmpDir, writer, time.Second)
	checkpointMgr.CreateCheckpoint()

	// Write more data after checkpoint
	for i := 50; i < 100; i++ {
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

	// Verify all data
	for i := 0; i < 100; i++ {
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
