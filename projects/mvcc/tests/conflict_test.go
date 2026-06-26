package mvcc

import (
	"testing"
)

// TestConflictDetectorWriteWrite tests write-write conflict detection.
func TestConflictDetectorWriteWrite(t *testing.T) {
	detector := NewConflictDetector()

	// Create two transactions writing to the same key
	tx1 := NewTransaction(1, 10)
	tx2 := NewTransaction(2, 10)

	tx1.WriteSet["key1"] = []byte("v1")
	tx2.WriteSet["key1"] = []byte("v2")

	detector.RecordWrite(1, "key1")
	detector.RecordWrite(2, "key1")

	// Should detect conflict
	conflict := detector.CheckWriteWrite(tx1, tx2)
	if conflict == nil {
		t.Error("expected write-write conflict, got none")
	}
	if conflict.Type != ConflictWriteWrite {
		t.Errorf("expected ConflictWriteWrite, got %v", conflict.Type)
	}
	if conflict.Key != "key1" {
		t.Errorf("expected key 'key1', got %q", conflict.Key)
	}
}

// TestConflictDetectorNoWriteWrite tests no conflict when writing different keys.
func TestConflictDetectorNoWriteWrite(t *testing.T) {
	detector := NewConflictDetector()

	tx1 := NewTransaction(1, 10)
	tx2 := NewTransaction(2, 10)

	tx1.WriteSet["key1"] = []byte("v1")
	tx2.WriteSet["key2"] = []byte("v2")

	detector.RecordWrite(1, "key1")
	detector.RecordWrite(2, "key2")

	conflict := detector.CheckWriteWrite(tx1, tx2)
	if conflict != nil {
		t.Errorf("expected no conflict, got: %v", conflict)
	}
}

// TestConflictDetectorReadWrite tests read-write conflict detection.
func TestConflictDetectorReadWrite(t *testing.T) {
	detector := NewConflictDetector()

	tx1 := NewTransaction(1, 10)
	tx2 := NewTransaction(2, 10)

	tx1.ReadSet["key1"] = 10
	tx2.WriteSet["key1"] = []byte("new_value")

	detector.RecordWrite(2, "key1")

	// Should detect conflict because tx2 wrote after tx1 read
	conflict := detector.CheckReadWrite(tx1, tx2)
	if conflict == nil {
		t.Error("expected read-write conflict, got none")
	}
	if conflict.Type != ConflictReadWrite {
		t.Errorf("expected ConflictReadWrite, got %v", conflict.Type)
	}
}

// TestConflictDetectorNoReadWrite tests no conflict when no overlapping access.
func TestConflictDetectorNoReadWrite(t *testing.T) {
	detector := NewConflictDetector()

	tx1 := NewTransaction(1, 10)
	tx2 := NewTransaction(2, 10)

	tx1.ReadSet["key1"] = 10
	tx2.WriteSet["key2"] = []byte("new_value")

	detector.RecordWrite(2, "key2")

	conflict := detector.CheckReadWrite(tx1, tx2)
	if conflict != nil {
		t.Errorf("expected no conflict, got: %v", conflict)
	}
}

// TestConflictDetectorWaitForGraph tests wait-for graph operations.
func TestConflictDetectorWaitForGraph(t *testing.T) {
	detector := NewConflictDetector()

	// Add edges: T1 waits for T2, T2 waits for T3
	detector.AddWaitEdge(1, 2)
	detector.AddWaitEdge(2, 3)

	// No cycle yet
	if detector.HasCycle() {
		t.Error("expected no cycle, got one")
	}

	// Add edge to create cycle: T3 waits for T1
	detector.AddWaitEdge(3, 1)

	// Now there should be a cycle
	if !detector.HasCycle() {
		t.Error("expected cycle, got none")
	}

	cycle := detector.DetectCycle()
	if cycle == nil {
		t.Error("expected non-nil cycle")
	}
}

// TestConflictDetectorRemoveTransaction tests removing a transaction from the graph.
func TestConflictDetectorRemoveTransaction(t *testing.T) {
	detector := NewConflictDetector()

	detector.AddWaitEdge(1, 2)
	detector.AddWaitEdge(2, 3)
	detector.AddWaitEdge(3, 1)

	// Remove T2 - should break the cycle
	detector.RemoveTransaction(2)

	if detector.HasCycle() {
		t.Error("expected no cycle after removing T2")
	}
}

// TestConflictError tests ConflictError.Error().
func TestConflictError(t *testing.T) {
	conflict := &ConflictError{
		Type:     ConflictWriteWrite,
		Key:      "key1",
		ReaderTx: 1,
		WriterTx: 2,
	}
	errStr := conflict.Error()
	if errStr == "" {
		t.Error("ConflictError.Error() should not be empty")
	}
}

// TestConflictTypeString tests ConflictType.String().
func TestConflictTypeString(t *testing.T) {
	tests := []struct {
		ctype  ConflictType
		expect string
	}{
		{ConflictWriteWrite, "WRITE-WRITE"},
		{ConflictReadWrite, "READ-WRITE"},
		{ConflictSerialization, "SERIALIZATION"},
		{ConflictType(99), "UNKNOWN"},
	}

	for _, tt := range tests {
		if got := tt.ctype.String(); got != tt.expect {
			t.Errorf("ConflictType.String() = %q, want %q", got, tt.expect)
		}
	}
}

// TestConflictDetectorWriteSetTracking tests write set tracking.
func TestConflictDetectorWriteSetTracking(t *testing.T) {
	detector := NewConflictDetector()

	detector.RecordWrite(1, "key1")
	detector.RecordWrite(1, "key2")
	detector.RecordWrite(2, "key2")
	detector.RecordWrite(2, "key3")

	// Check overlap on key2
	tx1 := NewTransaction(1, 10)
	tx1.WriteSet["key2"] = []byte("v1")
	tx2 := NewTransaction(2, 10)
	tx2.WriteSet["key2"] = []byte("v2")

	conflict := detector.CheckWriteWrite(tx1, tx2)
	if conflict == nil {
		t.Error("expected conflict on key2")
	}
}

// TestConflictDetectorReadCommits tests SSI read commit tracking.
func TestConflictDetectorReadCommits(t *testing.T) {
	detector := NewConflictDetector()

	// T1 reads a version committed by T2
	detector.RecordRead(1, 2, 100)

	// Check readCommits
	if detector.readCommits == nil {
		t.Fatal("readCommits should not be nil")
	}
	if detector.readCommits[1] == nil {
		t.Fatal("readCommits[1] should not be nil")
	}
	if detector.readCommits[1][2] != 100 {
		t.Errorf("expected readCommits[1][2] = 100, got %d", detector.readCommits[1][2])
	}
}

// TestConflictDetectorMultipleReadCommits tests updating read commits with latest timestamp.
func TestConflictDetectorMultipleReadCommits(t *testing.T) {
	detector := NewConflictDetector()

	detector.RecordRead(1, 2, 100)
	detector.RecordRead(1, 2, 200) // Should update to latest

	if detector.readCommits[1][2] != 200 {
		t.Errorf("expected latest timestamp 200, got %d", detector.readCommits[1][2])
	}
}
