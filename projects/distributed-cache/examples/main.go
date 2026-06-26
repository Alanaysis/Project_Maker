package main

import (
	"fmt"
	"time"

	"example.com/distributed-cache/src"
)

func main() {
	fmt.Println("=== Distributed Cache System Demo ===")
	fmt.Println()

	// Demo 1: LRU Eviction Policy
	fmt.Println("--- Demo 1: LRU (Least Recently Used) Cache ---")
	lruCache := cache.NewNode("node1", 5, cache.LRU)
	demoLRU(lruCache)

	fmt.Println()

	// Demo 2: LFU Eviction Policy
	fmt.Println("--- Demo 2: LFU (Least Frequently Used) Cache ---")
	lfuCache := cache.NewNode("node2", 5, cache.LFU)
	demoLFU(lfuCache)

	fmt.Println()

	// Demo 3: TTL Eviction Policy
	fmt.Println("--- Demo 3: TTL (Time To Live) Cache ---")
	ttlCache := cache.NewNode("node3", 10, cache.TTL)
	demoTTL(ttlCache)

	fmt.Println()

	// Demo 4: Cache Statistics
	fmt.Println("--- Demo 4: Cache Statistics ---")
	statsCache := cache.NewNode("node4", 100, cache.LRU)
	demoStats(statsCache)

	fmt.Println()

	// Demo 5: Hot Key Detection
	fmt.Println("--- Demo 5: Hot Key Detection ---")
	demoHotKey()

	fmt.Println()

	// Demo 6: Cache Warming
	fmt.Println("--- Demo 6: Cache Warming ---")
	demoWarming()
}

func demoLRU(c *cache.Node) {
	// Fill cache
	c.Set("key1", "value1")
	c.Set("key2", "value2")
	c.Set("key3", "value3")
	c.Set("key4", "value4")
	c.Set("key5", "value5")
	fmt.Printf("Cache capacity: %d, Current items: %d\n", c.Capacity(), c.Size())

	// Access key1 to make it recently used
	c.Get("key1")
	time.Sleep(10 * time.Millisecond)

	// Add key6, should evict key2 (least recently used)
	c.Set("key6", "value6")
	fmt.Printf("After adding key6: %d items\n", c.Size())

	// Verify key2 is evicted
	if _, ok := c.Get("key2"); !ok {
		fmt.Println("key2 evicted (LRU working correctly)")
	}
	// Verify key1 survives (it was recently accessed)
	if v, ok := c.Get("key1"); ok {
		fmt.Printf("key1 still present: %s\n", v)
	}
}

func demoLFU(c *cache.Node) {
	// Access key1 many times to make it hot
	for i := 0; i < 10; i++ {
		c.Set("key1", fmt.Sprintf("value1-%d", i))
		c.Get("key1")
	}
	c.Set("key2", "value2")
	c.Set("key3", "value3")
	c.Set("key4", "value4")
	c.Set("key5", "value5")
	fmt.Printf("Cache capacity: %d, Current items: %d\n", c.Capacity(), c.Size())

	// Add key6, should evict key2 (least frequently used)
	c.Set("key6", "value6")
	fmt.Printf("After adding key6: %d items\n", c.Size())

	if _, ok := c.Get("key2"); !ok {
		fmt.Println("key2 evicted (LFU working correctly)")
	}
	if v, ok := c.Get("key1"); ok {
		fmt.Printf("key1 still present (hot key): %s\n", v)
	}
}

func demoTTL(c *cache.Node) {
	c.SetWithTTL("temp", "temporary", 100*time.Millisecond)
	c.Set("permanent", "permanent")

	fmt.Printf("Before TTL: temp=%s\n", c.Get("temp"))
	fmt.Printf("Before TTL: permanent=%s\n", c.Get("permanent"))

	time.Sleep(150 * time.Millisecond)
	fmt.Printf("After TTL: temp exists=%v\n", c.Get("temp"))
	fmt.Printf("After TTL: permanent=%s\n", c.Get("permanent"))
}

func demoStats(c *cache.Node) {
	// Generate some hits and misses
	for i := 0; i < 50; i++ {
		c.Set(fmt.Sprintf("key%d", i), fmt.Sprintf("value%d", i))
	}
	for i := 0; i < 100; i++ {
		c.Get(fmt.Sprintf("key%d", i%60))
		c.Get(fmt.Sprintf("missing%d", i))
	}

	stats := c.Stats()
	fmt.Printf("Total Gets: %d\n", stats.Gets)
	fmt.Printf("Cache Hits: %d\n", stats.Hits)
	fmt.Printf("Cache Misses: %d\n", stats.Misses)
	if stats.Gets > 0 {
		fmt.Printf("Hit Ratio: %.2f%%\n", float64(stats.Hits)/float64(stats.Gets)*100)
	}
}

func demoHotKey() {
	c := cache.NewNode("hotnode", 1000, cache.LRU)

	// Simulate hot key access pattern
	hotKeys := []string{"popular1", "popular2", "popular3"}
	for i := 0; i < 1000; i++ {
		// Hot keys accessed frequently
		for _, k := range hotKeys {
			c.Get(k)
		}
		// Cold keys accessed rarely
		c.Get(fmt.Sprintf("cold%d", i%50))
	}

	hot := c.HotKeys(100)
	fmt.Printf("Hot keys (accessed > 100 times):\n")
	for _, h := range hot {
		fmt.Printf("  %s: %d accesses\n", h.Key, h.Count)
	}
}

func demoWarming() {
	c := cache.NewNode("warmnode", 100, cache.LRU)

	// Pre-populate cache with known important data
	warmData := map[string]string{
		"user:1":  "Alice",
		"user:2":  "Bob",
		"user:3":  "Charlie",
		"config":  "production",
		"session": "active",
	}
	c.Warm(warmData)
	fmt.Printf("Warmed cache with %d entries\n", c.Size())

	// Verify
	for k, v := range warmData {
		if got, ok := c.Get(k); ok {
			fmt.Printf("  %s = %s\n", k, got)
		}
	}
}
