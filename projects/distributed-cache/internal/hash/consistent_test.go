package hash

import (
	"fmt"
	"testing"
)

func TestConsistentHash_Basic(t *testing.T) {
	ch := NewConsistentHash(100, nil)

	// Add nodes
	ch.Add("node1")
	ch.Add("node2")
	ch.Add("node3")

	if ch.NodeCount() != 3 {
		t.Errorf("Expected 3 nodes, got %d", ch.NodeCount())
	}

	// Get node for key
	node, ok := ch.Get("test-key")
	if !ok {
		t.Error("Expected to find a node")
	}
	if node == "" {
		t.Error("Expected non-empty node")
	}

	t.Logf("Key 'test-key' maps to node: %s", node)
}

func TestConsistentHash_Distribution(t *testing.T) {
	ch := NewConsistentHash(100, nil)

	ch.Add("node1")
	ch.Add("node2")
	ch.Add("node3")

	distribution := make(map[string]int)
	for i := 0; i < 10000; i++ {
		key := fmt.Sprintf("key-%d", i)
		node, _ := ch.Get(key)
		distribution[node]++
	}

	t.Log("Distribution:")
	for node, count := range distribution {
		t.Logf("  %s: %d (%.1f%%)", node, count, float64(count)/100)
	}
}

func TestConsistentHash_Replication(t *testing.T) {
	ch := NewConsistentHash(100, nil)

	ch.Add("node1")
	ch.Add("node2")
	ch.Add("node3")

	nodes := ch.GetN("test-key", 2)
	if len(nodes) != 2 {
		t.Errorf("Expected 2 nodes, got %d", len(nodes))
	}

	t.Logf("Key 'test-key' replicas: %v", nodes)
}

func TestConsistentHash_AddRemove(t *testing.T) {
	ch := NewConsistentHash(100, nil)

	ch.Add("node1")
	ch.Add("node2")
	ch.Add("node3")

	// Record initial mapping
	key := "test-key"
	node1, _ := ch.Get(key)

	// Remove a node
	ch.Remove("node3")
	node2, _ := ch.Get(key)

	t.Logf("Before remove: %s, after remove: %s", node1, node2)

	// Add a new node
	ch.Add("node4")
	node3, _ := ch.Get(key)

	t.Logf("After add: %s", node3)
}

func TestConsistentHash_Scaling(t *testing.T) {
	ch := NewConsistentHash(100, nil)

	// Add initial nodes
	ch.Add("node1")
	ch.Add("node2")

	// Record initial mapping
	mappings := make(map[string]string)
	for i := 0; i < 1000; i++ {
		key := fmt.Sprintf("key-%d", i)
		node, _ := ch.Get(key)
		mappings[key] = node
	}

	// Add a new node
	ch.Add("node3")

	// Check how many keys were remapped
	remapped := 0
	for i := 0; i < 1000; i++ {
		key := fmt.Sprintf("key-%d", i)
		node, _ := ch.Get(key)
		if mappings[key] != node {
			remapped++
		}
	}

	t.Logf("Remapped %d/%d keys after adding node3", remapped, 1000)
	// With consistent hashing, we expect ~1/3 of keys to be remapped
	if remapped > 500 {
		t.Errorf("Too many keys remapped: %d", remapped)
	}
}
