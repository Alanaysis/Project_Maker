package test

import (
	"fmt"
	"path/filepath"
	"testing"

	lsm "github.com/lsm-tree/internal"
)

func TestSizeTieredCompactionBasic(t *testing.T) {
	dir := t.TempDir()
	nextID := 0
	st := lsm.NewSizeTieredCompactionStrategy(dir, &nextID)

	// Create 4 tables (enough to trigger compaction with minThreshold=4)
	tables := make([]*lsm.SSTable, 4)
	for i := 0; i < 4; i++ {
		filePath := filepath.Join(dir, fmt.Sprintf("table_%d.sst", i))
		builder := lsm.NewSSTableBuilder()
		for j := 0; j < 10; j++ {
			key := fmt.Sprintf("key_%02d", j)
			value := fmt.Sprintf("value_t%d_%d", i, j)
			builder.Add([]byte(key), []byte(value), false)
		}
		table, err := builder.Build(filePath, 0)
		if err != nil {
			t.Fatalf("Build table %d failed: %v", i, err)
		}
		tables[i] = table
	}

	// Should compact
	if !st.ShouldCompact(tables) {
		t.Error("Expected ShouldCompact to return true for 4 tables")
	}

	// Perform compaction
	result, err := st.Compact(tables)
	if err != nil {
		t.Fatalf("Compact failed: %v", err)
	}

	// Should produce fewer tables
	if len(result) == 0 {
		t.Fatal("Expected non-empty result")
	}

	// Verify merged data
	for _, table := range result {
		defer table.Close()
	}

	// The last table's values should win (table 3)
	for j := 0; j < 10; j++ {
		key := fmt.Sprintf("key_%02d", j)
		expected := fmt.Sprintf("value_t3_%d", j) // last table wins

		found := false
		for _, table := range result {
			val, ok, err := table.Get([]byte(key))
			if err != nil {
				t.Errorf("Get(%s) error: %v", key, err)
				continue
			}
			if ok {
				if string(val) != expected {
					t.Errorf("Key %s: expected %s, got %s", key, expected, val)
				}
				found = true
				break
			}
		}
		if !found {
			t.Errorf("Key %s not found in compacted tables", key)
		}
	}
}

func TestSizeTieredCompactionNotEnoughTables(t *testing.T) {
	dir := t.TempDir()
	nextID := 0
	st := lsm.NewSizeTieredCompactionStrategy(dir, &nextID)

	// Create only 2 tables (not enough for minThreshold=4)
	tables := make([]*lsm.SSTable, 2)
	for i := 0; i < 2; i++ {
		filePath := filepath.Join(dir, fmt.Sprintf("table_%d.sst", i))
		builder := lsm.NewSSTableBuilder()
		builder.Add([]byte("key"), []byte("value"), false)
		table, err := builder.Build(filePath, 0)
		if err != nil {
			t.Fatalf("Build table %d failed: %v", i, err)
		}
		tables[i] = table
	}

	// Should not compact
	if st.ShouldCompact(tables) {
		t.Error("Expected ShouldCompact to return false for 2 tables")
	}

	// Compact should return tables as-is
	result, err := st.Compact(tables)
	if err != nil {
		t.Fatalf("Compact failed: %v", err)
	}

	if len(result) != 2 {
		t.Errorf("Expected 2 tables, got %d", len(result))
	}
}

func TestSizeTieredCompactionEmpty(t *testing.T) {
	dir := t.TempDir()
	nextID := 0
	st := lsm.NewSizeTieredCompactionStrategy(dir, &nextID)

	result, err := st.Compact(nil)
	if err != nil {
		t.Fatalf("Compact failed: %v", err)
	}

	if len(result) != 0 {
		t.Errorf("Expected 0 tables, got %d", len(result))
	}
}

func TestSizeTieredCompactionWithTombstones(t *testing.T) {
	dir := t.TempDir()
	nextID := 0
	st := lsm.NewSizeTieredCompactionStrategy(dir, &nextID)

	// Create 4 tables with some tombstones
	tables := make([]*lsm.SSTable, 4)
	for i := 0; i < 4; i++ {
		filePath := filepath.Join(dir, fmt.Sprintf("table_%d.sst", i))
		builder := lsm.NewSSTableBuilder()
		builder.Add([]byte("alive"), []byte("yes"), false)
		builder.Add([]byte("dead"), []byte("value"), true) // tombstone
		builder.Add([]byte("key"), []byte(fmt.Sprintf("v%d", i)), false)
		table, err := builder.Build(filePath, 0)
		if err != nil {
			t.Fatalf("Build table %d failed: %v", i, err)
		}
		tables[i] = table
	}

	result, err := st.Compact(tables)
	if err != nil {
		t.Fatalf("Compact failed: %v", err)
	}

	// Verify data
	for _, table := range result {
		defer table.Close()

		// "alive" should exist
		val, found, err := table.Get([]byte("alive"))
		if err != nil {
			t.Errorf("Get(alive) error: %v", err)
		} else if found && string(val) != "yes" {
			t.Errorf("Expected alive=yes, got %s", val)
		}
	}
}

func TestSizeTieredCompactionLargeDataset(t *testing.T) {
	dir := t.TempDir()
	nextID := 0
	st := lsm.NewSizeTieredCompactionStrategy(dir, &nextID)

	// Create 4 tables with large datasets
	tables := make([]*lsm.SSTable, 4)
	for i := 0; i < 4; i++ {
		filePath := filepath.Join(dir, fmt.Sprintf("table_%d.sst", i))
		builder := lsm.NewSSTableBuilder()
		for j := 0; j < 100; j++ {
			key := fmt.Sprintf("key_%06d", j)
			value := fmt.Sprintf("value_t%d_%d", i, j)
			builder.Add([]byte(key), []byte(value), false)
		}
		table, err := builder.Build(filePath, 0)
		if err != nil {
			t.Fatalf("Build table %d failed: %v", i, err)
		}
		tables[i] = table
	}

	result, err := st.Compact(tables)
	if err != nil {
		t.Fatalf("Compact failed: %v", err)
	}

	// Verify all 100 keys with correct values (last table wins)
	for _, table := range result {
		defer table.Close()
		for j := 0; j < 100; j++ {
			key := fmt.Sprintf("key_%06d", j)
			expected := fmt.Sprintf("value_t3_%d", j)
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
	}
}
