package test

import (
	"fmt"
	"os"
	"path/filepath"
	"testing"
	"time"

	"github.com/copyninja/wal/internal/wal"
)

func TestRetentionPolicyDefaults(t *testing.T) {
	policy := wal.DefaultRetentionPolicy()

	if policy.MaxSize != 1024*1024*1024 {
		t.Errorf("Expected MaxSize 1GB, got %d", policy.MaxSize)
	}
	if policy.MaxAge != 7*24*time.Hour {
		t.Errorf("Expected MaxAge 7 days, got %v", policy.MaxAge)
	}
	if policy.MaxFiles != 10 {
		t.Errorf("Expected MaxFiles 10, got %d", policy.MaxFiles)
	}
	if policy.MinFiles != 2 {
		t.Errorf("Expected MinFiles 2, got %d", policy.MinFiles)
	}
}

func TestLogCleanerFileCount(t *testing.T) {
	tmpDir := t.TempDir()

	// Create multiple WAL files
	for i := 0; i < 5; i++ {
		walPath := filepath.Join(tmpDir, fmt.Sprintf("wal.%d.wal", i))
		writer, err := wal.NewWALWriter(walPath, wal.SyncImmediate)
		if err != nil {
			t.Fatalf("Failed to create WAL writer: %v", err)
		}
		writer.Write(&wal.LogEntry{
			TxID:   uint64(i),
			OpType: wal.OpPut,
			Key:    fmt.Sprintf("key%d", i),
			Value:  []byte(fmt.Sprintf("value%d", i)),
		})
		writer.Close()
	}

	// Create cleaner with max 3 files
	policy := &wal.RetentionPolicy{
		MaxFiles: 3,
		MinFiles: 1,
	}
	cleaner := wal.NewLogCleaner(tmpDir, policy, time.Hour)

	// Run cleanup
	err := cleaner.Cleanup()
	if err != nil {
		t.Fatalf("Failed to cleanup: %v", err)
	}

	// Verify file count
	count, err := cleaner.GetFileCount()
	if err != nil {
		t.Fatalf("Failed to get file count: %v", err)
	}

	if count > 3 {
		t.Errorf("Expected at most 3 files, got %d", count)
	}
}

func TestLogCleanerMinFiles(t *testing.T) {
	tmpDir := t.TempDir()

	// Create multiple WAL files
	for i := 0; i < 5; i++ {
		walPath := filepath.Join(tmpDir, fmt.Sprintf("wal.%d.wal", i))
		writer, err := wal.NewWALWriter(walPath, wal.SyncImmediate)
		if err != nil {
			t.Fatalf("Failed to create WAL writer: %v", err)
		}
		writer.Write(&wal.LogEntry{
			TxID:   uint64(i),
			OpType: wal.OpPut,
			Key:    fmt.Sprintf("key%d", i),
			Value:  []byte(fmt.Sprintf("value%d", i)),
		})
		writer.Close()
	}

	// Create cleaner with max 2 files but min 3 files
	policy := &wal.RetentionPolicy{
		MaxFiles: 2,
		MinFiles: 3,
	}
	cleaner := wal.NewLogCleaner(tmpDir, policy, time.Hour)

	// Run cleanup
	err := cleaner.Cleanup()
	if err != nil {
		t.Fatalf("Failed to cleanup: %v", err)
	}

	// Verify file count respects min files
	count, err := cleaner.GetFileCount()
	if err != nil {
		t.Fatalf("Failed to get file count: %v", err)
	}

	if count < 3 {
		t.Errorf("Expected at least 3 files (min files), got %d", count)
	}
}

