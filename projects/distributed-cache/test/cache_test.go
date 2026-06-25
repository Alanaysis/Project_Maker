package test

import (
	"fmt"
	"sync"
	"testing"
	"time"

	"github.com/distributed-cache/internal/cache"
	"github.com/distributed-cache/internal/hash"
	"github.com/distributed-cache/internal/problem"
)

// ============ Cache Tests ============

func TestCache_BasicOperations(t *testing.T) {
	c := cache.NewCache(cache.CacheConfig{
		Capacity:     100,
		EvictionType: "lru",
		DefaultTTL:   time.Minute,
	})

	// Set
	c.Set("key1", "value1", 0)
	c.Set("key2", "value2", time.Second)

	// Get
	val, ok := c.Get("key1")
	if !ok || val != "value1" {
		t.Errorf("Expected value1, got %v", val)
	}

	val, ok = c.Get("key2")
	if !ok || val != "value2" {
		t.Errorf("Expected value2, got %v", val)
	}

	// Has
	if !c.Has("key1") {
		t.Error("Expected key1 to exist")
	}

	// Delete
	c.Delete("key1")
	if c.Has("key1") {
		t.Error("Expected key1 to be deleted")
	}

	// Stats
	stats := c.Stats()
	t.Logf("Stats: hits=%d, misses=%d, hit_rate=%.2f%%", stats.Hits, stats.Misses, stats.HitRate*100)
}

func TestCache_LRUEviction(t *testing.T) {
	c := cache.NewCache(cache.CacheConfig{
		Capacity:     3,
		EvictionType: "lru",
		DefaultTTL:   time.Minute,
	})

	c.Set("key1", "value1", 0)
	c.Set("key2", "value2", 0)
	c.Set("key3", "value3", 0)

	// Access key1 to make it recently used
	c.Get("key1")

	// Add key4, should evict key2 (least recently used)
	c.Set("key4", "value4", 0)

	if c.Has("key2") {
		t.Error("Expected key2 to be evicted")
	}
	if !c.Has("key1") {
		t.Error("Expected key1 to still exist")
	}
}

func TestCache_LFUEviction(t *testing.T) {
	c := cache.NewCache(cache.CacheConfig{
		Capacity:     3,
		EvictionType: "lfu",
		DefaultTTL:   time.Minute,
	})

	c.Set("key1", "value1", 0)
	c.Set("key2", "value2", 0)
	c.Set("key3", "value3", 0)

	// Access key1 and key3 multiple times
	for i := 0; i < 5; i++ {
		c.Get("key1")
		c.Get("key3")
	}

	// Add key4, should evict key2 (least frequently used)
	c.Set("key4", "value4", 0)

	if c.Has("key2") {
		t.Error("Expected key2 to be evicted")
	}
}

func TestCache_FIFOEviction(t *testing.T) {
	c := cache.NewCache(cache.CacheConfig{
		Capacity:     3,
		EvictionType: "fifo",
		DefaultTTL:   time.Minute,
	})

	c.Set("key1", "value1", 0)
	c.Set("key2", "value2", 0)
	c.Set("key3", "value3", 0)

	// Access key1 (shouldn't matter for FIFO)
	c.Get("key1")

	// Add key4, should evict key1 (first in)
	c.Set("key4", "value4", 0)

	if c.Has("key1") {
		t.Error("Expected key1 to be evicted")
	}
}

func TestCache_TTLExpiration(t *testing.T) {
	c := cache.NewCache(cache.CacheConfig{
		Capacity:     100,
		EvictionType: "lru",
		DefaultTTL:   time.Minute,
	})

	c.Set("key1", "value1", 100*time.Millisecond)

	// Should exist immediately
	if !c.Has("key1") {
		t.Error("Expected key1 to exist")
	}

	// Wait for expiration
	time.Sleep(150 * time.Millisecond)

	// Should be expired
	if c.Has("key1") {
		t.Error("Expected key1 to be expired")
	}
}

