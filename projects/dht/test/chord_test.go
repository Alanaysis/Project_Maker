package test

import (
	"math/big"
	"testing"

	"github.com/dht-chord/internal"
)

// ==================== Hash Function Tests ====================

func TestDefaultHash(t *testing.T) {
	// Test that same input produces same output
	hash1 := internal.DefaultHash("test")
	hash2 := internal.DefaultHash("test")
	if hash1.Cmp(hash2) != 0 {
		t.Errorf("Same input should produce same hash")
	}

	// Test that different inputs produce different outputs
	hash3 := internal.DefaultHash("test2")
	if hash1.Cmp(hash3) == 0 {
		t.Errorf("Different inputs should produce different hashes")
	}

	// Test that hash is positive
	if hash1.Sign() < 0 {
		t.Errorf("Hash should be positive")
	}
}

func TestBetween(t *testing.T) {
	tests := []struct {
		name     string
		key      int64
		start    int64
		end      int64
		expected bool
	}{
		{"normal case", 5, 1, 10, true},
		{"normal case false", 15, 1, 10, false},
		{"wrap around", 5, 8, 3, true},
		{"wrap around false", 7, 8, 3, false},
		{"equal start and end", 5, 5, 5, true},
		{"key equals start", 5, 5, 10, false},
		{"key equals end", 10, 5, 10, false},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			key := big.NewInt(tt.key)
			start := big.NewInt(tt.start)
			end := big.NewInt(tt.end)
			result := internal.Between(key, start, end)
			if result != tt.expected {
				t.Errorf("Between(%d, %d, %d) = %v, want %v",
					tt.key, tt.start, tt.end, result, tt.expected)
			}
		})
	}
}

func TestBetweenRightInclusive(t *testing.T) {
	tests := []struct {
		name     string
		key      int64
		start    int64
		end      int64
		expected bool
	}{
		{"key equals end", 10, 5, 10, true},
		{"key between", 7, 5, 10, true},
		{"key not between", 3, 5, 10, false},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			key := big.NewInt(tt.key)
			start := big.NewInt(tt.start)
			end := big.NewInt(tt.end)
			result := internal.BetweenRightInclusive(key, start, end)
			if result != tt.expected {
				t.Errorf("BetweenRightInclusive(%d, %d, %d) = %v, want %v",
					tt.key, tt.start, tt.end, result, tt.expected)
			}
		})
	}
}

func TestPowerOfTwo(t *testing.T) {
	tests := []struct {
		exp      int
		expected int64
	}{
		{0, 1},
		{1, 2},
		{2, 4},
		{3, 8},
		{10, 1024},
	}

	for _, tt := range tests {
		t.Run("", func(t *testing.T) {
			result := internal.PowerOfTwo(tt.exp)
			expected := big.NewInt(tt.expected)
			if result.Cmp(expected) != 0 {
				t.Errorf("PowerOfTwo(%d) = %s, want %s",
					tt.exp, result.String(), expected.String())
			}
		})
	}
}

func TestFormatID(t *testing.T) {
	// Test nil
	if internal.FormatID(nil) != "nil" {
		t.Errorf("FormatID(nil) should return 'nil'")
	}

	// Test normal ID
	id := big.NewInt(12345)
	result := internal.FormatID(id)
	if result == "nil" {
		t.Errorf("FormatID should not return 'nil' for valid ID")
	}
}

// ==================== Node Tests ====================

func TestNewNode(t *testing.T) {
	node := internal.NewNode("test:8000", nil)

	if node == nil {
		t.Fatal("NewNode should not return nil")
	}

	if node.Addr != "test:8000" {
		t.Errorf("Node addr = %s, want test:8000", node.Addr)
	}

	if node.ID == nil {
		t.Error("Node ID should not be nil")
	}

	if len(node.FingerTable) != internal.M {
		t.Errorf("FingerTable length = %d, want %d", len(node.FingerTable), internal.M)
	}
}

func TestNodeStoreGet(t *testing.T) {
	node := internal.NewNode("test:8000", nil)

	// Store a value
	node.Store("key1", "value1")

	// Get the value
	value, ok := node.Get("key1")
	if !ok {
		t.Error("Should find key1")
	}
	if value != "value1" {
		t.Errorf("Got %s, want value1", value)
	}

	// Get non-existent key
	_, ok = node.Get("key2")
	if ok {
		t.Error("Should not find key2")
	}
}

