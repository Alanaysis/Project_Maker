package chord

import (
	"testing"
)

func TestNewChordRing(t *testing.T) {
	ring := NewChordRing()
	
	if ring == nil {
		t.Fatal("NewChordRing() should not return nil")
	}
	
	if len(ring.GetNodes()) != 0 {
		t.Errorf("New ring should have 0 nodes, got %d", len(ring.GetNodes()))
	}
}

func TestChordRingAddNode(t *testing.T) {
	ring := NewChordRing()
	
	id := GenerateNodeID("test-node")
	node := NewNode(id, "127.0.0.1:8000")
	
	ring.AddNode(node)
	
	nodes := ring.GetNodes()
	if len(nodes) != 1 {
		t.Errorf("Ring should have 1 node, got %d", len(nodes))
	}
	
	retrieved, ok := ring.GetNode(id)
	if !ok {
		t.Error("Should be able to retrieve added node")
	}
	if retrieved.ID != id {
		t.Errorf("Retrieved node ID = %d, want %d", retrieved.ID, id)
	}
}

func TestChordRingGetNodeNotFound(t *testing.T) {
	ring := NewChordRing()
	
	_, ok := ring.GetNode(99999)
	if ok {
		t.Error("GetNode should return false for nonexistent node")
	}
}

func TestChordRingRemoveNode(t *testing.T) {
	ring := NewChordRing()
	
	id1 := GenerateNodeID("node-1")
	id2 := GenerateNodeID("node-2")
	
	node1 := NewNode(id1, "127.0.0.1:8001")
	node2 := NewNode(id2, "127.0.0.1:8002")
	
	ring.AddNode(node1)
	ring.AddNode(node2)
	
	if len(ring.GetNodes()) != 2 {
		t.Errorf("Ring should have 2 nodes, got %d", len(ring.GetNodes()))
	}
	
	ring.RemoveNode(id1)
	
	nodes := ring.GetNodes()
	if len(nodes) != 1 {
		t.Errorf("Ring should have 1 node after removal, got %d", len(nodes))
	}
	
	_, ok := ring.GetNode(id1)
	if ok {
		t.Error("Removed node should not be in ring")
	}
}

func TestChordRingLookup(t *testing.T) {
	ring := NewChordRing()
	
	// Add nodes
	for i := 0; i < 5; i++ {
		id := GenerateNodeID("node-10.0.0." + string(rune('1'+i)))
		node := NewNode(id, "10.0.0."+string(rune('1'+i)))
		ring.AddNode(node)
	}
	
	ring.Stabilize()
	
	// Look up a key
	node, hops := ring.Lookup("test-key")
	
	if node == nil {
		t.Error("Lookup should return a node")
	}
	
	if hops == 0 {
		t.Error("Lookup should take at least 1 hop")
	}
}

func TestChordRingStoreAndRetrieve(t *testing.T) {
	ring := NewChordRing()
	
	// Add nodes
	for i := 0; i < 5; i++ {
		id := GenerateNodeID("node-10.0.0." + string(rune('1'+i)))
		node := NewNode(id, "10.0.0."+string(rune('1'+i)))
		ring.AddNode(node)
	}
	
	ring.Stabilize()
	
	// Store a value
	ok := ring.Store("my-key", "my-value")
	if !ok {
		t.Error("Store should return true")
	}
	
	// Retrieve the value
	value, found := ring.Retrieve("my-key")
	if !found {
		t.Error("Retrieve should find the key")
	}
	if value != "my-value" {
		t.Errorf("Retrieve returned %s, want my-value", value)
	}
}

func TestChordRingDelete(t *testing.T) {
	ring := NewChordRing()
	
	// Add nodes
	for i := 0; i < 5; i++ {
		id := GenerateNodeID("node-10.0.0." + string(rune('1'+i)))
		node := NewNode(id, "10.0.0."+string(rune('1'+i)))
		ring.AddNode(node)
	}
	
	ring.Stabilize()
	
	// Store and delete
	ring.Store("del-key", "del-value")
	
	ok := ring.Delete("del-key")
	if !ok {
		t.Error("Delete should return true")
	}
	
	_, found := ring.Retrieve("del-key")
	if found {
		t.Error("Deleted key should not be found")
	}
}

func TestChordRingIntegrity(t *testing.T) {
	ring := NewChordRing()
	
	// Add nodes
	for i := 0; i < 5; i++ {
		id := GenerateNodeID("node-10.0.0." + string(rune('1'+i)))
		node := NewNode(id, "10.0.0."+string(rune('1'+i)))
		ring.AddNode(node)
	}
	
	ring.Stabilize()
	
	ok, issues := ring.VerifyRingIntegrity()
	if !ok {
		t.Errorf("Ring integrity check failed: %v", issues)
	}
}

func TestChordRingStabilize(t *testing.T) {
	ring := NewChordRing()
	
	// Add nodes
	for i := 0; i < 10; i++ {
		id := GenerateNodeID("node-10.0.0." + string(rune('1'+i)))
		node := NewNode(id, "10.0.0."+string(rune('1'+i)))
		ring.AddNode(node)
	}
	
	// Stabilize before and after
	ring.Stabilize()
	
	// Verify integrity
	ok, issues := ring.VerifyRingIntegrity()
	if !ok {
		t.Errorf("Ring integrity after stabilize: %v", issues)
	}
}

func TestChordRingEmptyLookup(t *testing.T) {
	ring := NewChordRing()
	
	node, hops := ring.Lookup("test-key")
	
	if node != nil {
		t.Errorf("Lookup on empty ring should return nil, got %d", node.ID)
	}
	if hops != 0 {
		t.Errorf("Lookup on empty ring should return 0 hops, got %d", hops)
	}
}

func TestChordRingSingleNode(t *testing.T) {
	ring := NewChordRing()
	
	id := GenerateNodeID("single-node")
	node := NewNode(id, "127.0.0.1:8000")
	ring.AddNode(node)
	
	ring.Stabilize()
	
	// Store and retrieve on single node
	ring.Store("key", "value")
	val, found := ring.Retrieve("key")
	if !found {
		t.Error("Should retrieve from single node")
	}
	if val != "value" {
		t.Errorf("Value = %s, want value", val)
	}
}

func TestChordRingMultipleStores(t *testing.T) {
	ring := NewChordRing()
	
	// Add nodes
	for i := 0; i < 5; i++ {
		id := GenerateNodeID("node-10.0.0." + string(rune('1'+i)))
		node := NewNode(id, "10.0.0."+string(rune('1'+i)))
		ring.AddNode(node)
	}
	
	ring.Stabilize()
	
	// Store multiple keys
	for i := 0; i < 20; i++ {
		key := "key-" + string(rune('0'+i%10))
		ring.Store(key, "value-"+string(rune('0'+i%10)))
	}
	
	// Verify all keys are retrievable
	for i := 0; i < 20; i++ {
		key := "key-" + string(rune('0'+i%10))
		val, found := ring.Retrieve(key)
		if !found {
			t.Errorf("Key %s not found after storage", key)
		}
		_ = val
	}
}
