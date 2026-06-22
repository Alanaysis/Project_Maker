package test

import (
	"fmt"
	"testing"

	lsm "github.com/lsm-tree/internal"
)

func TestEngineBasicOperations(t *testing.T) {
	dir := t.TempDir()
	engine, err := lsm.NewLSMEngine(dir, 4096)
	if err != nil {
		t.Fatalf("NewLSMEngine failed: %v", err)
	}
	defer engine.Close()

	// Put
	if err := engine.Put([]byte("key1"), []byte("value1")); err != nil {
		t.Fatalf("Put failed: %v", err)
	}

	// Get
	val, err := engine.Get([]byte("key1"))
	if err != nil {
		t.Fatalf("Get failed: %v", err)
	}
	if string(val) != "value1" {
		t.Errorf("Expected value1, got %s", val)
	}

	// Get non-existent key
	val, err = engine.Get([]byte("nonexistent"))
	if err != nil {
		t.Fatalf("Get failed: %v", err)
	}
	if val != nil {
		t.Errorf("Expected nil for non-existent key, got %s", val)
	}
}

func TestEngineUpdate(t *testing.T) {
	dir := t.TempDir()
	engine, err := lsm.NewLSMEngine(dir, 4096)
	if err != nil {
		t.Fatalf("NewLSMEngine failed: %v", err)
	}
	defer engine.Close()

	engine.Put([]byte("key1"), []byte("value1"))
	engine.Put([]byte("key1"), []byte("value2"))

	val, _ := engine.Get([]byte("key1"))
	if string(val) != "value2" {
		t.Errorf("Expected value2 after update, got %s", val)
	}
}

func TestEngineDelete(t *testing.T) {
	dir := t.TempDir()
	engine, err := lsm.NewLSMEngine(dir, 4096)
	if err != nil {
		t.Fatalf("NewLSMEngine failed: %v", err)
	}
	defer engine.Close()

	engine.Put([]byte("key1"), []byte("value1"))
	engine.Delete([]byte("key1"))

	val, _ := engine.Get([]byte("key1"))
	if val != nil {
		t.Errorf("Expected nil after delete, got %s", val)
	}
}

func TestEngineFlush(t *testing.T) {
	dir := t.TempDir()
	// Small MemTable to trigger flush quickly
	engine, err := lsm.NewLSMEngine(dir, 256)
	if err != nil {
		t.Fatalf("NewLSMEngine failed: %v", err)
	}
	defer engine.Close()

	// Write enough data to trigger flush
	n := 50
	for i := 0; i < n; i++ {
		key := fmt.Sprintf("key%04d", i)
		value := fmt.Sprintf("value%04d", i)
		if err := engine.Put([]byte(key), []byte(value)); err != nil {
			t.Fatalf("Put failed at %d: %v", i, err)
		}
	}

	// Verify all data is accessible
	for i := 0; i < n; i++ {
		key := fmt.Sprintf("key%04d", i)
		expected := fmt.Sprintf("value%04d", i)
		val, err := engine.Get([]byte(key))
		if err != nil {
			t.Fatalf("Get(%s) failed: %v", key, err)
		}
		if string(val) != expected {
			t.Errorf("Get(%s): expected %s, got %s", key, expected, val)
		}
	}

	stats := engine.Stats()
	t.Logf("Stats: MemTable=%d entries, SSTables=%v", stats.MemTableSize, stats.SSTableCount)
}

func TestEnginePersistence(t *testing.T) {
	dir := t.TempDir()

	// Write data and close
	engine, err := lsm.NewLSMEngine(dir, 4096)
	if err != nil {
		t.Fatalf("NewLSMEngine failed: %v", err)
	}

	engine.Put([]byte("key1"), []byte("value1"))
	engine.Put([]byte("key2"), []byte("value2"))
	engine.Close()

	// Reopen and verify
	engine2, err := lsm.NewLSMEngine(dir, 4096)
	if err != nil {
		t.Fatalf("NewLSMEngine reopen failed: %v", err)
	}
	defer engine2.Close()

	val, _ := engine2.Get([]byte("key1"))
	if string(val) != "value1" {
		t.Errorf("Expected value1 after reopen, got %s", val)
	}

	val, _ = engine2.Get([]byte("key2"))
	if string(val) != "value2" {
		t.Errorf("Expected value2 after reopen, got %s", val)
	}
}