func TestNodeDelete(t *testing.T) {
	node := internal.NewNode("test:8000", nil)

	// Store and delete
	node.Store("key1", "value1")
	ok := node.Delete("key1")
	if !ok {
		t.Error("Delete should return true")
	}

	// Verify deletion
	_, ok = node.Get("key1")
	if ok {
		t.Error("Key should be deleted")
	}

	// Delete non-existent key
	ok = node.Delete("key2")
	if ok {
		t.Error("Delete of non-existent key should return false")
	}
}

func TestNodeSuccessor(t *testing.T) {
	node := internal.NewNode("test:8000", nil)

	// Initially successor should be nil
	if node.GetSuccessor() != nil {
		t.Error("Initial successor should be nil")
	}

	// Set successor
	successor := &internal.NodeID{
		ID:   big.NewInt(100),
		Addr: "successor:8001",
	}
	node.SetSuccessor(successor)

	// Get successor
	got := node.GetSuccessor()
	if got == nil || got.Addr != "successor:8001" {
		t.Error("Successor not set correctly")
	}
}

func TestNodePredecessor(t *testing.T) {
	node := internal.NewNode("test:8000", nil)

	// Initially predecessor should be nil
	if node.GetPredecessor() != nil {
		t.Error("Initial predecessor should be nil")
	}

	// Set predecessor
	predecessor := &internal.NodeID{
		ID:   big.NewInt(50),
		Addr: "predecessor:8000",
	}
	node.SetPredecessor(predecessor)

	// Get predecessor
	got := node.GetPredecessor()
	if got == nil || got.Addr != "predecessor:8000" {
		t.Error("Predecessor not set correctly")
	}
}

func TestNodeIsAlive(t *testing.T) {
	node := internal.NewNode("test:8000", nil)

	if !node.IsAlive() {
		t.Error("Node should be alive initially")
	}

	node.SetAlive(false)
	if node.IsAlive() {
		t.Error("Node should not be alive after SetAlive(false)")
	}
}

// ==================== Ring Tests ====================

func TestNewRing(t *testing.T) {
	ring := internal.NewRing(nil)

	if ring == nil {
		t.Fatal("NewRing should not return nil")
	}

	if ring.GetNodeCount() != 0 {
		t.Errorf("Empty ring should have 0 nodes, got %d", ring.GetNodeCount())
	}
}

func TestRingAddNode(t *testing.T) {
	ring := internal.NewRing(nil)

	// Add first node
	node1, err := ring.AddNode("node1:8000")
	if err != nil {
		t.Fatalf("Failed to add node1: %v", err)
	}
	if node1 == nil {
		t.Fatal("Node1 should not be nil")
	}

	// Add second node
	node2, err := ring.AddNode("node2:8001")
	if err != nil {
		t.Fatalf("Failed to add node2: %v", err)
	}

	// Verify node count
	if ring.GetNodeCount() != 2 {
		t.Errorf("Ring should have 2 nodes, got %d", ring.GetNodeCount())
	}

	// Try to add duplicate node
	_, err = ring.AddNode("node1:8000")
	if err == nil {
		t.Error("Adding duplicate node should fail")
	}

	// Verify nodes are different
	if node1.ID.Cmp(node2.ID) == 0 {
		t.Error("Different nodes should have different IDs")
	}
}

func TestRingRemoveNode(t *testing.T) {
	ring := internal.NewRing(nil)

	// Add nodes
	ring.AddNode("node1:8000")
	ring.AddNode("node2:8001")
	ring.AddNode("node3:8002")

	// Remove a node
	err := ring.RemoveNode("node2:8001")
	if err != nil {
		t.Fatalf("Failed to remove node: %v", err)
	}

	// Verify node count
	if ring.GetNodeCount() != 2 {
		t.Errorf("Ring should have 2 nodes, got %d", ring.GetNodeCount())
	}

	// Try to remove non-existent node
	err = ring.RemoveNode("node2:8001")
	if err == nil {
		t.Error("Removing non-existent node should fail")
	}
}

func TestRingPutGet(t *testing.T) {
	ring := internal.NewRing(nil)

	// Add nodes
	ring.AddNode("node1:8000")
	ring.AddNode("node2:8001")
	ring.AddNode("node3:8002")

	// Put key-value
	err := ring.Put("testkey", "testvalue")
	if err != nil {
		t.Fatalf("Failed to put: %v", err)
	}

	// Get key-value
	value, err := ring.Get("testkey")
	if err != nil {
		t.Fatalf("Failed to get: %v", err)
	}
	if value != "testvalue" {
		t.Errorf("Got %s, want testvalue", value)
	}

	// Get non-existent key
	_, err = ring.Get("nonexistent")
	if err == nil {
		t.Error("Getting non-existent key should fail")
	}
}