func TestLogCleanerSizeBased(t *testing.T) {
	tmpDir := t.TempDir()

	// Create WAL files with known sizes
	for i := 0; i < 5; i++ {
		walPath := filepath.Join(tmpDir, fmt.Sprintf("wal.%d.wal", i))
		writer, err := wal.NewWALWriter(walPath, wal.SyncImmediate)
		if err != nil {
			t.Fatalf("Failed to create WAL writer: %v", err)
		}
		// Write some data to make file larger
		for j := 0; j < 100; j++ {
			writer.Write(&wal.LogEntry{
				TxID:   uint64(i*100 + j),
				OpType: wal.OpPut,
				Key:    fmt.Sprintf("key-%d-%d", i, j),
				Value:  []byte(fmt.Sprintf("value-%d-%d", i, j)),
			})
		}
		writer.Close()
	}

	// Get total size before cleanup
	cleaner := wal.NewLogCleaner(tmpDir, nil, time.Hour)
	totalSizeBefore, _ := cleaner.GetTotalSize()

	// Create cleaner with small max size
	policy := &wal.RetentionPolicy{
		MaxSize:  totalSizeBefore / 2, // Half of current size
		MinFiles: 1,
	}
	cleaner = wal.NewLogCleaner(tmpDir, policy, time.Hour)

	// Run cleanup
	err := cleaner.Cleanup()
	if err != nil {
		t.Fatalf("Failed to cleanup: %v", err)
	}

	// Verify size is reduced
	totalSizeAfter, _ := cleaner.GetTotalSize()
	if totalSizeAfter >= totalSizeBefore {
		t.Errorf("Expected size to decrease: before=%d, after=%d", totalSizeBefore, totalSizeAfter)
	}
}

func TestTruncateWAL(t *testing.T) {
	tmpDir := t.TempDir()
	walPath := filepath.Join(tmpDir, "test.wal")

	// Create WAL with multiple entries
	writer, err := wal.NewWALWriter(walPath, wal.SyncImmediate)
	if err != nil {
		t.Fatalf("Failed to create WAL writer: %v", err)
	}

	// Write 10 entries
	for i := 0; i < 10; i++ {
		writer.Write(&wal.LogEntry{
			TxID:   uint64(i),
			OpType: wal.OpPut,
			Key:    fmt.Sprintf("key%d", i),
			Value:  []byte(fmt.Sprintf("value%d", i)),
		})
	}
	writer.Close()

	// Truncate at LSN 5
	err = wal.TruncateWAL(walPath, 5)
	if err != nil {
		t.Fatalf("Failed to truncate WAL: %v", err)
	}

	// Read remaining entries
	reader, err := wal.NewWALReader(walPath)
	if err != nil {
		t.Fatalf("Failed to create WAL reader: %v", err)
	}
	defer reader.Close()

	entries, err := reader.ReadAll()
	if err != nil {
		t.Fatalf("Failed to read entries: %v", err)
	}

	// Should have 5 entries (LSN 1-5)
	if len(entries) != 5 {
		t.Errorf("Expected 5 entries after truncation, got %d", len(entries))
	}

	// Verify all entries have LSN <= 5
	for _, entry := range entries {
		if entry.LSN > 5 {
			t.Errorf("Found entry with LSN %d after truncation at 5", entry.LSN)
		}
	}
}

func TestTruncateWALAfterTime(t *testing.T) {
	tmpDir := t.TempDir()
	walPath := filepath.Join(tmpDir, "test.wal")

	// Create WAL with entries at different times
	writer, err := wal.NewWALWriter(walPath, wal.SyncImmediate)
	if err != nil {
		t.Fatalf("Failed to create WAL writer: %v", err)
	}

	// Write entries with timestamps
	baseTime := time.Now()
	for i := 0; i < 10; i++ {
		entry := &wal.LogEntry{
			TxID:      uint64(i),
			OpType:    wal.OpPut,
			Key:       fmt.Sprintf("key%d", i),
			Value:     []byte(fmt.Sprintf("value%d", i)),
			Timestamp: baseTime.Add(time.Duration(i) * time.Minute).UnixNano(),
		}
		writer.Write(entry)
	}
	writer.Close()

	// Truncate after 5 minutes
	truncateTime := baseTime.Add(5 * time.Minute)
	err = wal.TruncateWALAfterTime(walPath, truncateTime)
	if err != nil {
		t.Fatalf("Failed to truncate WAL: %v", err)
	}

	// Read remaining entries
	reader, err := wal.NewWALReader(walPath)
	if err != nil {
		t.Fatalf("Failed to create WAL reader: %v", err)
	}
	defer reader.Close()

	entries, err := reader.ReadAll()
	if err != nil {
		t.Fatalf("Failed to read entries: %v", err)
	}

	// Should have entries with timestamps <= truncateTime
	if len(entries) == 0 {
		t.Error("Expected some entries after truncation")
	}

	for _, entry := range entries {
		entryTime := time.Unix(0, entry.Timestamp)
		if entryTime.After(truncateTime) {
			t.Errorf("Found entry with timestamp %v after truncation time %v",
				entryTime, truncateTime)
		}
	}
}

