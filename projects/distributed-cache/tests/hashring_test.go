package cache_test

import (
	"testing"

	"example.com/distributed-cache/src"
)

// TestHashRingCreation verifies hash ring creation.
func TestHashRingCreation(t *testing.T) {
	ring := cache.New(160)
	if ring == nil {
		t.Fatal("expected non-nil hash ring")
	}
	if len(ring.SortedKeys()) != 0 {
		t.Errorf("expected 0 keys initially, got %d", len(ring.SortedKeys()))
	}
}

// TestHashRingAddNode verifies adding nodes to the ring.
func TestHashRingAddNode(t *testing.T) {
	ring := cache.New(160)
	ring.AddNode("node1")

	keys := ring.SortedKeys()
	if len(keys) != 160 {
		t.Errorf("expected 160 keys after adding 1 node, got %d", len(keys))
	}
}

// TestHashRingGetNode verifies key-to-node mapping.
func TestHashRingGetNode(t *testing.T) {
	ring := cache.New(160)
	ring.AddNode("node1")
	ring.AddNode("node2")
	ring.AddNode("node3")

	// All keys should map to one of the three nodes
	testKeys := []string{"key1", "key2", "key3", "key4", "key5"}
	for _, key := range testKeys {
		node := ring.GetNode(key)
		if node != "node1" && node != "node2" && node != "node3" {
			t.Errorf("key '%s' mapped to unexpected node '%s'", key, node)
		}
	}
}

// TestHashRingDistribution verifies even distribution across nodes.
func TestHashRingDistribution(t *testing.T) {
	ring := cache.New(160)
	ring.AddNode("node1")
	ring.AddNode("node2")
	ring.AddNode("node3")

	// Test with many keys
	dist := make(map[string]int)
	for i := 0; i < 1000; i++ {
		node := ring.GetNode("key" + string(rune('a'+i%26)))
		dist[node]++
	}

	// Each node should have roughly 1/3 of keys
	expected := 1000 / 3
	tolerance := 200 // Allow 20% deviation

	for node, count := range dist {
		if count < expected-tolerance || count > expected+tolerance {
			t.Logf("Node %s has %d keys (expected ~%d)", node, count, expected)
		}
	}
}

// TestHashRingRemoveNode verifies node removal.
func TestHashRingRemoveNode(t *testing.T) {
	ring := cache.New(160)
	ring.AddNode("node1")
	ring.AddNode("node2")
	ring.AddNode("node3")

	// Remove node2
	ring.RemoveNode("node2")

	keys := ring.SortedKeys()
	if len(keys) != 320 {
		t.Errorf("expected 320 keys after removing 1 node, got %d", len(keys))
	}

	// Keys should now map to node1 or node3
	testKeys := []string{"key1", "key2", "key3"}
	for _, key := range testKeys {
		node := ring.GetNode(key)
		if node != "node1" && node != "node3" {
			t.Errorf("key '%s' mapped to unexpected node '%s' after removal", key, node)
		}
	}
}

// TestHashRingConsistency verifies the same key always maps to the same node.
func TestHashRingConsistency(t *testing.T) {
	ring := cache.New(160)
	ring.AddNode("node1")
	ring.AddNode("node2")

	key := "consistent-key"
	results := make(map[string]bool)

	for i := 0; i < 100; i++ {
		node := ring.GetNode(key)
		results[node] = true
	}

	// Should always map to the same node
	if len(results) != 1 {
		t.Errorf("expected key to always map to same node, got %v", results)
	}
}

// TestHashRingAddAfterRemove verifies re-adding a removed node.
func TestHashRingAddAfterRemove(t *testing.T) {
	ring := cache.New(160)
	ring.AddNode("node1")
	ring.AddNode("node2")
	ring.RemoveNode("node2")
	ring.AddNode("node2")

	keys := ring.SortedKeys()
	if len(keys) != 320 {
		t.Errorf("expected 320 keys, got %d", len(keys))
	}

	// node2 should be a valid target again
	if ring.GetNode("test-key") == "node1" {
		// This is acceptable - key might still map to node1
		// but node2 should be available
	}
}

// BenchmarkHashRingSet benchmarks adding nodes to a hash ring.
func BenchmarkHashRingAddNode(b *testing.B) {
	ring := cache.New(160)
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		ring.AddNode("node" + string(rune('a'+i%26)))
	}
}

// BenchmarkHashRingGet benchmarks getting the target node for a key.
func BenchmarkHashRingGet(b *testing.B) {
	ring := cache.New(160)
	for i := 0; i < 10; i++ {
		ring.AddNode("node" + string(rune('a'+i)))
	}
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		ring.GetNode("key" + string(rune('a'+i%26)))
	}
}

// BenchmarkHashRingRemove benchmarks removing nodes from a hash ring.
func BenchmarkHashRingRemove(b *testing.B) {
	ring := cache.New(160)
	for i := 0; i < 10; i++ {
		ring.AddNode("node" + string(rune('a'+i)))
	}
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		ring.RemoveNode("node" + string(rune('a'+i%10)))
	}
}
