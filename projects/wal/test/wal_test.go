package test

import (
	"fmt"
	"os"
	"path/filepath"
	"sync"
	"testing"

	"github.com/copyninja/wal/internal/wal"
)

func TestLogEntrySerialization(t *testing.T) {
	entry := &wal.LogEntry{
		LSN:       1,
		TxID:      100,
		OpType:    wal.OpPut,
		Key:       "test-key",
		Value:     []byte("test-value"),
		Timestamp: 1234567890,
	}

	// Serialize
	data, err := entry.Serialize()
	if err != nil {
		t.Fatalf("Failed to serialize entry: %v", err)
	}

	if len(data) == 0 {
		t.Fatal("Serialized data is empty")
	}

	// Deserialize
	decoded, err := wal.DeserializeLogEntry(data)
	if err != nil {
		t.Fatalf("Failed to deserialize entry: %v", err)
	}

	// Verify fields
	if decoded.LSN != entry.LSN {
		t.Errorf("LSN mismatch: got %d, want %d", decoded.LSN, entry.LSN)
	}
	if decoded.TxID != entry.TxID {
		t.Errorf("TxID mismatch: got %d, want %d", decoded.TxID, entry.TxID)
	}
	if decoded.OpType != entry.OpType {
		t.Errorf("OpType mismatch: got %d, want %d", decoded.OpType, entry.OpType)
	}
	if decoded.Key != entry.Key {
		t.Errorf("Key mismatch: got %s, want %s", decoded.Key, entry.Key)
	}
	if string(decoded.Value) != string(entry.Value) {
		t.Errorf("Value mismatch: got %s, want %s", decoded.Value, entry.Value)
	}
}

func TestLogEntryChecksumValidation(t *testing.T) {
	entry := &wal.LogEntry{
		LSN:       1,
		TxID:      100,
		OpType:    wal.OpPut,
		Key:       "test-key",
		Value:     []byte("test-value"),
		Timestamp: 1234567890,
	}

	data, err := entry.Serialize()
	if err != nil {
		t.Fatalf("Failed to serialize entry: %v", err)
	}

	// Corrupt the data
	corruptedData := make([]byte, len(data))
	copy(corruptedData, data)
	corruptedData[10] ^= 0xFF // Flip one bit

	// Should fail with checksum error
	_, err = wal.DeserializeLogEntry(corruptedData)
	if err == nil {
		t.Fatal("Expected checksum error, got nil")
	}
}

func TestWALWriterBasicWrite(t *testing.T) {
	tmpDir := t.TempDir()
	walPath := filepath.Join(tmpDir, "test.wal")

	writer, err := wal.NewWALWriter(walPath, wal.SyncImmediate)
	if err != nil {
		t.Fatalf("Failed to create WAL writer: %v", err)
	}
	defer writer.Close()

	entry := &wal.LogEntry{
		TxID:      1,
		OpType:    wal.OpPut,
		Key:       "key1",
		Value:     []byte("value1"),
		Timestamp: 1234567890,
	}

	err = writer.Write(entry)
	if err != nil {
		t.Fatalf("Failed to write entry: %v", err)
	}

	// Verify file exists
	if _, err := os.Stat(walPath); os.IsNotExist(err) {
		t.Fatal("WAL file does not exist")
	}

	// Verify LSN is assigned
	if entry.LSN == 0 {
		t.Fatal("LSN was not assigned")
	}
}

func TestWALWriterBatchWrite(t *testing.T) {
	tmpDir := t.TempDir()
	walPath := filepath.Join(tmpDir, "test.wal")

	writer, err := wal.NewWALWriter(walPath, wal.SyncImmediate)
	if err != nil {
		t.Fatalf("Failed to create WAL writer: %v", err)
	}
	defer writer.Close()

	entries := make([]*wal.LogEntry, 100)
	for i := 0; i < 100; i++ {
		entries[i] = &wal.LogEntry{
			TxID:      uint64(i),
			OpType:    wal.OpPut,
			Key:       fmt.Sprintf("key%d", i),
			Value:     []byte(fmt.Sprintf("value%d", i)),
			Timestamp: int64(i),
		}
	}

	err = writer.WriteBatch(entries)
	if err != nil {
		t.Fatalf("Failed to write batch: %v", err)
	}

	// Verify LSNs are assigned and increasing
	for i := 1; i < len(entries); i++ {
		if entries[i].LSN <= entries[i-1].LSN {
			t.Errorf("LSN not increasing: entry[%d].LSN=%d, entry[%d].LSN=%d",
				i, entries[i].LSN, i-1, entries[i-1].LSN)
		}
	}
}

