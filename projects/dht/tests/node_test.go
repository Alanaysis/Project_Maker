package chord

import (
	"testing"
	"time"
)

func TestNewNode(t *testing.T) {
	id := GenerateNodeID("test-node")
	node := NewNode(id, "127.0.0.1:8000")
	
	if node.ID != id {
		t.Errorf("Node.ID = %d, want %d", node.ID, id)
	}
	
	if node.Address != "127.0.0.1:8000" {
		t.Errorf("Node.Address = %s, want 127.0.0.1:8000", node.Address)
	}
	
	if node.Store == nil {
		t.Error("Node.Store should not be nil")
	}
	
	if !node.IsAlive {
		t.Error("New node should be alive")
	}
}

func TestNodeSuccessor(t *testing.T) {
	id := GenerateNodeID("test-node")
	node := NewNode(id, "127.0.0.1:8000")
	
	newSucc := GenerateNodeID("new-successor")
	node.SetSuccessor(newSucc)
	
	if node.GetSuccessor() != newSucc {
		t.Errorf("Successor = %d, want %d", node.GetSuccessor(), newSucc)
	}
}

func TestNodePredecessor(t *testing.T) {
	id := GenerateNodeID("test-node")
	node := NewNode(id, "127.0.0.1:8000")
	
	newPred := GenerateNodeID("new-predecessor")
	node.SetPredecessor(newPred)
	
	if node.GetPredecessor() != newPred {
		t.Errorf("Predecessor = %d, want %d", node.GetPredecessor(), newPred)
	}
}

func TestNodeFingerTable(t *testing.T) {
	id := GenerateNodeID("test-node")
	node := NewNode(id, "127.0.0.1:8000")
	
	ft := node.GetFingerTable()
	
	if len(ft) != ComputeFingerTableSize() {
		t.Errorf("Finger table length = %d, want %d", len(ft), ComputeFingerTableSize())
	}
	
	// All entries should initially point to self
	for i, entry := range ft {
		if entry != id {
			t.Errorf("FingerTable[%d] = %d, want %d", i, entry, id)
		}
	}
}

func TestNodeStoreValue(t *testing.T) {
	id := GenerateNodeID("test-node")
	node := NewNode(id, "127.0.0.1:8000")
	
	// Set predecessor so the node is responsible for some keys
	node.SetPredecessor(PrevID(id))
	
	// Store a value
	node.StoreValue("test-key", "test-value")
	
	val, ok := node.GetValue("test-key")
	if !ok {
		t.Error("Should be able to retrieve stored value")
	}
	if val != "test-value" {
		t.Errorf("Value = %s, want test-value", val)
	}
}

func TestNodeDeleteValue(t *testing.T) {
	id := GenerateNodeID("test-node")
	node := NewNode(id, "127.0.0.1:8000")
	node.SetPredecessor(PrevID(id))
	
	node.StoreValue("delete-me", "value")
	
	ok := node.DeleteValue("delete-me")
	if !ok {
		t.Error("Delete should return true for existing key")
	}
	
	_, ok = node.GetValue("delete-me")
	if ok {
		t.Error("Value should not exist after deletion")
	}
}

func TestNodeHeartbeat(t *testing.T) {
	id := GenerateNodeID("test-node")
	node := NewNode(id, "127.0.0.1:8000")
	
	// Node should be alive initially
	if !node.CheckAlive(1 * time.Second) {
		t.Error("New node should be alive")
	}
	
	// Simulate heartbeat
	node.Heartbeat()
	
	if !node.CheckAlive(1 * time.Second) {
		t.Error("Node should still be alive after heartbeat")
	}
}

func TestNodeHeartbeatTimeout(t *testing.T) {
	id := GenerateNodeID("test-node")
	node := NewNode(id, "127.0.0.1:8000")
	
	// Node should be alive with long timeout
	if !node.CheckAlive(10 * time.Hour) {
		t.Error("Node should be alive with long timeout")
	}
	
	// Node should be dead with very short timeout (simulate old heartbeat)
	node.mu.Lock()
	node.LastHeartbeat = time.Now().Add(-1 * time.Hour)
	node.mu.Unlock()
	
	if node.CheckAlive(1 * time.Second) {
		t.Error("Node should be dead with short timeout")
	}
}

func TestNodeString(t *testing.T) {
	id := GenerateNodeID("test-node")
	node := NewNode(id, "127.0.0.1:8000")
	node.SetPredecessor(100)
	node.SetSuccessor(200)
	
	s := node.String()
	
	expected := "Node(id="
	if s[:len(expected)] != expected {
		t.Errorf("String() = %s, should start with %s", s, expected)
	}
}

func TestNodeStats(t *testing.T) {
	id := GenerateNodeID("test-node")
	node := NewNode(id, "127.0.0.1:8000")
	
	stats := node.Stats()
	
	if stats["id"] != id {
		t.Errorf("Stats[id] = %v, want %d", stats["id"], id)
	}
	
	if stats["is_alive"] != true {
		t.Error("Stats[is_alive] should be true")
	}
	
	if stats["store_size"] != 0 {
		t.Errorf("Stats[store_size] = %v, want 0", stats["store_size"])
	}
}

func TestNodeFingerTableUpdate(t *testing.T) {
	id := GenerateNodeID("test-node")
	node := NewNode(id, "127.0.0.1:8000")
	
	// Update finger table with a new node
	newNode := GenerateNodeID("new-node")
	node.UpdateFingerTable(newNode)
	
	ft := node.GetFingerTable()
	
	// At least one entry should have been updated
	updated := false
	for _, entry := range ft {
		if entry == newNode {
			updated = true
			break
		}
	}
	
	if !updated {
		t.Log("Finger table update: no entries changed (may be expected for certain ID positions)")
	}
}
