package test

import (
	"fmt"
	"os"
	"path/filepath"
	"testing"

	lsm "github.com/lsm-tree/internal"
)

func TestCompactMergeTwoTables(t *testing.T) {
	dir := t.TempDir()

	// Build first SSTable
	file1 := filepath.Join(dir, "table1.sst")
	builder1 := lsm.NewSSTableBuilder()
	builder1.Add([]byte("a"), []byte("1"), false)
	builder1.Add([]byte("b"), []byte("2"), false)
	builder1.Add([]byte("c"), []byte("3"), false)
	table1, err := builder1.Build(file1, 0)
	if err != nil {
		t.Fatalf("Build table1 failed: %v", err)
	}

	// Build second SSTable (overwrites some keys)
	file2 := filepath.Join(dir, "table2.sst")
	builder2 := lsm.NewSSTableBuilder()
	builder2.Add([]byte("b"), []byte("20"), false)
	builder2.Add([]byte("d"), []byte("4"), false)
	table2, err := builder2.Build(file2, 0)
	if err != nil {
		t.Fatalf("Build table2 failed: %v", err)
	}

	// Compact
	outputPath := filepath.Join(dir, "merged.sst")
	merged, err := lsm.Compact([]*lsm.SSTable{table1, table2}, outputPath, 1)
	if err != nil {
		t.Fatalf("Compact failed: %v", err)
	}
	defer merged.Close()

	// Verify merged results
	expected := map[string]string{
		"a": "1",
		"b": "20", // overwritten by table2
		"c": "3",
		"d": "4",
	}

	for key, expectedVal := range expected {
		val, found, err := merged.Get([]byte(key))
		if err != nil {
			t.Errorf("Get(%s) error: %v", key, err)
			continue
		}
		if !found {
			t.Errorf("Key %s not found in merged table", key)
			continue
		}
		if string(val) != expectedVal {
			t.Errorf("Key %s: expected %s, got %s", key, expectedVal, val)
		}
	}
}

func TestCompactRemovesTombstones(t *testing.T) {
	dir := t.TempDir()

	// Build SSTable with tombstone
	file1 := filepath.Join(dir, "table1.sst")
	builder := lsm.NewSSTableBuilder()
	builder.Add([]byte("alive"), []byte("yes"), false)
	builder.Add([]byte("dead"), []byte("value"), true) // tombstone
	table1, err := builder.Build(file1, 0)
	if err != nil {
		t.Fatalf("Build failed: %v", err)
	}

	// Compact at max level - tombstones should be removed
	outputPath := filepath.Join(dir, "merged.sst")
	merged, err := lsm.Compact([]*lsm.SSTable{table1}, outputPath, 6) // max level
	if err != nil {
		t.Fatalf("Compact failed: %v", err)
	}
	if merged == nil {
		t.Fatal("Expected non-nil merged table")
	}
	defer merged.Close()

	// "dead" should not exist (tombstone removed at max level)
	_, found, _ := merged.Get([]byte("dead"))
	if found {
		t.Error("Tombstone should be removed at max level")
	}

	// "alive" should still exist
	val, found, _ := merged.Get([]byte("alive"))
	if !found || string(val) != "yes" {
		t.Error("Alive key should still exist")
	}
}

func TestCompactMultipleTables(t *testing.T) {
	dir := t.TempDir()

	// Create 3 tables with overlapping keys
	tables := make([]*lsm.SSTable, 3)
	for i := 0; i < 3; i++ {
		filePath := filepath.Join(dir, fmt.Sprintf("table%d.sst", i))
		builder := lsm.NewSSTableBuilder()
		for j := 0; j < 10; j++ {
			key := fmt.Sprintf("key%02d", j)
			value := fmt.Sprintf("value_t%d_%d", i, j)
			builder.Add([]byte(key), []byte(value), false)
		}
		table, err := builder.Build(filePath, 0)
		if err != nil {
			t.Fatalf("Build table %d failed: %v", i, err)
		}
		tables[i] = table
	}

	// Compact all tables
	outputPath := filepath.Join(dir, "merged.sst")
	merged, err := lsm.Compact(tables, outputPath, 1)
	if err != nil {
		t.Fatalf("Compact failed: %v", err)
	}
	defer merged.Close()

	// The last table's values should win (table 2)
	for j := 0; j < 10; j++ {
		key := fmt.Sprintf("key%02d", j)
		expected := fmt.Sprintf("value_t2_%d", j) // last table wins
		val, found, err := merged.Get([]byte(key))
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
}

func TestCompactEmptyTables(t *testing.T) {
	dir := t.TempDir()

	tables := make([]*lsm.SSTable, 0)
	outputPath := filepath.Join(dir, "merged.sst")
	merged, err := lsm.Compact(tables, outputPath, 0)
	if err != nil {
		t.Fatalf("Compact empty tables should not fail: %v", err)
	}
	if merged != nil {
		t.Error("Expected nil result for empty compact")
		os.Remove(merged.FilePath())
	}
}