func TestWALWriterConcurrentWrite(t *testing.T) {
	tmpDir := t.TempDir()
	walPath := filepath.Join(tmpDir, "test.wal")

	writer, err := wal.NewWALWriter(walPath, wal.SyncImmediate)
	if err != nil {
		t.Fatalf("Failed to create WAL writer: %v", err)
	}
	defer writer.Close()

	var wg sync.WaitGroup
	for i := 0; i < 10; i++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			for j := 0; j < 100; j++ {
				entry := &wal.LogEntry{
					TxID:      uint64(id*100 + j),
					OpType:    wal.OpPut,
					Key:       fmt.Sprintf("key-%d-%d", id, j),
					Value:     []byte(fmt.Sprintf("value-%d-%d", id, j)),
					Timestamp: int64(id*100 + j),
				}
				err := writer.Write(entry)
				if err != nil {
					t.Errorf("Failed to write entry: %v", err)
				}
			}
		}(i)
	}

	wg.Wait()

	// Read all entries
	reader, err := wal.NewWALReader(walPath)
	if err != nil {
		t.Fatalf("Failed to create WAL reader: %v", err)
	}
	defer reader.Close()

	entries, err := reader.ReadAll()
	if err != nil {
		t.Fatalf("Failed to read entries: %v", err)
	}

	if len(entries) != 1000 {
		t.Errorf("Expected 1000 entries, got %d", len(entries))
	}
}

func TestWALReaderBasicRead(t *testing.T) {
	tmpDir := t.TempDir()
	walPath := filepath.Join(tmpDir, "test.wal")

	// Write entries
	writer, err := wal.NewWALWriter(walPath, wal.SyncImmediate)
	if err != nil {
		t.Fatalf("Failed to create WAL writer: %v", err)
	}

	entry := &wal.LogEntry{
		TxID:      1,
		OpType:    wal.OpPut,
		Key:       "test-key",
		Value:     []byte("test-value"),
		Timestamp: 1234567890,
	}

	err = writer.Write(entry)
	if err != nil {
		t.Fatalf("Failed to write entry: %v", err)
	}
	writer.Close()

	// Read entries
	reader, err := wal.NewWALReader(walPath)
	if err != nil {
		t.Fatalf("Failed to create WAL reader: %v", err)
	}
	defer reader.Close()

	entries, err := reader.ReadAll()
	if err != nil {
		t.Fatalf("Failed to read entries: %v", err)
	}

	if len(entries) != 1 {
		t.Fatalf("Expected 1 entry, got %d", len(entries))
	}

	if entries[0].Key != "test-key" {
		t.Errorf("Key mismatch: got %s, want test-key", entries[0].Key)
	}
	if string(entries[0].Value) != "test-value" {
		t.Errorf("Value mismatch: got %s, want test-value", entries[0].Value)
	}
}

func TestWALReaderReadByLSN(t *testing.T) {
	tmpDir := t.TempDir()
	walPath := filepath.Join(tmpDir, "test.wal")

	// Write multiple entries
	writer, err := wal.NewWALWriter(walPath, wal.SyncImmediate)
	if err != nil {
		t.Fatalf("Failed to create WAL writer: %v", err)
	}

	entries := make([]*wal.LogEntry, 10)
	for i := 0; i < 10; i++ {
		entries[i] = &wal.LogEntry{
			TxID:      uint64(i),
			OpType:    wal.OpPut,
			Key:       fmt.Sprintf("key%d", i),
			Value:     []byte(fmt.Sprintf("value%d", i)),
			Timestamp: int64(i),
		}
		err = writer.Write(entries[i])
		if err != nil {
			t.Fatalf("Failed to write entry: %v", err)
		}
	}
	writer.Close()

	// Read specific entry
	reader, err := wal.NewWALReader(walPath)
	if err != nil {
		t.Fatalf("Failed to create WAL reader: %v", err)
	}
	defer reader.Close()

	entry, err := reader.ReadByLSN(5)
	if err != nil {
		t.Fatalf("Failed to read entry by LSN: %v", err)
	}

	if entry.LSN != 5 {
		t.Errorf("LSN mismatch: got %d, want 5", entry.LSN)
	}
}

func TestWALWriterSyncModes(t *testing.T) {
	tmpDir := t.TempDir()

	tests := []struct {
		name      string
		syncMode  wal.SyncMode
	}{
		{"SyncImmediate", wal.SyncImmediate},
		{"SyncBatch", wal.SyncBatch},
		{"SyncNone", wal.SyncNone},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			walPath := filepath.Join(tmpDir, tt.name+".wal")

			writer, err := wal.NewWALWriter(walPath, tt.syncMode)
			if err != nil {
				t.Fatalf("Failed to create WAL writer: %v", err)
			}
			defer writer.Close()

			entry := &wal.LogEntry{
				TxID:      1,
				OpType:    wal.OpPut,
				Key:       "key",
				Value:     []byte("value"),
				Timestamp: 1234567890,
			}

			err = writer.Write(entry)
			if err != nil {
				t.Fatalf("Failed to write entry: %v", err)
			}
		})
	}
}
