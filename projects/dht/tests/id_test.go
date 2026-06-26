package chord

import (
	"testing"
)

func TestNextID(t *testing.T) {
	if NextID(0) != 1 {
		t.Errorf("NextID(0) = %d, want 1", NextID(0))
	}
	if NextID(RingSize-1) != 0 {
		t.Errorf("NextID(RingSize-1) = %d, want 0", NextID(RingSize-1))
	}
}

func TestPrevID(t *testing.T) {
	if PrevID(1) != 0 {
		t.Errorf("PrevID(1) = %d, want 0", PrevID(1))
	}
	if PrevID(0) != RingSize-1 {
		t.Errorf("PrevID(0) = %d, want RingSize-1", PrevID(0))
	}
}

func TestDistance(t *testing.T) {
	tests := []struct {
		id1, id2, want NodeID
	}{
		{0, 10, 10},
		{10, 0, RingSize - 10},
		{5, 5, 0},
		{0, RingSize - 1, RingSize - 1},
		{RingSize - 1, 0, 1},
	}
	
	for _, tt := range tests {
		got := Distance(tt.id1, tt.id2)
		if got != tt.want {
			t.Errorf("Distance(%d, %d) = %d, want %d", tt.id1, tt.id2, got, tt.want)
		}
	}
}

func TestGenerateNodeID(t *testing.T) {
	id1 := GenerateNodeID("node-1")
	id2 := GenerateNodeID("node-2")
	
	// Different identifiers should produce different IDs
	if id1 == id2 {
		t.Errorf("Different identifiers produced same ID: %d", id1)
	}
	
	// Same identifier should produce same ID
	id3 := GenerateNodeID("node-1")
	if id1 != id3 {
		t.Errorf("Same identifier produced different IDs: %d vs %d", id1, id3)
	}
	
	// ID should be within ring bounds
	if id1 >= RingSize {
		t.Errorf("NodeID %d exceeds ring size %d", id1, RingSize)
	}
}

func TestGenerateKeyID(t *testing.T) {
	keyID1 := GenerateKeyID("key1")
	keyID2 := GenerateKeyID("key2")
	
	if keyID1 == keyID2 {
		t.Errorf("Different keys produced same key ID")
	}
	
	if keyID1 >= RingSize {
		t.Errorf("KeyID %d exceeds ring size %d", keyIDID, RingSize)
	}
}

func TestIDFromString(t *testing.T) {
	id, err := IDFromString("12345")
	if err != nil {
		t.Fatalf("IDFromString(12345) error: %v", err)
	}
	if id != 12345 {
		t.Errorf("IDFromString(12345) = %d, want 12345", id)
	}
	
	_, err = IDFromString("invalid")
	if err == nil {
		t.Error("IDFromString(invalid) should return error")
	}
}

func TestIsInRange(t *testing.T) {
	tests := []struct {
		start, end, target NodeID
		want               bool
	}{
		{0, 10, 5, true},
		{0, 10, 0, false},
		{0, 10, 10, true},
		{0, 10, 11, false},
		{10, 5, 12, true},   // wrap-around
		{10, 5, 3, true},    // wrap-around
		{10, 5, 7, false},   // not in range
		{10, 10, 10, true},  // same start/end
		{10, 10, 5, false},  // same start/end, different target
	}
	
	for _, tt := range tests {
		got := IsInRange(tt.start, tt.end, tt.target)
		if got != tt.want {
			t.Errorf("IsInRange(%d, %d, %d) = %v, want %v",
				tt.start, tt.end, tt.target, got, tt.want)
		}
	}
}

func TestComputeFingerTableSize(t *testing.T) {
	size := ComputeFingerTableSize()
	if size != 16 {
		t.Errorf("Finger table size = %d, want 16", size)
	}
}

func TestFingerIndex(t *testing.T) {
	// Finger table entry i covers [id + 2^(i-1), id + 2^i)
	tests := []struct {
		id     NodeID
		i      int
		wantMin NodeID
		wantMax NodeID
	}{
		{0, 1, 1, 2},
		{0, 2, 2, 4},
		{0, 3, 4, 8},
		{100, 1, 101, 102},
	}
	
	for _, tt := range tests {
		got := FingerIndex(tt.id, tt.i)
		if got < tt.wantMin || got >= tt.wantMax {
			t.Errorf("FingerIndex(%d, %d) = %d, want in [%d, %d)",
				tt.id, tt.i, got, tt.wantMin, tt.wantMax)
		}
	}
}

func TestMinDistance(t *testing.T) {
	tests := []struct {
		a, b NodeID
		want NodeID
	}{
		{0, 10, 10},
		{10, 0, RingSize - 10},
		{5, 5, 0},
	}
	
	for _, tt := range tests {
		got := MinDistance(tt.a, tt.b)
		if got != tt.want {
			t.Errorf("MinDistance(%d, %d) = %d, want %d", tt.a, tt.b, got, tt.want)
		}
	}
}

func TestVerifyRing(t *testing.T) {
	// Empty ring
	if !VerifyRing(nil) {
		t.Error("Empty ring should be valid")
	}
	
	// Single node
	if !VerifyRing([]NodeID{100}) {
		t.Error("Single node ring should be valid")
	}
	
	// Two nodes
	if !VerifyRing([]NodeID{100, 200}) {
		t.Error("Two node ring should be valid")
	}
	
	// Duplicate nodes
	if VerifyRing([]NodeID{100, 100, 200}) {
		t.Error("Ring with duplicate nodes should be invalid")
	}
}

func TestAverageDistance(t *testing.T) {
	// With many uniformly distributed nodes, average distance should be ~RingSize/numNodes
	nodes := []NodeID{0, 1000, 2000, 3000, 4000}
	avg := AverageDistance(nodes)
	expected := float64(RingSize) / float64(len(nodes))
	
	if avg < expected*0.5 || avg > expected*1.5 {
		t.Errorf("AverageDistance = %f, expected ~%f", avg, expected)
	}
}

func TestCountKeysPerNode(t *testing.T) {
	tests := []struct {
		totalKeys, numNodes, want int
	}{
		{100, 10, 10},
		{100, 3, 33},
		{10, 100, 0},
		{100, 0, 0},
	}
	
	for _, tt := range tests {
		got := CountKeysPerNode(tt.totalKeys, tt.numNodes)
		if got != tt.want {
			t.Errorf("CountKeysPerNode(%d, %d) = %d, want %d",
				tt.totalKeys, tt.numNodes, got, tt.want)
		}
	}
}

func TestHashToID(t *testing.T) {
	id1 := HashToID("test-node-1")
	id2 := HashToID("test-node-1")
	
	if id1 != id2 {
		t.Errorf("Same input produced different IDs: %d vs %d", id1, id2)
	}
	
	if id1 >= RingSize {
		t.Errorf("Hashed ID %d exceeds ring size", id1)
	}
}

func TestComputeStats(t *testing.T) {
	nodes := []NodeID{100, 500, 1000, 2000, 5000}
	keys := []NodeID{150, 250, 600, 800, 1100, 1500, 2500, 6000}
	
	stats := ComputeStats(nodes, keys)
	
	if stats.TotalNodes != 5 {
		t.Errorf("TotalNodes = %d, want 5", stats.TotalNodes)
	}
	
	if stats.TotalKeys != 8 {
		t.Errorf("TotalKeys = %d, want 8", stats.TotalKeys)
	}
	
	if stats.MinKeysPerNode < 0 || stats.MaxKeysPerNode < 0 {
		t.Errorf("Invalid key counts: min=%d, max=%d", stats.MinKeysPerNode, stats.MaxKeysPerNode)
	}
}
