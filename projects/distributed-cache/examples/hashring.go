package main

import (
	"fmt"
	"sort"

	"example.com/distributed-cache/src"
)

func main() {
	fmt.Println("=== Consistent Hashing Visualization ===")
	fmt.Println()

	// Create a hashring with virtual nodes
	hashRing := hashring.New(160) // 160 virtual nodes per real node

	// Add nodes
	nodes := []string{"node-1", "node-2", "node-3", "node-4"}
	for _, n := range nodes {
		hashRing.AddNode(n)
	}

	fmt.Println("--- Hash Ring Layout ---")
	fmt.Printf("Nodes on ring: %d\n", len(nodes))
	fmt.Printf("Virtual nodes per real node: 160\n")
	fmt.Printf("Total points on ring: %d\n", len(hashRing.SortedKeys()))

	fmt.Println()

	// Assign keys to nodes
	fmt.Println("--- Key Distribution ---")
	testKeys := []string{
		"user:1", "user:2", "user:3", "user:4", "user:5",
		"session:abc", "session:def", "session:ghi",
		"config:main", "config:backup",
		"product:100", "product:200", "product:300",
		"order:5001", "order:5002",
		"cache:warm", "cache:hot",
		"index:a", "index:b", "index:c",
	}

	// Count distribution
	dist := make(map[string]int)
	for _, key := range testKeys {
		node := hashRing.GetNode(key)
		dist[node]++
	}

	// Sort for display
	type kv struct {
		Key   string
		Value int
	}
	var sorted []kv
	for k, v := range dist {
		sorted = append(sorted, kv{k, v})
	}
	sort.Slice(sorted, func(i, j int) bool {
		return sorted[i].Value > sorted[j].Value
	})

	for _, kv := range sorted {
		bar := ""
		for i := 0; i < kv.Value; i++ {
			bar += "█"
		}
		fmt.Printf("  %-10s: %2d keys |%s\n", kv.Key, kv.Value, bar)
	}

	fmt.Println()

	// Show which node handles each key
	fmt.Println("--- Key -> Node Mapping ---")
	for _, key := range testKeys {
		node := hashRing.GetNode(key)
		fmt.Printf("  %-15s -> %s\n", key, node)
	}

	fmt.Println()

	// Demonstrate virtual node benefit
	fmt.Println("--- Without Virtual Nodes (problematic) ---")
	simpleRing := hashring.New(0) // no virtual nodes
	for _, n := range nodes {
		simpleRing.AddNode(n)
	}

	simpleDist := make(map[string]int)
	for _, key := range testKeys {
		node := simpleRing.GetNode(key)
		simpleDist[node]++
	}

	fmt.Println("  Key distribution is uneven with no virtual nodes!")
	for _, kv := range sorted {
		fmt.Printf("  %-10s: %2d keys\n", kv.Key, simpleDist[kv.Key])
	}

	fmt.Println()

	// Demonstrate node removal
	fmt.Println("--- Node Removal Impact ---")
	fmt.Println("Removing node-2...")
	hashRing.RemoveNode("node-2")

	newDist := make(map[string]int)
	for _, key := range testKeys {
		node := hashRing.GetNode(key)
		newDist[node]++
	}

	fmt.Println("  New distribution:")
	for _, kv := range sorted {
		fmt.Printf("  %-10s: %2d keys\n", kv.Key, newDist[kv.Key])
	}

	fmt.Println()
	fmt.Println("Note: Only keys that were on node-2 need to be remapped.")
	fmt.Println("Virtual nodes ensure even distribution and minimal remapping.")
}
