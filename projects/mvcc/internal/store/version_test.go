package store

import (
	"testing"
)

func TestStorePutAndGet(t *testing.T) {
	s := NewStore()

	// Put a value
	s.Put("key1", []byte("value1"), 1, 1)

	// Get should return the value
	val, ok := s.Get("key1", 1)
	if !ok {
		t.Fatal("expected to find key1")
	}
	if string(val) != "value1" {
		t.Fatalf("expected 'value1', got '%s'", string(val))
	}
}

func TestStoreGetNonExistent(t *testing.T) {
	s := NewStore()

	_, ok := s.Get("nonexistent", 1)
	if ok {
		t.Fatal("expected not to find nonexistent key")
	}
}

func TestStoreMultipleVersions(t *testing.T) {
	s := NewStore()

	// Create multiple versions
	s.Put("key1", []byte("v1"), 1, 1)
	s.Put("key1", []byte("v2"), 2, 2)
	s.Put("key1", []byte("v3"), 3, 3)

	// Read at timestamp 1 should see v1
	val, ok := s.Get("key1", 1)
	if !ok || string(val) != "v1" {
		t.Fatalf("expected 'v1' at ts=1, got '%s', ok=%v", string(val), ok)
	}

	// Read at timestamp 2 should see v2
	val, ok = s.Get("key1", 2)
	if !ok || string(val) != "v2" {
		t.Fatalf("expected 'v2' at ts=2, got '%s', ok=%v", string(val), ok)
	}

	// Read at timestamp 3 should see v3
	val, ok = s.Get("key1", 3)
	if !ok || string(val) != "v3" {
		t.Fatalf("expected 'v3' at ts=3, got '%s', ok=%v", string(val), ok)
	}

	// Read at timestamp 100 should see v3 (latest)
	val, ok = s.Get("key1", 100)
	if !ok || string(val) != "v3" {
		t.Fatalf("expected 'v3' at ts=100, got '%s', ok=%v", string(val), ok)
	}
}

func TestStoreDelete(t *testing.T) {
	s := NewStore()

	s.Put("key1", []byte("value1"), 1, 1)

	// Delete at timestamp 2
	ok := s.Delete("key1", 2, 2)
	if !ok {
		t.Fatal("expected delete to succeed")
	}

	// Should still be visible at timestamp 1
	val, ok := s.Get("key1", 1)
	if !ok || string(val) != "value1" {
		t.Fatalf("expected 'value1' at ts=1 after delete at ts=2, got ok=%v", ok)
	}

	// Should not be visible at timestamp 2
	_, ok = s.Get("key1", 2)
	if ok {
		t.Fatal("expected key1 to not be visible at ts=2")
	}

	// Should not be visible at timestamp 3
	_, ok = s.Get("key1", 3)
	if ok {
		t.Fatal("expected key1 to not be visible at ts=3")
	}
}

func TestStoreDeleteNonExistent(t *testing.T) {
	s := NewStore()

	ok := s.Delete("key1", 1, 1)
	if ok {
		t.Fatal("expected delete to fail for non-existent key")
	}
}

func TestStoreHasConflict(t *testing.T) {
	s := NewStore()

	// Transaction 1 writes at timestamp 2
	s.Put("key1", []byte("value1"), 1, 2)

	// Transaction 2 started at timestamp 1, should detect conflict
	hasConflict := s.HasConflict("key1", 1, 2)
	if !hasConflict {
		t.Fatal("expected conflict for txn2 that started before write")
	}

	// Transaction 3 started at timestamp 2, no conflict
	hasConflict = s.HasConflict("key1", 2, 3)
	if hasConflict {
		t.Fatal("expected no conflict for txn3 that started at same time as write")
	}

	// Transaction 4 started at timestamp 3, no conflict
	hasConflict = s.HasConflict("key1", 3, 4)
	if hasConflict {
		t.Fatal("expected no conflict for txn4 that started after write")
	}
}

func TestStoreHasConflictSameTxn(t *testing.T) {
	s := NewStore()

	// Transaction 1 writes at timestamp 2
	s.Put("key1", []byte("value1"), 1, 2)

	// Same transaction should not conflict with itself
	hasConflict := s.HasConflict("key1", 1, 1)
	if hasConflict {
		t.Fatal("expected no conflict for same transaction")
	}
}

func TestStoreRemoveVersions(t *testing.T) {
	s := NewStore()

	// Create versions at different timestamps
	s.Put("key1", []byte("v1"), 1, 1)
	s.Put("key1", []byte("v2"), 2, 2)
	s.Put("key1", []byte("v3"), 3, 3)

	// Mark v1 as deleted
	s.Delete("key1", 4, 4)

	// Remove versions visible before timestamp 3
	removed := s.RemoveVersions(3)

	// v1 (deleted) should be removed, v2 and v3 should remain
	if removed != 1 {
		t.Fatalf("expected 1 version removed, got %d", removed)
	}

	versions := s.AllVersions("key1")
	if len(versions) != 2 {
		t.Fatalf("expected 2 versions remaining, got %d", len(versions))
	}
}

func TestStoreVersionCount(t *testing.T) {
	s := NewStore()

	s.Put("key1", []byte("v1"), 1, 1)
	s.Put("key1", []byte("v2"), 2, 2)
	s.Put("key2", []byte("v3"), 3, 3)

	count := s.VersionCount()
	if count != 3 {
		t.Fatalf("expected 3 versions, got %d", count)
	}
}

func TestStoreKeys(t *testing.T) {
	s := NewStore()

	s.Put("key1", []byte("v1"), 1, 1)
	s.Put("key2", []byte("v2"), 2, 2)

	keys := s.Keys()
	if len(keys) != 2 {
		t.Fatalf("expected 2 keys, got %d", len(keys))
	}
}

func TestVersionIsVisible(t *testing.T) {
	tests := []struct {
		name           string
		createdAt      uint64
		deletedAt      uint64
		status         VersionStatus
		readTimestamp  uint64
		expectedVisible bool
	}{
		{
			name:           "visible - created before read",
			createdAt:      1,
			deletedAt:      0,
			status:         VersionActive,
			readTimestamp:  2,
			expectedVisible: true,
		},
		{
			name:           "visible - created at read time",
			createdAt:      2,
			deletedAt:      0,
			status:         VersionActive,
			readTimestamp:  2,
			expectedVisible: true,
		},
		{
			name:           "not visible - created after read",
			createdAt:      3,
			deletedAt:      0,
			status:         VersionActive,
			readTimestamp:  2,
			expectedVisible: false,
		},
		{
			name:           "not visible - deleted before read",
			createdAt:      1,
			deletedAt:      2,
			status:         VersionDeleted,
			readTimestamp:  3,
			expectedVisible: false,
		},
		{
			name:           "visible - deleted after read",
			createdAt:      1,
			deletedAt:      3,
			status:         VersionDeleted,
			readTimestamp:  2,
			expectedVisible: true,
		},
		{
			name:           "not visible - garbage status",
			createdAt:      1,
			deletedAt:      0,
			status:         VersionGarbage,
			readTimestamp:  10,
			expectedVisible: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			v := &Version{
				CreatedAt: tt.createdAt,
				DeletedAt: tt.deletedAt,
				Status:    tt.status,
			}
			if got := v.IsVisible(tt.readTimestamp); got != tt.expectedVisible {
				t.Errorf("IsVisible(%d) = %v, want %v", tt.readTimestamp, got, tt.expectedVisible)
			}
		})
	}
}