func TestGetWALStats(t *testing.T) {
	tmpDir := t.TempDir()
	walPath := filepath.Join(tmpDir, "test.wal")

	// Create WAL with various operations
	writer, err := wal.NewWALWriter(walPath, wal.SyncImmediate)
	if err != nil {
		t.Fatalf("Failed to create WAL writer: %v", err)
	}

	// Write different types of entries
	writer.Write(&wal.LogEntry{TxID: 1, OpType: wal.OpPut, Key: "key1", Value: []byte("value1")})
	writer.Write(&wal.LogEntry{TxID: 2, OpType: wal.OpPut, Key: "key2", Value: []byte("value2")})
	writer.Write(&wal.LogEntry{TxID: 3, OpType: wal.OpDelete, Key: "key1"})
	writer.Write(&wal.LogEntry{TxID: 1, OpType: wal.OpCommit})
	writer.Write(&wal.LogEntry{TxID: 2, OpType: wal.OpCommit})
	writer.Write(&wal.LogEntry{TxID: 3, OpType: wal.OpCommit})
	writer.Close()

	// Get stats
	stats, err := wal.GetWALStats(walPath)
	if err != nil {
		t.Fatalf("Failed to get WAL stats: %v", err)
	}

	// Verify stats
	if stats.TotalEntries != 6 {
		t.Errorf("Expected 6 total entries, got %d", stats.TotalEntries)
	}
	if stats.PutOperations != 2 {
		t.Errorf("Expected 2 put operations, got %d", stats.PutOperations)
	}
	if stats.DeleteOperations != 1 {
		t.Errorf("Expected 1 delete operation, got %d", stats.DeleteOperations)
	}
	if stats.Commits != 3 {
		t.Errorf("Expected 3 commits, got %d", stats.Commits)
	}
	if stats.MaxLSN != 6 {
		t.Errorf("Expected max LSN 6, got %d", stats.MaxLSN)
	}
	if stats.FileSize == 0 {
		t.Error("Expected non-zero file size")
	}
}

func TestWALStatsString(t *testing.T) {
	stats := &wal.WALStats{
		Path:             "/tmp/test.wal",
		FileSize:         1024,
		TotalEntries:     10,
		CorruptedEntries: 0,
		PutOperations:    5,
		DeleteOperations: 2,
		Commits:          3,
		Rollbacks:        0,
		Checkpoints:      0,
		MaxLSN:           10,
		OldestEntry:      time.Now().Add(-time.Hour),
		NewestEntry:      time.Now(),
	}

	str := stats.String()
	if str == "" {
		t.Error("Expected non-empty string representation")
	}
}

