package cache_test

import (
	"testing"
	"time"

	"example.com/distributed-cache/src"
)

// TestNodeCreation verifies a new cache node is created correctly.
func TestNodeCreation(t *testing.T) {
	node := cache.NewNode("test-node", 100, cache.LRU)

	if node.ID() != "test-node" {
		t.Errorf("expected ID 'test-node', got '%s'", node.ID())
	}
	if node.Capacity() != 100 {
		t.Errorf("expected capacity 100, got %d", node.Capacity())
	}
	if node.Policy() != cache.LRU {
		t.Errorf("expected policy cache.LRU, got %v", node.Policy())
	}
	if node.Size() != 0 {
		t.Errorf("expected initial size 0, got %d", node.Size())
	}
}

// TestNodeSetGet verifies basic set and get operations.
func TestNodeSetGet(t *testing.T) {
	node := cache.NewNode("test", 10, cache.LRU)

	// Set and get a value
	node.Set("key1", "value1")
	val, ok := node.Get("key1")
	if !ok {
		t.Fatal("expected key1 to exist in cache")
	}
	if val != "value1" {
		t.Errorf("expected 'value1', got '%s'", val)
	}

	// Get non-existent key
	_, ok = node.Get("nonexistent")
	if ok {
		t.Error("expected non-existent key to return false")
	}

	// Size should be 1
	if node.Size() != 1 {
		t.Errorf("expected size 1, got %d", node.Size())
	}
}

// TestNodeOverwrite verifies that setting an existing key updates the value.
func TestNodeOverwrite(t *testing.T) {
	node := cache.NewNode("test", 10, cache.LRU)

	node.Set("key1", "value1")
	node.Set("key1", "value2")

	val, ok := node.Get("key1")
	if !ok || val != "value2" {
		t.Errorf("expected 'value2', got '%s', ok=%v", val, ok)
	}
	if node.Size() != 1 {
		t.Errorf("expected size 1 after overwrite, got %d", node.Size())
	}
}

// TestNodeDelete verifies deletion works correctly.
func TestNodeDelete(t *testing.T) {
	node := cache.NewNode("test", 10, cache.LRU)

	node.Set("key1", "value1")
	if node.Size() != 1 {
		t.Errorf("expected size 1, got %d", node.Size())
	}

	deleted := node.Delete("key1")
	if !deleted {
		t.Error("expected delete to return true")
	}
	if node.Size() != 0 {
		t.Errorf("expected size 0 after delete, got %d", node.Size())
	}

	// Delete non-existent key
	deleted = node.Delete("key1")
	if deleted {
		t.Error("expected delete of non-existent key to return false")
	}
}

// TestLRUEviction verifies cache.LRU eviction policy works correctly.
func TestLRUEviction(t *testing.T) {
	node := cache.NewNode("lru-test", 3, cache.LRU)

	// Fill cache
	node.Set("a", "1")
	node.Set("b", "2")
	node.Set("c", "3")

	// Access 'a' to make it recently used
	node.Get("a")

	// Add 'd', should evict 'b' (least recently used)
	node.Set("d", "4")

	// 'b' should be evicted
	if _, ok := node.Get("b"); ok {
		t.Error("expected 'b' to be evicted by cache.LRU")
	}

	// 'a' should still be present (recently accessed)
	if _, ok := node.Get("a"); !ok {
		t.Error("expected 'a' to still be present (recently accessed)")
	}

	// 'c' and 'd' should be present
	if _, ok := node.Get("c"); !ok {
		t.Error("expected 'c' to be present")
	}
	if _, ok := node.Get("d"); !ok {
		t.Error("expected 'd' to be present")
	}
}

// TestLFUEviction verifies cache.LFU eviction policy works correctly.
func TestLFUEviction(t *testing.T) {
	node := cache.NewNode("lfu-test", 3, cache.LFU)

	// Access 'a' many times to make it hot
	for i := 0; i < 10; i++ {
		node.Set("a", "1")
		node.Get("a")
	}

	// Access 'b' and 'c' once each
	node.Set("b", "2")
	node.Get("b")
	node.Set("c", "3")
	node.Get("c")

	// Add 'd', should evict 'b' or 'c' (both have freq 1, but 'b' was added first)
	node.Set("d", "4")

	// 'a' should definitely survive (freq 20)
	if _, ok := node.Get("a"); !ok {
		t.Error("expected 'a' to survive (highest frequency)")
	}

	// Size should still be 3
	if node.Size() != 3 {
		t.Errorf("expected size 3, got %d", node.Size())
	}
}

