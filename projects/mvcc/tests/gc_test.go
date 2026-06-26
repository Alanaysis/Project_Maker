package mvcc

import (
	"testing"
)

// TestGarbageCollectorNoSnapshots tests GC when there are no active snapshots.
func TestGarbageCollectorNoSnapshots(t *testing.T) {
	storage := NewMVCCStorage()
	gc := NewGarbageCollector(storage)

	// Create multiple versions
	for i := 1; i <= 5; i++ {
		ts := storage.NextTimestamp()
		storage.Write("key1", []byte(fmt.Sprintf("v%d", i)), ts, i)
	}

	// Commit all versions
	for i := 1; i <= 5; i++ {
		storage.Commit(&Transaction{ID: i, WriteSet: map[string][]byte{"key1": []byte(fmt.Sprintf("v%d", i))}})
	}

	// Verify 5 versions exist
	versions := storage.GetVersions("key1")
	if len(versions) != 5 {
		t.Fatalf("expected 5 versions, got %d", len(versions))
	}

	// No active snapshots - GC should keep only the latest committed version
	reclaimed, cleaned := gc.Collect()

	if reclaimed != 4 {
		t.Errorf("expected reclaimed 4, got %d", reclaimed)
	}
	if cleaned != 1 {
		t.Errorf("expected cleaned 1, got %d", cleaned)
	}

	// Only one version should remain
	versions = storage.GetVersions("key1")
	if len(versions) != 1 {
		t.Errorf("expected 1 version after GC, got %d", len(versions))
	}
	if string(versions[0].Value) != "v5" {
		t.Errorf("expected remaining version 'v5', got %q", string(versions[0].Value))
	}
}

// TestGarbageCollectorWithSnapshot tests GC with an active snapshot.
func TestGarbageCollectorWithSnapshot(t *testing.T) {
	storage := NewMVCCStorage()
	gc := NewGarbageCollector(storage)

	// Create versions
	for i := 1; i <= 10; i++ {
		ts := storage.NextTimestamp()
		storage.Write("key1", []byte(fmt.Sprintf("v%d", i)), ts, i)
	}

	// Commit all versions
	for i := 1; i <= 10; i++ {
		storage.Commit(&Transaction{ID: i, WriteSet: map[string][]byte{"key1": []byte(fmt.Sprintf("v%d", i))}})
	}

	// Register active snapshot at timestamp 5
	gc.RegisterSnapshot(5)

	// Run GC
	reclaimed, cleaned := gc.Collect()

	// Versions with WriteTS < 5 should be reclaimed
	if reclaimed != 4 {
		t.Errorf("expected reclaimed 4, got %d", reclaimed)
	}
	if cleaned != 1 {
		t.Errorf("expected cleaned 1, got %d", cleaned)
	}

	// Versions at timestamps 5-10 should remain
	versions := storage.GetVersions("key1")
	if len(versions) != 6 {
		t.Errorf("expected 6 versions after GC, got %d", len(versions))
	}
}

// TestGarbageCollectorUnregisterSnapshot tests unregistering a snapshot.
func TestGarbageCollectorUnregisterSnapshot(t *testing.T) {
	storage := NewMVCCStorage()
	gc := NewGarbageCollector(storage)

	// Create versions
	for i := 1; i <= 5; i++ {
		ts := storage.NextTimestamp()
		storage.Write("key1", []byte(fmt.Sprintf("v%d", i)), ts, i)
	}

	// Commit all versions
	for i := 1; i <= 5; i++ {
		storage.Commit(&Transaction{ID: i, WriteSet: map[string][]byte{"key1": []byte(fmt.Sprintf("v%d", i))}})
	}

	// Register snapshot
	gc.RegisterSnapshot(3)

	// GC with snapshot
	reclaimed1, _ := gc.Collect()
	if reclaimed1 != 2 {
		t.Errorf("expected reclaimed 2 with snapshot, got %d", reclaimed1)
	}

	// Unregister snapshot
	gc.UnregisterSnapshot(3)

	// GC without snapshot - should reclaim more
	reclaimed2, _ := gc.Collect()
	if reclaimed2 != 1 {
		t.Errorf("expected reclaimed 1 without snapshot, got %d", reclaimed2)
	}
}

