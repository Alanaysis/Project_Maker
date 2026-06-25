package test

import (
	"testing"
	"time"

	"github.com/dht-chord/internal"
)

// ==================== DistributedStorage Tests ====================

func TestDistributedStoragePutGet(t *testing.T) {
	node := internal.NewNetworkNode("localhost:19020")
	if err := node.Start(); err != nil {
		t.Fatalf("Failed to start node: %v", err)
	}
	defer node.Stop()

	time.Sleep(100 * time.Millisecond)

	storage := internal.NewDistributedStorage(node, 3)

	// Put
	if err := storage.Put("key1", "value1", 0); err != nil {
		t.Fatalf("Failed to put: %v", err)
	}

	// Get
	value, err := storage.Get("key1")
	if err != nil {
		t.Fatalf("Failed to get: %v", err)
	}
	if value != "value1" {
		t.Errorf("Got %s, want value1", value)
	}

	// Get non-existent
	_, err = storage.Get("nonexistent")
	if err == nil {
		t.Error("Getting non-existent key should fail")
	}
}

func TestDistributedStorageDelete(t *testing.T) {
	node := internal.NewNetworkNode("localhost:19021")
	if err := node.Start(); err != nil {
		t.Fatalf("Failed to start node: %v", err)
	}
	defer node.Stop()

	time.Sleep(100 * time.Millisecond)

	storage := internal.NewDistributedStorage(node, 3)

	// Put and delete
	storage.Put("key1", "value1", 0)
	if err := storage.Delete("key1"); err != nil {
		t.Fatalf("Failed to delete: %v", err)
	}

	// Verify deletion
	_, err := storage.Get("key1")
	if err == nil {
		t.Error("Getting deleted key should fail")
	}
}

func TestDistributedStorageTTL(t *testing.T) {
	node := internal.NewNetworkNode("localhost:19022")
	if err := node.Start(); err != nil {
		t.Fatalf("Failed to start node: %v", err)
	}
	defer node.Stop()

	time.Sleep(100 * time.Millisecond)

	storage := internal.NewDistributedStorage(node, 3)

	// Put with TTL
	storage.Put("key1", "value1", 1) // 1 second TTL

	// Should exist immediately
	value, err := storage.Get("key1")
	if err != nil {
		t.Fatalf("Failed to get: %v", err)
	}
	if value != "value1" {
		t.Errorf("Got %s, want value1", value)
	}

	// Wait for expiry
	time.Sleep(1100 * time.Millisecond)

	// Should be expired
	_, err = storage.Get("key1")
	if err == nil {
		t.Error("Key should be expired")
	}
}

func TestDistributedStorageList(t *testing.T) {
	node := internal.NewNetworkNode("localhost:19023")
	if err := node.Start(); err != nil {
		t.Fatalf("Failed to start node: %v", err)
	}
	defer node.Stop()

	time.Sleep(100 * time.Millisecond)

	storage := internal.NewDistributedStorage(node, 3)

	// Put multiple items
	storage.Put("key1", "value1", 0)
	storage.Put("key2", "value2", 0)
	storage.Put("key3", "value3", 0)

	// List
	keys := storage.List()
	if len(keys) != 3 {
		t.Errorf("List returned %d keys, want 3", len(keys))
	}
}

func TestDistributedStorageSize(t *testing.T) {
	node := internal.NewNetworkNode("localhost:19024")
	if err := node.Start(); err != nil {
		t.Fatalf("Failed to start node: %v", err)
	}
	defer node.Stop()

	time.Sleep(100 * time.Millisecond)

	storage := internal.NewDistributedStorage(node, 3)

	// Empty
	if storage.Size() != 0 {
		t.Errorf("Size should be 0, got %d", storage.Size())
	}

	// Add items
	storage.Put("key1", "value1", 0)
	storage.Put("key2", "value2", 0)

	if storage.Size() != 2 {
		t.Errorf("Size should be 2, got %d", storage.Size())
	}
}

