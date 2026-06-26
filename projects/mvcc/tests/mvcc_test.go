package mvcc

import (
	"fmt"
	"testing"
)

// TestTransactionLifecycle tests the basic transaction lifecycle.
func TestTransactionLifecycle(t *testing.T) {
	tx := NewTransaction(1, 10)

	if tx.ID != 1 {
		t.Errorf("expected ID 1, got %d", tx.ID)
	}
	if tx.State != StateActive {
		t.Errorf("expected StateActive, got %v", tx.State)
	}
	if tx.StartTime != 10 {
		t.Errorf("expected StartTime 10, got %d", tx.StartTime)
	}

	// Create snapshot
	tx.CreateSnapshot(10)
	if tx.State != StateSnapshotRead {
		t.Errorf("expected StateSnapshotRead after CreateSnapshot, got %v", tx.State)
	}
	if tx.ReadTimestamp != 10 {
		t.Errorf("expected ReadTimestamp 10, got %d", tx.ReadTimestamp)
	}

	// Add to read/write sets
	tx.AddToReadSet("key1", 10)
	tx.AddToWriteSet("key2", []byte("value"))

	readSet := tx.GetReadSet()
	if len(readSet) != 1 || readSet["key1"] != 10 {
		t.Errorf("unexpected read set: %v", readSet)
	}

	writeSet := tx.GetWriteSet()
	if len(writeSet) != 1 || string(writeSet["key2"]) != "value" {
		t.Errorf("unexpected write set: %v", writeSet)
	}
}

// TestTransactionStates tests transaction state transitions.
func TestTransactionStates(t *testing.T) {
	tx := NewTransaction(1, 10)

	if tx.IsCommitted() {
		t.Error("should not be committed initially")
	}
	if tx.IsAborted() {
		t.Error("should not be aborted initially")
	}

	// Commit
	tx.State = StateCommitted
	tx.CommitTime = 20
	if !tx.IsCommitted() {
		t.Error("should be committed after setting StateCommitted")
	}

	// Abort
	tx.State = StateAborted
	if tx.IsAborted() {
		t.Error("should be aborted after setting StateAborted")
	}

	// Conflict
	tx.State = StateConflict
	if !tx.IsAborted() {
		t.Error("should be considered aborted when in conflict state")
	}
}

// TestTransactionStateString tests the String method of TransactionState.
func TestTransactionStateString(t *testing.T) {
	tests := []struct {
		state  TransactionState
		expect string
	}{
		{StateActive, "ACTIVE"},
		{StateCommitted, "COMMITTED"},
		{StateAborted, "ABORTED"},
		{StateSnapshotRead, "SNAPSHOT_READ"},
		{StateConflict, "CONFLICT"},
		{TransactionState(99), "UNKNOWN"},
	}

	for _, tt := range tests {
		if got := tt.state.String(); got != tt.expect {
			t.Errorf("state.String() = %q, want %q", got, tt.expect)
		}
	}
}

// TestMVCCStorageWriteRead tests basic write and read operations.
func TestMVCCStorageWriteRead(t *testing.T) {
	storage := NewMVCCStorage()

	// Write a value
	ts := storage.NextTimestamp()
	ver := storage.Write("key1", []byte("value1"), ts, 1)

	if ver.WriteTS != ts {
		t.Errorf("expected WriteTS %d, got %d", ts, ver.WriteTS)
	}
	if ver.WriterID != 1 {
		t.Errorf("expected WriterID 1, got %d", ver.WriterID)
	}
	if ver.Committed {
		t.Error("new version should not be committed initially")
	}

	// Read before commit (should not find uncommitted version)
	val, exists, err := storage.Read("key1", ts)
	if err != nil {
		t.Errorf("unexpected error: %v", err)
	}
	if exists {
		t.Error("should not find uncommitted version")
	}

	// Commit the version
	storage.Commit(&Transaction{ID: 1, WriteSet: map[string][]byte{"key1": []byte("value1")}})

	// Read after commit
	val, exists, err = storage.Read("key1", ts)
	if err != nil {
		t.Errorf("unexpected error: %v", err)
	}
	if !exists {
		t.Error("should find committed version")
	}
	if string(val) != "value1" {
		t.Errorf("expected value 'value1', got %q", string(val))
	}
}

