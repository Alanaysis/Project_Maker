package main

import (
	"fmt"
	"sync"
	"time"

	"example.com/distributed-cache/src"
)

func main() {
	fmt.Println("=== Cache Performance Benchmarking ===")
	fmt.Println()

	benchLRU()
	fmt.Println()
	benchLFU()
	fmt.Println()
	benchTTL()
	fmt.Println()
	benchCluster()
}

func benchLRU() {
	fmt.Println("--- LRU Cache Benchmark ---")

	capacities := []int{100, 1000, 10000, 100000}
	ops := 100000

	for _, cap := range capacities {
		cache := cache.NewNode("bench-lru", cap, cache.LRU)

		// Warm up
		for i := 0; i < cap; i++ {
			cache.Set(fmt.Sprintf("key%d", i), fmt.Sprintf("val%d", i))
		}

		start := time.Now()
		var wg sync.WaitGroup
		for i := 0; i < ops; i++ {
			wg.Add(1)
			go func(idx int) {
				defer wg.Done()
				key := fmt.Sprintf("key%d", idx%cap)
				cache.Get(key)
				cache.Set(key, fmt.Sprintf("val%d", idx))
			}(i)
		}
		wg.Wait()
		elapsed := time.Since(start)

		stats := cache.Stats()
		fmt.Printf("  Cap=%6d | Ops=%6d | Time=%-8s | Hits=%5d | Misses=%5d | Ratio=%.1f%%\n",
			cap, ops, elapsed, stats.Hits, stats.Misses,
			float64(stats.Hits)/float64(stats.Gets)*100)
	}
}

func benchLFU() {
	fmt.Println("--- LFU Cache Benchmark ---")

	capacities := []int{100, 1000, 10000, 100000}
	ops := 100000

	for _, cap := range capacities {
		cache := cache.NewNode("bench-lfu", cap, cache.LFU)

		// Warm up
		for i := 0; i < cap; i++ {
			cache.Set(fmt.Sprintf("key%d", i), fmt.Sprintf("val%d", i))
		}

		start := time.Now()
		var wg sync.WaitGroup
		for i := 0; i < ops; i++ {
			wg.Add(1)
			go func(idx int) {
				defer wg.Done()
				key := fmt.Sprintf("key%d", idx%cap)
				cache.Get(key)
				cache.Set(key, fmt.Sprintf("val%d", idx))
			}(i)
		}
		wg.Wait()
		elapsed := time.Since(start)

		stats := cache.Stats()
		fmt.Printf("  Cap=%6d | Ops=%6d | Time=%-8s | Hits=%5d | Misses=%5d | Ratio=%.1f%%\n",
			cap, ops, elapsed, stats.Hits, stats.Misses,
			float64(stats.Hits)/float64(stats.Gets)*100)
	}
}

func benchTTL() {
	fmt.Println("--- TTL Cache Benchmark ---")

	cap := 10000
	ops := 100000
	cache := cache.NewNode("bench-ttl", cap, cache.TTL)

	// Set items with 1-second TTL
	for i := 0; i < cap; i++ {
		cache.SetWithTTL(fmt.Sprintf("key%d", i), fmt.Sprintf("val%d", i), time.Second)
	}

	start := time.Now()
	var wg sync.WaitGroup
	for i := 0; i < ops; i++ {
		wg.Add(1)
		go func(idx int) {
			defer wg.Done()
			key := fmt.Sprintf("key%d", idx%cap)
			cache.Get(key)
			cache.SetWithTTL(key, fmt.Sprintf("val%d", idx), time.Second)
		}(i)
	}
	wg.Wait()
	elapsed := time.Since(start)

	stats := cache.Stats()
	fmt.Printf("  Cap=%6d | Ops=%6d | Time=%-8s | Hits=%5d | Misses=%5d | Ratio=%.1f%%\n",
		cap, ops, elapsed, stats.Hits, stats.Misses,
		float64(stats.Hits)/float64(stats.Gets)*100)
}

func benchCluster() {
	fmt.Println("--- Cluster Benchmark ---")

	numNodes := 3
	cluster := cache.NewCluster("bench-cluster", numNodes)
	for i := 0; i < numNodes; i++ {
		cluster.AddNode(fmt.Sprintf("bench-node-%d", i), 10000)
	}

	ops := 50000
	start := time.Now()
	var wg sync.WaitGroup
	for i := 0; i < ops; i++ {
		wg.Add(1)
		go func(idx int) {
			defer wg.Done()
			key := fmt.Sprintf("key%d", idx)
			cluster.Set(key, fmt.Sprintf("val%d", idx))
			cluster.Get(key)
		}(i)
	}
	wg.Wait()
	elapsed := time.Since(start)

	stats := cluster.Stats()
	fmt.Printf("  Nodes=%d | Ops=%6d | Time=%-8s | Hits=%5d | Ratio=%.1f%%\n",
		numNodes, ops, elapsed, stats.Hits,
		float64(stats.Hits)/float64(stats.Gets)*100)
}