// TestTTLEviction verifies cache.TTL-based expiration works correctly.
func TestTTLEviction(t *testing.T) {
	node := cache.NewNode("ttl-test", 100, cache.TTL)

	// Set item with 100ms cache.TTL
	node.SetWithTTL("temp", "value", 100*time.Millisecond)

	// Should be present
	if _, ok := node.Get("temp"); !ok {
		t.Error("expected 'temp' to be present before cache.TTL expires")
	}

	// Wait for cache.TTL to expire
	time.Sleep(150 * time.Millisecond)

	// Should be gone
	if _, ok := node.Get("temp"); ok {
		t.Error("expected 'temp' to be evicted after cache.TTL expires")
	}

	// Item without cache.TTL should still be present
	node.Set("permanent", "forever")
	if _, ok := node.Get("permanent"); !ok {
		t.Error("expected 'permanent' to still be present")
	}
}

// TestLRUCapacityZero verifies unlimited cache works.
func TestLRUCapacityZero(t *testing.T) {
	node := cache.NewNode("unlimited", 0, cache.LRU)

	// Should never evict
	for i := 0; i < 1000; i++ {
		node.Set("key", "value")
	}

	if node.Size() != 1 {
		t.Errorf("expected size 1 for unlimited cache, got %d", node.Size())
	}
}

// TestStats verifies cache statistics are tracked correctly.
func TestStats(t *testing.T) {
	node := cache.NewNode("stats-test", 100, cache.LRU)

	node.Set("a", "1")
	node.Set("b", "2")
	node.Get("a")
	node.Get("a")
	node.Get("nonexistent")

	stats := node.Stats()

	if stats.Gets != 3 {
		t.Errorf("expected 3 gets, got %d", stats.Gets)
	}
	if stats.Hits != 2 {
		t.Errorf("expected 2 hits, got %d", stats.Hits)
	}
	if stats.Misses != 1 {
		t.Errorf("expected 1 miss, got %d", stats.Misses)
	}
	if stats.Sets != 2 {
		t.Errorf("expected 2 sets, got %d", stats.Sets)
	}
	if stats.TotalItems != 2 {
		t.Errorf("expected 2 total items, got %d", stats.TotalItems)
	}

	// Hit ratio should be 2/3
	hitRatio := float64(stats.Hits) / float64(stats.Gets) * 100
	if hitRatio != 66.67 {
		t.Logf("hit ratio: %.2f%%", hitRatio)
	}
}

// TestHotKeyDetection verifies hot key detection works.
func TestHotKeyDetection(t *testing.T) {
	node := cache.NewNode("hot-test", 100, cache.LFU)

	// Access 'hot-key' many times
	for i := 0; i < 100; i++ {
		node.Set("hot-key", "value")
		node.Get("hot-key")
	}

	// Access 'cold-key' once
	node.Set("cold-key", "value")
	node.Get("cold-key")

	hotKeys := node.HotKeys(50)

	found := false
	for _, hk := range hotKeys {
		if hk.Key == "hot-key" && hk.Count >= 100 {
			found = true
			break
		}
	}
	if !found {
		t.Error("expected to find 'hot-key' as a hot key")
	}
}

// TestWarm verifies cache warming works correctly.
func TestWarm(t *testing.T) {
	node := cache.NewNode("warm-test", 100, cache.LRU)

	warmData := map[string]string{
		"a": "1",
		"b": "2",
		"c": "3",
	}
	node.Warm(warmData)

	if node.Size() != 3 {
		t.Errorf("expected size 3 after warming, got %d", node.Size())
	}

	for key, expected := range warmData {
		val, ok := node.Get(key)
		if !ok {
			t.Errorf("expected key '%s' to be present after warming", key)
		}
		if val != expected {
			t.Errorf("expected '%s' for key '%s', got '%s'", expected, key, val)
		}
	}
}

// TestNodeConcurrent verifies thread safety of cache operations.
func TestNodeConcurrent(t *testing.T) {
	node := cache.NewNode("concurrent", 10000, cache.LRU)

	done := make(chan bool)
	for i := 0; i < 10; i++ {
		go func(id int) {
			for j := 0; j < 100; j++ {
				key := "key" + string(rune('0'+id)) + string(rune('0'+j))
				node.Set(key, "value")
				node.Get(key)
			}
			done <- true
		}(i)
	}

	for i := 0; i < 10; i++ {
		<-done
	}
}

// BenchmarkNodeSet benchmarks the Set operation.
func BenchmarkNodeSet(b *testing.B) {
	node := cache.NewNode("bench", 10000, cache.LRU)
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		node.Set("key", "value")
	}
}

// BenchmarkNodeGet benchmarks the Get operation.
func BenchmarkNodeGet(b *testing.B) {
	node := cache.NewNode("bench", 10000, cache.LRU)
	for i := 0; i < 10000; i++ {
		node.Set("key", "value")
	}
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		node.Get("key")
	}
}

// BenchmarkNodeGetMiss benchmarks the Get operation for cache misses.
func BenchmarkNodeGetMiss(b *testing.B) {
	node := cache.NewNode("bench", 10000, cache.LRU)
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		node.Get("nonexistent")
	}
}