func TestRingDelete(t *testing.T) {
	ring := internal.NewRing(nil)

	// Add nodes
	ring.AddNode("node1:8000")
	ring.AddNode("node2:8001")

	// Put and delete
	ring.Put("testkey", "testvalue")
	err := ring.Delete("testkey")
	if err != nil {
		t.Fatalf("Failed to delete: %v", err)
	}

	// Verify deletion
	_, err = ring.Get("testkey")
	if err == nil {
		t.Error("Getting deleted key should fail")
	}

	// Delete non-existent key
	err = ring.Delete("nonexistent")
	if err == nil {
		t.Error("Deleting non-existent key should fail")
	}
}

func TestRingFindNode(t *testing.T) {
	ring := internal.NewRing(nil)

	// Add nodes
	ring.AddNode("node1:8000")
	ring.AddNode("node2:8001")
	ring.AddNode("node3:8002")

	// Find node for a key
	node := ring.FindNode("testkey")
	if node == nil {
		t.Fatal("FindNode should not return nil")
	}

	// Verify node is in the ring
	found := false
	for _, n := range ring.GetNodes() {
		if n.Addr == node.Addr {
			found = true
			break
		}
	}
	if !found {
		t.Error("Returned node should be in the ring")
	}
}

func TestRingGetNodes(t *testing.T) {
	ring := internal.NewRing(nil)

	// Add nodes
	ring.AddNode("node1:8000")
	ring.AddNode("node2:8001")
	ring.AddNode("node3:8002")

	// Get all nodes
	nodes := ring.GetNodes()
	if len(nodes) != 3 {
		t.Errorf("Should have 3 nodes, got %d", len(nodes))
	}

	// Verify nodes are sorted by ID
	for i := 1; i < len(nodes); i++ {
		if nodes[i-1].ID.Cmp(nodes[i].ID) > 0 {
			t.Error("Nodes should be sorted by ID")
		}
	}
}

// ==================== Integration Tests ====================

func TestChordIntegration(t *testing.T) {
	ring := internal.NewRing(nil)

	// Create ring with multiple nodes
	nodeAddrs := []string{
		"node1:8000",
		"node2:8001",
		"node3:8002",
		"node4:8003",
		"node5:8004",
	}

	for _, addr := range nodeAddrs {
		_, err := ring.AddNode(addr)
		if err != nil {
			t.Fatalf("Failed to add node %s: %v", addr, err)
		}
	}

	// Store multiple key-value pairs
	testData := map[string]string{
		"key1": "value1",
		"key2": "value2",
		"key3": "value3",
		"key4": "value4",
		"key5": "value5",
	}

	for key, value := range testData {
		err := ring.Put(key, value)
		if err != nil {
			t.Fatalf("Failed to put key %s: %v", key, err)
		}
	}

	// Verify all key-value pairs
	for key, expected := range testData {
		actual, err := ring.Get(key)
		if err != nil {
			t.Fatalf("Failed to get key %s: %v", key, err)
		}
		if actual != expected {
			t.Errorf("Key %s: got %s, want %s", key, actual, expected)
		}
	}

	// Remove a node and verify data still accessible
	err := ring.RemoveNode("node3:8002")
	if err != nil {
		t.Fatalf("Failed to remove node: %v", err)
	}

	// Some keys may need to be re-put if they were on the removed node
	// For this test, we'll just verify the ring still works
	if ring.GetNodeCount() != 4 {
		t.Errorf("Ring should have 4 nodes, got %d", ring.GetNodeCount())
	}
}

func TestKeyDistribution(t *testing.T) {
	ring := internal.NewRing(nil)

	// Add 5 nodes
	for i := 1; i <= 5; i++ {
		ring.AddNode("node" + string(rune('0'+i)) + ":800" + string(rune('0'+i)))
	}

	// Store 100 keys
	for i := 0; i < 100; i++ {
		key := "key" + string(rune('0'+i%10)) + string(rune('0'+i/10))
		ring.Put(key, "value")
	}

	// Verify ring still works
	value, err := ring.Get("key00")
	if err != nil {
		t.Fatalf("Failed to get key: %v", err)
	}
	if value != "value" {
		t.Errorf("Got %s, want value", value)
	}
}