func TestEngineCrashRecovery(t *testing.T) {
	dir := t.TempDir()

	// Write data (not flushed to SSTable yet)
	engine, err := lsm.NewLSMEngine(dir, 1024*1024) // large MemTable, no auto-flush
	if err != nil {
		t.Fatalf("NewLSMEngine failed: %v", err)
	}

	engine.Put([]byte("key1"), []byte("value1"))
	engine.Put([]byte("key2"), []byte("value2"))

	// Simulate crash: just create new engine (WAL replay should recover)
	engine2, err := lsm.NewLSMEngine(dir, 1024*1024)
	if err != nil {
		t.Fatalf("NewLSMEngine failed: %v", err)
	}
	defer engine2.Close()

	val, _ := engine2.Get([]byte("key1"))
	if string(val) != "value1" {
		t.Errorf("Expected value1 after recovery, got %s", val)
	}

	val, _ = engine2.Get([]byte("key2"))
	if string(val) != "value2" {
		t.Errorf("Expected value2 after recovery, got %s", val)
	}
}

func TestEngineMixedOperations(t *testing.T) {
	dir := t.TempDir()
	engine, err := lsm.NewLSMEngine(dir, 512)
	if err != nil {
		t.Fatalf("NewLSMEngine failed: %v", err)
	}
	defer engine.Close()

	// Mix of put, update, and delete
	engine.Put([]byte("a"), []byte("1"))
	engine.Put([]byte("b"), []byte("2"))
	engine.Put([]byte("c"), []byte("3"))
	engine.Delete([]byte("b"))
	engine.Put([]byte("a"), []byte("10"))

	// Verify
	val, _ := engine.Get([]byte("a"))
	if string(val) != "10" {
		t.Errorf("Expected 10, got %s", val)
	}

	val, _ = engine.Get([]byte("b"))
	if val != nil {
		t.Errorf("Expected nil for deleted key b, got %s", val)
	}

	val, _ = engine.Get([]byte("c"))
	if string(val) != "3" {
		t.Errorf("Expected 3, got %s", val)
	}
}

func TestEngineLargeDataset(t *testing.T) {
	dir := t.TempDir()
	engine, err := lsm.NewLSMEngine(dir, 1024)
	if err != nil {
		t.Fatalf("NewLSMEngine failed: %v", err)
	}
	defer engine.Close()

	n := 500
	for i := 0; i < n; i++ {
		key := fmt.Sprintf("key%06d", i)
		value := fmt.Sprintf("value%06d", i*10)
		if err := engine.Put([]byte(key), []byte(value)); err != nil {
			t.Fatalf("Put failed at %d: %v", i, err)
		}
	}

	// Verify all data
	for i := 0; i < n; i++ {
		key := fmt.Sprintf("key%06d", i)
		expected := fmt.Sprintf("value%06d", i*10)
		val, err := engine.Get([]byte(key))
		if err != nil {
			t.Fatalf("Get(%s) failed: %v", key, err)
		}
		if string(val) != expected {
			t.Errorf("Get(%s): expected %s, got %s", key, expected, val)
		}
	}

	stats := engine.Stats()
	t.Logf("After %d entries: MemTable=%d, SSTables=%v", n, stats.MemTableSize, stats.SSTableCount)
}

func TestEngineStats(t *testing.T) {
	dir := t.TempDir()
	engine, err := lsm.NewLSMEngine(dir, 4096)
	if err != nil {
		t.Fatalf("NewLSMEngine failed: %v", err)
	}
	defer engine.Close()

	stats := engine.Stats()
	if stats.MemTableSize != 0 {
		t.Errorf("Expected empty MemTable, got %d", stats.MemTableSize)
	}

	engine.Put([]byte("key1"), []byte("value1"))
	stats = engine.Stats()
	if stats.MemTableSize != 1 {
		t.Errorf("Expected 1 entry, got %d", stats.MemTableSize)
	}
}
