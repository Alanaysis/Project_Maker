package cache_test

import (
	"testing"

	"example.com/distributed-cache/src"
)

// TestClusterCreation verifies cluster initialization.
func TestClusterCreation(t *testing.T) {
	cluster := cache.NewCluster("test-cluster", 3)

	if cluster.Name() != "test-cluster" {
		t.Errorf("expected name 'test-cluster', got '%s'", cluster.Name())
	}
	if len(cluster.Nodes()) != 0 {
		t.Errorf("expected 0 nodes initially, got %d", len(cluster.Nodes()))
	}
}

// TestClusterAddNode verifies adding nodes to a cluster.
func TestClusterAddNode(t *testing.T) {
	cluster := cache.NewCluster("test", 3)
	cluster.AddNode("node1", 100)
	cluster.AddNode("node2", 100)
	cluster.AddNode("node3", 100)

	nodes := cluster.Nodes()
	if len(nodes) != 3 {
		t.Errorf("expected 3 nodes, got %d", len(nodes))
	}
}

// TestClusterSetGet verifies set and get across the cluster.
func TestClusterSetGet(t *testing.T) {
	cluster := cache.NewCluster("test", 3)
	cluster.AddNode("node1", 100)
	cluster.AddNode("node2", 100)
	cluster.AddNode("node3", 100)

	cluster.Set("key1", "value1")
	cluster.Set("key2", "value2")

	val, ok := cluster.Get("key1")
	if !ok {
		t.Error("expected key1 to be found in cluster")
	}
	if val != "value1" {
		t.Errorf("expected 'value1', got '%s'", val)
	}

	val, ok = cluster.Get("key2")
	if !ok {
		t.Error("expected key2 to be found in cluster")
	}
	if val != "value2" {
		t.Errorf("expected 'value2', got '%s'", val)
	}
}

// TestClusterGetNode verifies consistent hashing routing.
func TestClusterGetNode(t *testing.T) {
	cluster := cache.NewCluster("test", 3)
	cluster.AddNode("node1", 100)
	cluster.AddNode("node2", 100)
	cluster.AddNode("node3", 100)

	// Same key should always route to same node
	key := "consistent-key"
	node1 := cluster.GetNode(key)
	node2 := cluster.GetNode(key)

	if node1 != node2 {
		t.Errorf("same key routed to different nodes: %s vs %s", node1.ID(), node2.ID())
	}
}

// TestClusterDelete verifies deletion across the cluster.
func TestClusterDelete(t *testing.T) {
	cluster := cache.NewCluster("test", 3)
	cluster.AddNode("node1", 100)

	cluster.Set("key1", "value1")
	deleted := cluster.Delete("key1")
	if !deleted {
		t.Error("expected delete to return true")
	}

	_, ok := cluster.Get("key1")
	if ok {
		t.Error("expected key1 to be deleted")
	}
}

// TestClusterStats verifies cluster statistics aggregation.
func TestClusterStats(t *testing.T) {
	cluster := cache.NewCluster("test", 3)
	cluster.AddNode("node1", 100)
	cluster.AddNode("node2", 100)
	cluster.AddNode("node3", 100)

	cluster.Set("a", "1")
	cluster.Set("b", "2")
	cluster.Get("a")
	cluster.Get("a")
	cluster.Get("nonexistent")

	stats := cluster.Stats()

	// Stats are aggregated from per-node stats only
	if stats.Gets != 3 {
		t.Errorf("expected 3 gets, got %d", stats.Gets)
	}
	if stats.Hits != 2 {
		t.Errorf("expected 2 hits, got %d", stats.Hits)
	}
	if stats.Misses != 1 {
		t.Errorf("expected 1 miss, got %d", stats.Misses)
	}
}

// TestClusterNodeRemoval verifies graceful node removal.
func TestClusterNodeRemoval(t *testing.T) {
	cluster := cache.NewCluster("test", 3)
	cluster.AddNode("node1", 100)
	cluster.AddNode("node2", 100)
	cluster.AddNode("node3", 100)

	// Set some data
	cluster.Set("key1", "value1")
	cluster.Set("key2", "value2")

	// Remove a node
	cluster.RemoveNode("node2")

	if len(cluster.Nodes()) != 2 {
		t.Errorf("expected 2 nodes after removal, got %d", len(cluster.Nodes()))
	}

	// Data should still be accessible (possibly on a different node)
	_, ok := cluster.Get("key1")
	if !ok {
		t.Error("expected key1 to still be accessible after node removal")
	}
}

// TestClusterString verifies the String method.
func TestClusterString(t *testing.T) {
	cluster := cache.NewCluster("test-cluster", 3)
	cluster.AddNode("node1", 100)

	s := cluster.String()
	expected := "Cluster(test-cluster, 1 nodes)"
	if s != expected {
		t.Errorf("expected '%s', got '%s'", expected, s)
	}
}

// BenchmarkClusterSet benchmarks set operations across the cluster.
func BenchmarkClusterSet(b *testing.B) {
	cluster := cache.NewCluster("bench", 3)
	cluster.AddNode("node1", 10000)
	cluster.AddNode("node2", 10000)
	cluster.AddNode("node3", 10000)
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		cluster.Set("key", "value")
	}
}

// BenchmarkClusterGet benchmarks get operations across the cluster.
func BenchmarkClusterGet(b *testing.B) {
	cluster := cache.NewCluster("bench", 3)
	cluster.AddNode("node1", 10000)
	cluster.AddNode("node2", 10000)
	cluster.AddNode("node3", 10000)
	cluster.Set("key", "value")
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		cluster.Get("key")
	}
}
