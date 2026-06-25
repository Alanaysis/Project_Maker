package main

import (
	"fmt"
	"math/rand"
	"sync"
	"sync/atomic"
	"time"

	"github.com/distributed-cache/internal/cache"
	"github.com/distributed-cache/internal/hash"
)

func main() {
	fmt.Println("=== Distributed Cache Benchmark ===")
	fmt.Println()

	// Benchmark single cache
	benchmarkSingleCache()

	// Benchmark consistent hashing
	benchmarkConsistentHash()

	// Benchmark concurrent access
	benchmarkConcurrentAccess()
}

func benchmarkSingleCache() {
	fmt.Println("--- Single Cache Benchmark ---")

	configs := []struct {
		name    string
		eviction string
	}{
		{"LRU", "lru"},
		{"LFU", "lfu"},
		{"FIFO", "fifo"},
		{"TTL", "ttl"},
	}

	for _, cfg := range configs {
		c := cache.NewCache(cache.CacheConfig{
			Capacity:     10000,
			EvictionType: cfg.eviction,
			DefaultTTL:   time.Minute,
		})

		// Write benchmark
		start := time.Now()
		for i := 0; i < 100000; i++ {
			key := fmt.Sprintf("key-%d", i)
			c.Set(key, fmt.Sprintf("value-%d", i), time.Minute)
		}
		writeDuration := time.Since(start)

		// Read benchmark
		start = time.Now()
		for i := 0; i < 100000; i++ {
			key := fmt.Sprintf("key-%d", i%100000)
			c.Get(key)
		}
		readDuration := time.Since(start)

		stats := c.Stats()
		fmt.Printf("%s:\n", cfg.name)
		fmt.Printf("  Write: %v (%.0f ops/sec)\n", writeDuration, 100000/writeDuration.Seconds())
		fmt.Printf("  Read:  %v (%.0f ops/sec)\n", readDuration, 100000/readDuration.Seconds())
		fmt.Printf("  Hit Rate: %.2f%%\n", stats.HitRate*100)
		fmt.Println()
	}
}

func benchmarkConsistentHash() {
	fmt.Println("--- Consistent Hash Benchmark ---")

	nodeCounts := []int{3, 5, 10, 20}
	keyCount := 100000

	for _, nodeCount := range nodeCounts {
		ch := hash.NewConsistentHash(150, nil)
		for i := 0; i < nodeCount; i++ {
			ch.Add(fmt.Sprintf("node-%d", i))
		}

		// Distribution test
		distribution := make(map[string]int)
		start := time.Now()
		for i := 0; i < keyCount; i++ {
			key := fmt.Sprintf("key-%d", i)
			node, _ := ch.Get(key)
			distribution[node]++
		}
		duration := time.Since(start)

		// Calculate standard deviation
		mean := float64(keyCount) / float64(nodeCount)
		variance := 0.0
		for _, count := range distribution {
			diff := float64(count) - mean
			variance += diff * diff
		}
	 stddev := variance / float64(nodeCount)

		fmt.Printf("Nodes: %d\n", nodeCount)
		fmt.Printf("  Lookup: %v (%.0f ops/sec)\n", duration, float64(keyCount)/duration.Seconds())
		fmt.Printf("  StdDev: %.2f (%.1f%%)\n", stddev, stddev/mean*100)
		fmt.Println()
	}
}

func benchmarkConcurrentAccess() {
	fmt.Println("--- Concurrent Access Benchmark ---")

	concurrencyLevels := []int{1, 10, 50, 100}

	for _, concurrency := range concurrencyLevels {
		c := cache.NewCache(cache.CacheConfig{
			Capacity:     10000,
			EvictionType: "lru",
			DefaultTTL:   time.Minute,
		})

		// Pre-populate
		for i := 0; i < 1000; i++ {
			c.Set(fmt.Sprintf("key-%d", i), fmt.Sprintf("value-%d", i), time.Minute)
		}

		var ops int64
		var wg sync.WaitGroup

		start := time.Now()
		for i := 0; i < concurrency; i++ {
			wg.Add(1)
			go func() {
				defer wg.Done()
				for j := 0; j < 10000; j++ {
					key := fmt.Sprintf("key-%d", rand.Intn(1000))
					if rand.Float64() < 0.7 { // 70% reads
						c.Get(key)
					} else { // 30% writes
						c.Set(key, "new-value", time.Minute)
					}
					atomic.AddInt64(&ops, 1)
				}
			}()
		}
		wg.Wait()
		duration := time.Since(start)

		fmt.Printf("Concurrency: %d\n", concurrency)
		fmt.Printf("  Duration: %v\n", duration)
		fmt.Printf("  Throughput: %.0f ops/sec\n", float64(ops)/duration.Seconds())
		fmt.Println()
	}
}