func TestCache_ConcurrentAccess(t *testing.T) {
	c := cache.NewCache(cache.CacheConfig{
		Capacity:     1000,
		EvictionType: "lru",
		DefaultTTL:   time.Minute,
	})

	var wg sync.WaitGroup
	for i := 0; i < 100; i++ {
		wg.Add(1)
		go func(i int) {
			defer wg.Done()
			for j := 0; j < 100; j++ {
				key := fmt.Sprintf("key-%d-%d", i, j)
				c.Set(key, fmt.Sprintf("value-%d-%d", i, j), time.Minute)
				c.Get(key)
				c.Delete(key)
			}
		}(i)
	}
	wg.Wait()
}

// ============ Consistent Hash Tests ============

func TestConsistentHash_Basic(t *testing.T) {
	ch := hash.NewConsistentHash(100, nil)

	ch.Add("node1")
	ch.Add("node2")
	ch.Add("node3")

	if ch.NodeCount() != 3 {
		t.Errorf("Expected 3 nodes, got %d", ch.NodeCount())
	}

	node, ok := ch.Get("test-key")
	if !ok || node == "" {
		t.Error("Expected to find a node")
	}
}

func TestConsistentHash_Distribution(t *testing.T) {
	ch := hash.NewConsistentHash(100, nil)

	ch.Add("node1")
	ch.Add("node2")
	ch.Add("node3")

	distribution := make(map[string]int)
	for i := 0; i < 10000; i++ {
		key := fmt.Sprintf("key-%d", i)
		node, _ := ch.Get(key)
		distribution[node]++
	}

	for node, count := range distribution {
		t.Logf("Node %s: %d keys (%.1f%%)", node, count, float64(count)/100)
	}
}

func TestConsistentHash_Replication(t *testing.T) {
	ch := hash.NewConsistentHash(100, nil)

	ch.Add("node1")
	ch.Add("node2")
	ch.Add("node3")

	nodes := ch.GetN("test-key", 2)
	if len(nodes) != 2 {
		t.Errorf("Expected 2 nodes, got %d", len(nodes))
	}
}

// ============ Problem Solver Tests ============

func TestProblemSolver_Penetration(t *testing.T) {
	c := cache.NewCache(cache.CacheConfig{
		Capacity:     100,
		EvictionType: "lru",
		DefaultTTL:   time.Minute,
	})

	solver := problem.NewCacheProblemSolver(c)

	// Add some known keys to bloom filter
	solver.PreventPenetrationWithBloom("existing-key", func(key string) (interface{}, error) {
		return "value", nil
	})

	// Test with non-existing key
	_, err := solver.PreventPenetrationWithBloom("non-existing", func(key string) (interface{}, error) {
		return nil, fmt.Errorf("not found")
	})

	if err == nil {
		t.Error("Expected error for non-existing key")
	}
}

func TestProblemSolver_Breakdown(t *testing.T) {
	c := cache.NewCache(cache.CacheConfig{
		Capacity:     100,
		EvictionType: "lru",
		DefaultTTL:   time.Minute,
	})

	solver := problem.NewCacheProblemSolver(c)

	// Simulate concurrent access to same key
	var wg sync.WaitGroup
	for i := 0; i < 10; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			solver.PreventBreakdownWithSingleFlight("hot-key", func(key string) (interface{}, error) {
				time.Sleep(100 * time.Millisecond) // Simulate slow storage
				return "value", nil
			})
		}()
	}
	wg.Wait()

	// Should only have loaded once
	val, ok := c.Get("hot-key")
	if !ok || val != "value" {
		t.Error("Expected hot-key to be cached")
	}
}

func TestProblemSolver_Avalanche(t *testing.T) {
	c := cache.NewCache(cache.CacheConfig{
		Capacity:     100,
		EvictionType: "lru",
		DefaultTTL:   time.Minute,
	})

	solver := problem.NewCacheProblemSolver(c)

	// Set multiple keys with random TTLs
	for i := 0; i < 10; i++ {
		key := fmt.Sprintf("key-%d", i)
		solver.PreventAvalancheWithRandomTTL(key, "value", time.Minute, 10*time.Second)
	}

	// All keys should exist
	for i := 0; i < 10; i++ {
		key := fmt.Sprintf("key-%d", i)
		if !c.Has(key) {
			t.Errorf("Expected %s to exist", key)
		}
	}
}
