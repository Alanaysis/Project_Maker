package test

import (
	"fmt"
	"os"
	"path/filepath"
	"testing"

	lsm "github.com/lsm-tree/internal"
)

func TestSSTableBuildAndGet(t *testing.T) {
	dir := t.TempDir()
	filePath := filepath.Join(dir, "test.sst")

	builder := lsm.NewSSTableBuilder()
	builder.Add([]byte("apple"), []byte("red"), false)
	builder.Add([]byte("banana"), []byte("yellow"), false)
	builder.Add([]byte("cherry"), []byte("red"), false)

	table, err := builder.Build(filePath, 0)
	if err != nil {
		t.Fatalf("Build failed: %v", err)
	}
	defer table.Close()

	tests := []struct {
		key      string
		expected string
		found    bool
	}{
		{"apple", "red", true},
		{"banana", "yellow", true},
		{"cherry", "red", true},
		{"date", "", false},
	}

	for _, tt := range tests {
		val, found, err := table.Get([]byte(tt.key))
		if err != nil {
			t.Errorf("Get(%s) error: %v", tt.key, err)
			continue
		}
		if found != tt.found {
			t.Errorf("Get(%s): expected found=%v, got %v", tt.key, tt.found, found)
			continue
		}
		if found && string(val) != tt.expected {
			t.Errorf("Get(%s): expected %s, got %s", tt.key, tt.expected, val)
		}
	}
}

func TestSSTableTombstone(t *testing.T) {
	dir := t.TempDir()
	filePath := filepath.Join(dir, "test.sst")

	builder := lsm.NewSSTableBuilder()
	builder.Add([]byte("key1"), []byte("value1"), false)
	builder.Add([]byte("key1"), nil, true) // tombstone

	table, err := builder.Build(filePath, 0)
	if err != nil {
		t.Fatalf("Build failed: %v", err)
	}
	defer table.Close()

	// The entry is marked as deleted
	val, found, err := table.Get([]byte("key1"))
	if err != nil {
		t.Fatalf("Get error: %v", err)
	}
	if !found {
		t.Error("Expected to find the key (even if tombstone)")
	}
	// Tombstone entries have nil or empty value
	_ = val
}

func TestSSTableSorted(t *testing.T) {
	dir := t.TempDir()
	filePath := filepath.Join(dir, "test.sst")

	builder := lsm.NewSSTableBuilder()
	// Insert in reverse order
	builder.Add([]byte("cherry"), []byte("3"), false)
	builder.Add([]byte("apple"), []byte("1"), false)
	builder.Add([]byte("banana"), []byte("2"), false)

	table, err := builder.Build(filePath, 0)
	if err != nil {
		t.Fatalf("Build failed: %v", err)
	}
	defer table.Close()

	// Read back in sorted order
	iter, err := table.NewIterator()
	if err != nil {
		t.Fatalf("NewIterator failed: %v", err)
	}

	expected := []string{"apple", "banana", "cherry"}
	i := 0
	for iter.Valid() {
		if string(iter.Key()) != expected[i] {
			t.Errorf("Entry %d: expected %s, got %s", i, expected[i], iter.Key())
		}
		i++
		iter.Next()
	}

	if i != len(expected) {
		t.Errorf("Expected %d entries, got %d", len(expected), i)
	}
}

func TestSSTableLargeDataset(t *testing.T) {
	dir := t.TempDir()
	filePath := filepath.Join(dir, "test.sst")

	builder := lsm.NewSSTableBuilder()
	n := 1000
	for i := 0; i < n; i++ {
		key := fmt.Sprintf("key%06d", i)
		value := fmt.Sprintf("value%d", i)
		builder.Add([]byte(key), []byte(value), false)
	}

	table, err := builder.Build(filePath, 0)
	if err != nil {
		t.Fatalf("Build failed: %v", err)
	}
	defer table.Close()

	// Verify all entries via Get
	for i := 0; i < n; i++ {
		key := fmt.Sprintf("key%06d", i)
		expected := fmt.Sprintf("value%d", i)
		val, found, err := table.Get([]byte(key))
		if err != nil {
			t.Errorf("Get(%s) error: %v", key, err)
			continue
		}
		if !found {
			t.Errorf("Key %s not found", key)
			continue
		}
		if string(val) != expected {
			t.Errorf("Key %s: expected %s, got %s", key, expected, val)
		}
	}

	// Verify via iterator
	iter, err := table.NewIterator()
	if err != nil {
		t.Fatalf("NewIterator failed: %v", err)
	}

	count := 0
	for iter.Valid() {
		count++
		iter.Next()
	}
	if count != n {
		t.Errorf("Iterator expected %d entries, got %d", n, count)
	}
}

func TestSSTablePersistence(t *testing.T) {
	dir := t.TempDir()
	filePath := filepath.Join(dir, "test.sst")

	// Build SSTable
	builder := lsm.NewSSTableBuilder()
	builder.Add([]byte("key1"), []byte("value1"), false)
	builder.Add([]byte("key2"), []byte("value2"), false)
	table, err := builder.Build(filePath, 0)
	if err != nil {
		t.Fatalf("Build failed: %v", err)
	}
	table.Close()

	// Reopen and verify
	table, err = lsm.OpenSSTable(filePath)
	if err != nil {
		t.Fatalf("OpenSSTable failed: %v", err)
	}
	defer table.Close()

	if table.EntryCount() != 2 {
		t.Errorf("Expected 2 entries, got %d", table.EntryCount())
	}

	val, found, err := table.Get([]byte("key1"))
	if err != nil || !found || string(val) != "value1" {
		t.Errorf("Get(key1) failed: found=%v, val=%s, err=%v", found, val, err)
	}
}

func TestSSTableEmpty(t *testing.T) {
	dir := t.TempDir()
	filePath := filepath.Join(dir, "empty.sst")

	builder := lsm.NewSSTableBuilder()
	_, err := builder.Build(filePath, 0)
	if err != nil {
		t.Fatalf("Build empty SSTable should not fail: %v", err)
	}

	_, err = os.Stat(filePath)
	if err != nil {
		t.Error("Empty SSTable file should exist")
	}
}
