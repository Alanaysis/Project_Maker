package queue

import (
	"testing"
)

// TestIndexFileCreation verifies index file creation.
func TestIndexFileCreation(t *testing.T) {
	idx := NewIndexFile("/tmp/test.index", 100)

	if idx.capacity != 100 {
		t.Errorf("expected capacity 100, got %d", idx.capacity)
	}
	if idx.path != "/tmp/test.index" {
		t.Errorf("expected path '/tmp/test.index', got '%s'", idx.path)
	}
	if idx.EntryCount() != 0 {
		t.Errorf("expected 0 entries, got %d", idx.EntryCount())
	}
}

// TestIndexFileAppend verifies appending entries.
func TestIndexFileAppend(t *testing.T) {
	idx := NewIndexFile("/tmp/test.index", 100)

	for i := 0; i < 10; i++ {
		idx.Append(int64(i), uint32(i*100))
	}

	if idx.EntryCount() != 10 {
		t.Errorf("expected 10 entries, got %d", idx.EntryCount())
	}
}

// TestIndexFileLookup verifies offset lookup.
func TestIndexFileLookup(t *testing.T) {
	idx := NewIndexFile("/tmp/test.index", 100)

	// Add entries
	for i := 0; i < 10; i++ {
		idx.Append(int64(i), uint32(i*100))
	}

	// Lookup existing offset
	pos, found := idx.Lookup(5)
	if !found {
		t.Error("should find offset 5")
	}
	if pos != 500 {
		t.Errorf("expected position 500, got %d", pos)
	}

	// Lookup non-existing offset (should return closest earlier entry)
	pos, found = idx.Lookup(7)
	if found {
		t.Error("should not find exact offset 7")
	}
	if pos != 600 {
		t.Errorf("expected position 600 for offset 7, got %d", pos)
	}
}

// TestIndexFileLookupEmpty verifies lookup on empty index.
func TestIndexFileLookupEmpty(t *testing.T) {
	idx := NewIndexFile("/tmp/test.index", 100)

	_, found := idx.Lookup(0)
	if found {
		t.Error("should not find anything in empty index")
	}
}

// TestIndexFileLookupOutOfRange verifies lookup of offset beyond index.
func TestIndexFileLookupOutOfRange(t *testing.T) {
	idx := NewIndexFile("/tmp/test.index", 100)

	for i := 0; i < 5; i++ {
		idx.Append(int64(i), uint32(i*10))
	}

	// Lookup offset beyond the last entry
	pos, found := idx.Lookup(100)
	if !found {
		t.Error("should find closest entry for out-of-range offset")
	}
	if pos != 40 {
		t.Errorf("expected position 40, got %d", pos)
	}
}

// TestIndexFileCapacityLimit verifies capacity limit.
func TestIndexFileCapacityLimit(t *testing.T) {
	idx := NewIndexFile("/tmp/test.index", 5)

	for i := 0; i < 10; i++ {
		idx.Append(int64(i), uint32(i*10))
	}

	// Should be capped at capacity
	if idx.EntryCount() > 5 {
		t.Errorf("expected at most 5 entries, got %d", idx.EntryCount())
	}
}

// TestIndexFileClear verifies clearing entries.
func TestIndexFileClear(t *testing.T) {
	idx := NewIndexFile("/tmp/test.index", 100)

	for i := 0; i < 10; i++ {
		idx.Append(int64(i), uint32(i*10))
	}

	idx.Clear()

	if idx.EntryCount() != 0 {
		t.Errorf("expected 0 entries after clear, got %d", idx.EntryCount())
	}
}

// TestIndexFileBinarySearch verifies binary search correctness.
func TestIndexFileBinarySearch(t *testing.T) {
	idx := NewIndexFile("/tmp/test.index", 100)

	// Add entries with gaps
	gaps := []int{0, 5, 10, 20, 50, 100, 200, 500}
	for _, offset := range gaps {
		idx.Append(int64(offset), uint32(offset*10))
	}

	// Test exact lookups
	for _, offset := range gaps {
		pos, found := idx.Lookup(int64(offset))
		if !found {
			t.Errorf("should find exact offset %d", offset)
		}
		if pos != uint32(offset*10) {
			t.Errorf("expected position %d for offset %d, got %d", offset*10, offset, pos)
		}
	}

	// Test in-between lookups (should return closest earlier)
	testCases := []struct {
		offset   int64
		expected uint32
	}{
		{1, 10},    // Between 0 and 5
		{7, 100},   // Between 5 and 10
		{15, 200},  // Between 10 and 20
		{25, 500},  // Between 20 and 50
		{75, 1000}, // Between 50 and 100
	}

	for _, tc := range testCases {
		pos, _ := idx.Lookup(tc.offset)
		if pos != tc.expected {
			t.Errorf("offset %d: expected position %d, got %d", tc.offset, tc.expected, pos)
		}
	}
}

// TestIndexFileLargeIndex verifies handling of large indices.
func TestIndexFileLargeIndex(t *testing.T) {
	idx := NewIndexFile("/tmp/test.index", 10000)

	// Add many entries
	numEntries := 5000
	for i := 0; i < numEntries; i++ {
		idx.Append(int64(i), uint32(i*10))
	}

	if idx.EntryCount() != uint32(numEntries) {
		t.Errorf("expected %d entries, got %d", numEntries, idx.EntryCount())
	}

	// Lookup middle entry
	pos, found := idx.Lookup(2500)
	if !found {
		t.Error("should find offset 2500")
	}
	if pos != 25000 {
		t.Errorf("expected position 25000, got %d", pos)
	}
}

// TestIndexFileConcurrentAccess verifies thread safety.
func TestIndexFileConcurrentAccess(t *testing.T) {
	idx := NewIndexFile("/tmp/test.index", 1000)

	done := make(chan bool, 10)
	for i := 0; i < 10; i++ {
		go func(start int) {
			for j := 0; j < 100; j++ {
				offset := start*100 + j
				idx.Append(int64(offset), uint32(offset*10))
				_, _ = idx.Lookup(int64(offset))
			}
			done <- true
		}(i)
	}

	// Wait for all goroutines
	for i := 0; i < 10; i++ {
		<-done
	}

	count := idx.EntryCount()
	if count == 0 {
		t.Error("expected some entries after concurrent access")
	}
}

// TestIndexFileNegativeOffset verifies handling of negative offsets.
func TestIndexFileNegativeOffset(t *testing.T) {
	idx := NewIndexFile("/tmp/test.index", 100)

	// Add entry with offset 0
	idx.Append(0, 0)

	// Lookup negative offset (should return the earliest entry)
	pos, found := idx.Lookup(-1)
	if !found {
		t.Error("should find closest entry for negative offset")
	}
	if pos != 0 {
		t.Errorf("expected position 0, got %d", pos)
	}
}

// TestIndexFileSingleEntry verifies single entry behavior.
func TestIndexFileSingleEntry(t *testing.T) {
	idx := NewIndexFile("/tmp/test.index", 100)

	idx.Append(42, 420)

	if idx.EntryCount() != 1 {
		t.Errorf("expected 1 entry, got %d", idx.EntryCount())
	}

	pos, found := idx.Lookup(42)
	if !found {
		t.Error("should find offset 42")
	}
	if pos != 420 {
		t.Errorf("expected position 420, got %d", pos)
	}
}