func TestLogCleanerGetTotalSize(t *testing.T) {
	tmpDir := t.TempDir()

	// Create WAL files
	for i := 0; i < 3; i++ {
		walPath := filepath.Join(tmpDir, fmt.Sprintf("wal.%d.wal", i))
		writer, err := wal.NewWALWriter(walPath, wal.SyncImmediate)
		if err != nil {
			t.Fatalf("Failed to create WAL writer: %v", err)
		}
		writer.Write(&wal.LogEntry{
			TxID:   uint64(i),
			OpType: wal.OpPut,
			Key:    fmt.Sprintf("key%d", i),
			Value:  []byte(fmt.Sprintf("value%d", i)),
		})
		writer.Close()
	}

	cleaner := wal.NewLogCleaner(tmpDir, nil, time.Hour)

	totalSize, err := cleaner.GetTotalSize()
	if err != nil {
		t.Fatalf("Failed to get total size: %v", err)
	}

	if totalSize == 0 {
		t.Error("Expected non-zero total size")
	}
}

func TestLogCleanerGetFileCount(t *testing.T) {
	tmpDir := t.TempDir()

	// Create WAL files
	for i := 0; i < 5; i++ {
		walPath := filepath.Join(tmpDir, fmt.Sprintf("wal.%d.wal", i))
		writer, err := wal.NewWALWriter(walPath, wal.SyncImmediate)
		if err != nil {
			t.Fatalf("Failed to create WAL writer: %v", err)
		}
		writer.Write(&wal.LogEntry{
			TxID:   uint64(i),
			OpType: wal.OpPut,
			Key:    fmt.Sprintf("key%d", i),
			Value:  []byte(fmt.Sprintf("value%d", i)),
		})
		writer.Close()
	}

	cleaner := wal.NewLogCleaner(tmpDir, nil, time.Hour)

	count, err := cleaner.GetFileCount()
	if err != nil {
		t.Fatalf("Failed to get file count: %v", err)
	}

	if count != 5 {
		t.Errorf("Expected 5 files, got %d", count)
	}
}

func TestLogCleanerEmptyDirectory(t *testing.T) {
	tmpDir := t.TempDir()

	policy := &wal.RetentionPolicy{
		MaxFiles: 3,
		MinFiles: 1,
	}
	cleaner := wal.NewLogCleaner(tmpDir, policy, time.Hour)

	// Should not error on empty directory
	err := cleaner.Cleanup()
	if err != nil {
		t.Fatalf("Failed to cleanup empty directory: %v", err)
	}

	count, err := cleaner.GetFileCount()
	if err != nil {
		t.Fatalf("Failed to get file count: %v", err)
	}

	if count != 0 {
		t.Errorf("Expected 0 files in empty directory, got %d", count)
	}
}

func TestLogCleanerWithNonWALFiles(t *testing.T) {
	tmpDir := t.TempDir()

	// Create WAL files
	for i := 0; i < 3; i++ {
		walPath := filepath.Join(tmpDir, fmt.Sprintf("wal.%d.wal", i))
		writer, err := wal.NewWALWriter(walPath, wal.SyncImmediate)
		if err != nil {
			t.Fatalf("Failed to create WAL writer: %v", err)
		}
		writer.Write(&wal.LogEntry{
			TxID:   uint64(i),
			OpType: wal.OpPut,
			Key:    fmt.Sprintf("key%d", i),
			Value:  []byte(fmt.Sprintf("value%d", i)),
		})
		writer.Close()
	}

	// Create non-WAL files
	os.WriteFile(filepath.Join(tmpDir, "data.txt"), []byte("test"), 0644)
	os.WriteFile(filepath.Join(tmpDir, "config.json"), []byte("{}"), 0644)

	policy := &wal.RetentionPolicy{
		MaxFiles: 2,
		MinFiles: 1,
	}
	cleaner := wal.NewLogCleaner(tmpDir, policy, time.Hour)

	// Run cleanup
	err := cleaner.Cleanup()
	if err != nil {
		t.Fatalf("Failed to cleanup: %v", err)
	}

	// Verify non-WAL files are not affected
	if _, err := os.Stat(filepath.Join(tmpDir, "data.txt")); os.IsNotExist(err) {
		t.Error("Non-WAL file data.txt was deleted")
	}
	if _, err := os.Stat(filepath.Join(tmpDir, "config.json")); os.IsNotExist(err) {
		t.Error("Non-WAL file config.json was deleted")
	}
}