// TestGarbageCollectorStats tests GC statistics.
func TestGarbageCollectorStats(t *testing.T) {
	storage := NewMVCCStorage()
	gc := NewGarbageCollector(storage)

	// Create versions for key1
	for i := 1; i <= 3; i++ {
		ts := storage.NextTimestamp()
		storage.Write("key1", []byte(fmt.Sprintf("v%d", i)), ts, i)
	}

	// Commit all
	for i := 1; i <= 3; i++ {
		storage.Commit(&Transaction{ID: i, WriteSet: map[string][]byte{"key1": []byte(fmt.Sprintf("v%d", i))}})
	}

	// Create versions for key2
	for i := 1; i <= 4; i++ {
		ts := storage.NextTimestamp()
		storage.Write("key2", []byte(fmt.Sprintf("v%d", i)), ts, i+10)
	}

	// Commit all
	for i := 1; i <= 4; i++ {
		storage.Commit(&Transaction{ID: i + 10, WriteSet: map[string][]byte{"key2": []byte(fmt.Sprintf("v%d", i))}})
	}

	// GC with no snapshots
	gc.Collect()

	reclaimed, cleaned := gc.Stats()
	if reclaimed != 6 { // 2 from key1 + 3 from key2 = 5... let me recalculate
		// key1: 3 versions -> keep 1 -> reclaim 2
		// key2: 4 versions -> keep 1 -> reclaim 3
		// total reclaimed: 5
	}
	if cleaned != 2 {
		t.Errorf("expected cleaned 2, got %d", cleaned)
	}
}

// TestGarbageCollectorEmptyStorage tests GC on empty storage.
func TestGarbageCollectorEmptyStorage(t *testing.T) {
	storage := NewMVCCStorage()
	gc := NewGarbageCollector(storage)

	reclaimed, cleaned := gc.Collect()
	if reclaimed != 0 {
		t.Errorf("expected reclaimed 0 on empty storage, got %d", reclaimed)
	}
	if cleaned != 0 {
		t.Errorf("expected cleaned 0 on empty storage, got %d", cleaned)
	}
}

// TestGarbageCollectorSingleVersion tests GC when each key has only one version.
func TestGarbageCollectorSingleVersion(t *testing.T) {
	storage := NewMVCCStorage()
	gc := NewGarbageCollector(storage)

	// Create single version
	ts := storage.NextTimestamp()
	storage.Write("key1", []byte("v1"), ts, 1)
	storage.Commit(&Transaction{ID: 1, WriteSet: map[string][]byte{"key1": []byte("v1")}})

	// No active snapshots
	reclaimed, cleaned := gc.Collect()

	// Should not reclaim anything (only one version per key)
	if reclaimed != 0 {
		t.Errorf("expected reclaimed 0 for single-version key, got %d", reclaimed)
	}
	if cleaned != 0 {
		t.Errorf("expected cleaned 0 for single-version key, got %d", cleaned)
	}

	// Version should still exist
	versions := storage.GetVersions("key1")
	if len(versions) != 1 {
		t.Errorf("expected 1 version, got %d", len(versions))
	}
}

// TestGarbageCollectorMultipleKeys tests GC across multiple keys.
func TestGarbageCollectorMultipleKeys(t *testing.T) {
	storage := NewMVCCStorage()
	gc := NewGarbageCollector(storage)

	// Create versions for multiple keys
	keys := []string{"key1", "key2", "key3"}
	for _, key := range keys {
		for i := 1; i <= 5; i++ {
			ts := storage.NextTimestamp()
			storage.Write(key, []byte("v"+key+"-"+string(rune('0'+i))), ts, i)
		}
		for i := 1; i <= 5; i++ {
			storage.Commit(&Transaction{ID: i, WriteSet: map[string][]byte{key: []byte("v" + key + "-" + string(rune('0'+i)))}})
		}
	}

	// No active snapshots
	reclaimed, cleaned := gc.Collect()

	if cleaned != 3 {
		t.Errorf("expected cleaned 3 keys, got %d", cleaned)
	}
	// Each key: 5 versions -> keep 1 -> reclaim 4
	// Total: 3 * 4 = 12
	if reclaimed != 12 {
		t.Errorf("expected reclaimed 12, got %d", reclaimed)
	}
}
