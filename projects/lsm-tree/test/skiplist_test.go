package test

import (
	"fmt"
	"testing"

	lsm "github.com/lsm-tree/internal"
)

func TestSkipListInsertAndGet(t *testing.T) {
	sl := lsm.NewSkipList()

	sl.Insert([]byte("key1"), []byte("value1"))
	sl.Insert([]byte("key2"), []byte("value2"))
	sl.Insert([]byte("key3"), []byte("value3"))

	tests := []struct {
		key      string
		expected string
		found    bool
	}{
		{"key1", "value1", true},
		{"key2", "value2", true},
		{"key3", "value3", true},
		{"key4", "", false},
	}

	for _, tt := range tests {
		val, found := sl.Get([]byte(tt.key))
		if found != tt.found {
			t.Errorf("Get(%s): expected found=%v, got %v", tt.key, tt.found, found)
		}
		if found && string(val) != tt.expected {
			t.Errorf("Get(%s): expected %s, got %s", tt.key, tt.expected, val)
		}
	}
}

func TestSkipListUpdate(t *testing.T) {
	sl := lsm.NewSkipList()

	sl.Insert([]byte("key1"), []byte("value1"))
	val, found := sl.Get([]byte("key1"))
	if !found || string(val) != "value1" {
		t.Fatalf("Expected value1, got %s", val)
	}

	sl.Insert([]byte("key1"), []byte("updated"))
	val, found = sl.Get([]byte("key1"))
	if !found || string(val) != "updated" {
		t.Errorf("Expected updated, got %s", val)
	}
}

func TestSkipListDelete(t *testing.T) {
	sl := lsm.NewSkipList()

	sl.Insert([]byte("key1"), []byte("value1"))
	sl.Insert([]byte("key2"), []byte("value2"))

	// Delete key1
	deleted := sl.Delete([]byte("key1"))
	if !deleted {
		t.Error("Expected delete to return true")
	}

	// key1 should not be found
	_, found := sl.Get([]byte("key1"))
	if found {
		t.Error("Expected key1 to be deleted")
	}

	// key2 should still be there
	val, found := sl.Get([]byte("key2"))
	if !found || string(val) != "value2" {
		t.Error("Expected key2 to still exist")
	}

	// Delete non-existent key
	deleted = sl.Delete([]byte("key3"))
	if deleted {
		t.Error("Expected delete of non-existent key to return false")
	}
}

func TestSkipListSortedOrder(t *testing.T) {
	sl := lsm.NewSkipList()

	// Insert in random order
	keys := []string{"banana", "apple", "cherry", "date", "elderberry"}
	for _, key := range keys {
		sl.Insert([]byte(key), []byte("value"))
	}

	entries := sl.Entries()
	expectedOrder := []string{"apple", "banana", "cherry", "date", "elderberry"}

	if len(entries) != len(expectedOrder) {
		t.Fatalf("Expected %d entries, got %d", len(expectedOrder), len(entries))
	}

	for i, entry := range entries {
		if string(entry.Key) != expectedOrder[i] {
			t.Errorf("Entry %d: expected %s, got %s", i, expectedOrder[i], entry.Key)
		}
	}
}

func TestSkipListIterator(t *testing.T) {
	sl := lsm.NewSkipList()

	for i := 0; i < 10; i++ {
		key := fmt.Sprintf("key%02d", i)
		value := fmt.Sprintf("value%d", i)
		sl.Insert([]byte(key), []byte(value))
	}

	iter := sl.NewIterator()
	count := 0
	for iter.Valid() {
		expectedKey := fmt.Sprintf("key%02d", count)
		if string(iter.Key()) != expectedKey {
			t.Errorf("Expected key %s, got %s", expectedKey, iter.Key())
		}
		iter.Next()
		count++
	}

	if count != 10 {
		t.Errorf("Expected 10 entries, got %d", count)
	}
}

func TestSkipListSize(t *testing.T) {
	sl := lsm.NewSkipList()

	if sl.Size() != 0 {
		t.Errorf("Expected size 0, got %d", sl.Size())
	}

	sl.Insert([]byte("key1"), []byte("value1"))
	if sl.Size() != 1 {
		t.Errorf("Expected size 1, got %d", sl.Size())
	}

	sl.Insert([]byte("key2"), []byte("value2"))
	if sl.Size() != 2 {
		t.Errorf("Expected size 2, got %d", sl.Size())
	}

	// Update should not change size
	sl.Insert([]byte("key1"), []byte("updated"))
	if sl.Size() != 2 {
		t.Errorf("Expected size 2 after update, got %d", sl.Size())
	}
}

func TestSkipListLargeDataset(t *testing.T) {
	sl := lsm.NewSkipList()

	n := 1000
	for i := 0; i < n; i++ {
		key := fmt.Sprintf("key%06d", i)
		value := fmt.Sprintf("value%d", i)
		sl.Insert([]byte(key), []byte(value))
	}

	if sl.Size() != n {
		t.Errorf("Expected size %d, got %d", n, sl.Size())
	}

	// Verify all entries
	for i := 0; i < n; i++ {
		key := fmt.Sprintf("key%06d", i)
		expected := fmt.Sprintf("value%d", i)
		val, found := sl.Get([]byte(key))
		if !found {
			t.Errorf("Key %s not found", key)
			continue
		}
		if string(val) != expected {
			t.Errorf("Key %s: expected %s, got %s", key, expected, val)
		}
	}
}