func TestDistributedStorageStats(t *testing.T) {
	node := internal.NewNetworkNode("localhost:19025")
	if err := node.Start(); err != nil {
		t.Fatalf("Failed to start node: %v", err)
	}
	defer node.Stop()

	time.Sleep(100 * time.Millisecond)

	storage := internal.NewDistributedStorage(node, 3)

	storage.Put("key1", "value1", 0)
	storage.Put("key2", "value2", 60)

	stats := storage.Stats()
	if stats["total_items"] != 2 {
		t.Errorf("Stats total_items = %v, want 2", stats["total_items"])
	}
	if stats["replicas"] != 3 {
		t.Errorf("Stats replicas = %v, want 3", stats["replicas"])
	}
}

func TestDistributedStorageBatchPut(t *testing.T) {
	node := internal.NewNetworkNode("localhost:19026")
	if err := node.Start(); err != nil {
		t.Fatalf("Failed to start node: %v", err)
	}
	defer node.Stop()

	time.Sleep(100 * time.Millisecond)

	storage := internal.NewDistributedStorage(node, 3)

	items := map[string]string{
		"key1": "value1",
		"key2": "value2",
		"key3": "value3",
	}

	if err := storage.BatchPut(items, 0); err != nil {
		t.Fatalf("BatchPut failed: %v", err)
	}

	if storage.Size() != 3 {
		t.Errorf("Size should be 3 after batch put, got %d", storage.Size())
	}
}

func TestDistributedStorageBatchGet(t *testing.T) {
	node := internal.NewNetworkNode("localhost:19027")
	if err := node.Start(); err != nil {
		t.Fatalf("Failed to start node: %v", err)
	}
	defer node.Stop()

	time.Sleep(100 * time.Millisecond)

	storage := internal.NewDistributedStorage(node, 3)

	// Put items
	storage.Put("key1", "value1", 0)
	storage.Put("key2", "value2", 0)

	// Batch get
	keys := []string{"key1", "key2", "key3"}
	results, err := storage.BatchGet(keys)
	if err != nil {
		t.Fatalf("BatchGet failed: %v", err)
	}

	if len(results) != 2 {
		t.Errorf("BatchGet returned %d results, want 2", len(results))
	}

	if results["key1"] != "value1" {
		t.Errorf("key1 = %s, want value1", results["key1"])
	}
}

func TestDistributedStorageCleanup(t *testing.T) {
	node := internal.NewNetworkNode("localhost:19028")
	if err := node.Start(); err != nil {
		t.Fatalf("Failed to start node: %v", err)
	}
	defer node.Stop()

	time.Sleep(100 * time.Millisecond)

	storage := internal.NewDistributedStorage(node, 3)

	// Put items with short TTL
	storage.Put("key1", "value1", 1)
	storage.Put("key2", "value2", 0) // No TTL

	// Wait for expiry
	time.Sleep(1100 * time.Millisecond)

	// Cleanup
	removed := storage.Cleanup()
	if removed != 1 {
		t.Errorf("Cleanup removed %d items, want 1", removed)
	}

	if storage.Size() != 1 {
		t.Errorf("Size after cleanup should be 1, got %d", storage.Size())
	}
}

// ==================== P2PNetwork Tests ====================

func TestP2PNetwork(t *testing.T) {
	node := internal.NewNetworkNode("localhost:19029")
	if err := node.Start(); err != nil {
		t.Fatalf("Failed to start node: %v", err)
	}
	defer node.Stop()

	time.Sleep(100 * time.Millisecond)

	p2p, err := internal.NewP2PNetwork(node, "/tmp/dht_test_files")
	if err != nil {
		t.Fatalf("Failed to create P2P network: %v", err)
	}

	// List files (should be empty)
	files := p2p.ListFiles()
	if len(files) != 0 {
		t.Errorf("ListFiles should return empty, got %d files", len(files))
	}

	// Search files (should be empty)
	results := p2p.SearchFiles("test")
	if len(results) != 0 {
		t.Errorf("SearchFiles should return empty, got %d results", len(results))
	}
}