// TestMVCCStorageVersionChain tests version chain management.
func TestMVCCStorageVersionChain(t *testing.T) {
	storage := NewMVCCStorage()

	// Write multiple versions
	for i := 1; i <= 5; i++ {
		ts := storage.NextTimestamp()
		storage.Write("key1", []byte(fmt.Sprintf("v%d", i)), ts, i)
	}

	// Commit all versions
	for i := 1; i <= 5; i++ {
		storage.Commit(&Transaction{ID: i, WriteSet: map[string][]byte{"key1": []byte(fmt.Sprintf("v%d", i))}})
	}

	// Read with different snapshot timestamps
	tests := []struct {
		snapshotTS Timestamp
		expect     string
	}{
		{1, "v1"},
		{2, "v2"},
		{3, "v3"},
		{4, "v4"},
		{5, "v5"},
		{6, "v5"}, // No newer version
		{0, ""},   // No visible version
	}

	for _, tt := range tests {
		val, exists, _ := storage.Read("key1", tt.snapshotTS)
		if tt.expect == "" {
			if exists {
				t.Errorf("snapshotTS=%d: expected not found, got %q", tt.snapshotTS, string(val))
			}
		} else {
			if !exists {
				t.Errorf("snapshotTS=%d: expected found, got not found", tt.snapshotTS)
			}
			if string(val) != tt.expect {
				t.Errorf("snapshotTS=%d: expected %q, got %q", tt.snapshotTS, tt.expect, string(val))
			}
		}
	}

	// Check version chain length
	versions := storage.GetVersions("key1")
	if len(versions) != 5 {
		t.Errorf("expected 5 versions, got %d", len(versions))
	}
}

// TestMVCCStorageNonExistentKey tests reading a non-existent key.
func TestMVCCStorageNonExistentKey(t *testing.T) {
	storage := NewMVCCStorage()

	val, exists, err := storage.Read("nonexistent", 10)
	if err != nil {
		t.Errorf("unexpected error: %v", err)
	}
	if exists {
		t.Error("should not find nonexistent key")
	}
	if val != nil {
		t.Errorf("expected nil value, got %q", string(val))
	}
}

// TestMVCCStorageRollback tests transaction rollback.
func TestMVCCStorageRollback(t *testing.T) {
	storage := NewMVCCStorage()

	// Write initial committed value
	ts := storage.NextTimestamp()
	storage.Write("key1", []byte("initial"), ts, 0)
	storage.Commit(&Transaction{ID: 0, WriteSet: map[string][]byte{"key1": []byte("initial")}})

	// Write uncommitted value
	ts = storage.NextTimestamp()
	tx := NewTransaction(1, ts)
	tx.WriteSet["key1"] = []byte("modified")
	storage.Write("key1", []byte("modified"), ts, 1)

	// Read should not see uncommitted value
	val, exists, _ := storage.Read("key1", ts)
	if exists {
		t.Error("should not see uncommitted value")
	}

	// Rollback
	storage.Rollback(tx)

	// Read should still not see the rolled-back value
	val, exists, _ = storage.Read("key1", ts)
	if exists {
		t.Error("should not see rolled-back value")
	}
	if string(val) != "initial" {
		t.Errorf("expected 'initial', got %q", string(val))
	}
}

// TestMVCCStorageTimestampMonotonicity tests that timestamps are strictly monotonic.
func TestMVCCStorageTimestampMonotonicity(t *testing.T) {
	storage := NewMVCCStorage()

	ts1 := storage.NextTimestamp()
	ts2 := storage.NextTimestamp()
	ts3 := storage.NextTimestamp()

	if ts1 >= ts2 || ts2 >= ts3 {
		t.Errorf("timestamps should be strictly monotonic: %d, %d, %d", ts1, ts2, ts3)
	}
}

// TestMVCCStorageGetAllKeys tests GetAllKeys.
func TestMVCCStorageGetAllKeys(t *testing.T) {
	storage := NewMVCCStorage()

	storage.Write("key1", []byte("v1"), 1, 0)
	storage.Write("key2", []byte("v2"), 2, 0)
	storage.Write("key3", []byte("v3"), 3, 0)

	keys := storage.GetAllKeys()
	if len(keys) != 3 {
		t.Errorf("expected 3 keys, got %d", len(keys))
	}

	keyMap := make(map[string]bool)
	for _, k := range keys {
		keyMap[k] = true
	}
	for _, expected := range []string{"key1", "key2", "key3"} {
		if !keyMap[expected] {
			t.Errorf("missing key: %s", expected)
		}
	}
}

// TestMVCCStorageVersionString tests Version.String().
func TestMVCCStorageVersionString(t *testing.T) {
	ver := &Version{
		Value:     []byte("test"),
		WriteTS:   10,
		ReadTS:    10,
		WriterID:  1,
		Committed: true,
	}
	s := ver.String()
	if s == "" {
		t.Error("Version.String() should not be empty")
	}
}


