package test

import (
	"os"
	"path/filepath"
	"testing"

	lsm "github.com/lsm-tree/internal"
)

func TestWALWriteAndReplay(t *testing.T) {
	dir := t.TempDir()
	walPath := filepath.Join(dir, "test.wal")

	// Write records
	wal, err := lsm.NewWAL(walPath)
	if err != nil {
		t.Fatalf("Failed to create WAL: %v", err)
	}

	if err := wal.WritePut([]byte("key1"), []byte("value1")); err != nil {
		t.Fatalf("WritePut failed: %v", err)
	}
	if err := wal.WritePut([]byte("key2"), []byte("value2")); err != nil {
		t.Fatalf("WritePut failed: %v", err)
	}
	if err := wal.WriteDelete([]byte("key1")); err != nil {
		t.Fatalf("WriteDelete failed: %v", err)
	}
	if err := wal.Sync(); err != nil {
		t.Fatalf("Sync failed: %v", err)
	}
	wal.Close()

	// Replay into a new MemTable
	memTable := lsm.NewMemTable(1024 * 1024)
	if err := lsm.WALReplay(walPath, memTable); err != nil {
		t.Fatalf("WALReplay failed: %v", err)
	}

	// key1 should be deleted (tombstone exists)
	_, found := memTable.Get([]byte("key1"))
	if found {
		t.Error("Expected key1 to be deleted after replay")
	}

	// key2 should exist
	val, found := memTable.Get([]byte("key2"))
	if !found {
		t.Fatal("Expected key2 to exist after replay")
	}
	if string(val) != "value2" {
		t.Errorf("Expected value2, got %s", val)
	}
}

func TestWALMultiplePuts(t *testing.T) {
	dir := t.TempDir()
	walPath := filepath.Join(dir, "test.wal")

	wal, err := lsm.NewWAL(walPath)
	if err != nil {
		t.Fatalf("Failed to create WAL: %v", err)
	}

	// Write many records
	for i := 0; i < 100; i++ {
		key := []byte("key" + string(rune('A'+i%26)) + string(rune('0'+i/26)))
		value := []byte("value" + string(rune('A'+i%26)))
		if err := wal.WritePut(key, value); err != nil {
			t.Fatalf("WritePut failed at %d: %v", i, err)
		}
	}

	wal.Close()

	// Replay
	memTable := lsm.NewMemTable(1024 * 1024)
	if err := lsm.WALReplay(walPath, memTable); err != nil {
		t.Fatalf("WALReplay failed: %v", err)
	}

	if memTable.Size() != 100 {
		t.Errorf("Expected 100 entries, got %d", memTable.Size())
	}
}

func TestWALNonExistentReplay(t *testing.T) {
	dir := t.TempDir()
	walPath := filepath.Join(dir, "nonexistent.wal")

	memTable := lsm.NewMemTable(1024 * 1024)
	// Replay of non-existent WAL should succeed (no-op)
	if err := lsm.WALReplay(walPath, memTable); err != nil {
		t.Errorf("Expected no error for non-existent WAL, got: %v", err)
	}
}

func TestWALIntegrity(t *testing.T) {
	dir := t.TempDir()
	walPath := filepath.Join(dir, "test.wal")

	wal, err := lsm.NewWAL(walPath)
	if err != nil {
		t.Fatalf("Failed to create WAL: %v", err)
	}

	if err := wal.WritePut([]byte("key1"), []byte("value1")); err != nil {
		t.Fatalf("WritePut failed: %v", err)
	}
	wal.Close()

	// Corrupt the WAL file
	data, _ := os.ReadFile(walPath)
	if len(data) > 10 {
		data[len(data)-1] ^= 0xFF // flip bits in CRC
		os.WriteFile(walPath, data, 0644)
	}

	memTable := lsm.NewMemTable(1024 * 1024)
	err = lsm.WALReplay(walPath, memTable)
	if err == nil {
		t.Error("Expected CRC error during replay of corrupted WAL")
	}
}

func TestWALRemove(t *testing.T) {
	dir := t.TempDir()
	walPath := filepath.Join(dir, "test.wal")

	wal, _ := lsm.NewWAL(walPath)
	wal.WritePut([]byte("key"), []byte("value"))
	wal.Close()

	if _, err := os.Stat(walPath); os.IsNotExist(err) {
		t.Fatal("WAL file should exist")
	}

	if err := lsm.RemoveWAL(walPath); err != nil {
		t.Fatalf("RemoveWAL failed: %v", err)
	}

	if _, err := os.Stat(walPath); !os.IsNotExist(err) {
		t.Error("WAL file should be removed")
	}
}
