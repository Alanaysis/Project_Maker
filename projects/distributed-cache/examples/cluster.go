package main

import (
	"fmt"
	"time"

	"example.com/distributed-cache/src"
)

func main() {
	fmt.Println("=== Multi-Node Cluster Demo ===")
	fmt.Println()

	// Create a 3-node cluster
	cluster := cache.NewCluster("cluster1", 3)

	// Add nodes
	nodes := []string{"node1", "node2", "node3"}
	for _, n := range nodes {
		cluster.AddNode(n, 10)
	}
	fmt.Printf("Cluster %s has %d nodes\n", cluster.Name(), len(cluster.Nodes()))

	fmt.Println()

	// Demonstrate data distribution via consistent hashing
	fmt.Println("--- Data Distribution ---")
	testKeys := []string{
		"user:1", "user:2", "user:3", "user:4", "user:5",
		"config:app", "config:db", "session:abc", "session:def",
		"product:1", "product:2", "product:3",
	}
	for _, key := range testKeys {
		target := cluster.GetNode(key)
		if target != nil {
			fmt.Printf("  %s -> %s\n", key, target.ID())
		}
	}

	fmt.Println()

	// Demonstrate set/get across cluster
	fmt.Println("--- Cluster Set/Get ---")
	cluster.Set("user:1", "Alice")
	cluster.Set("user:2", "Bob")
	cluster.Set("user:3", "Charlie")

	if v, ok := cluster.Get("user:1"); ok {
		fmt.Printf("Got user:1 = %s\n", v)
	}
	if v, ok := cluster.Get("user:2"); ok {
		fmt.Printf("Got user:2 = %s\n", v)
	}

	fmt.Println()

	// Demonstrate node failure scenario
	fmt.Println("--- Node Failure Simulation ---")
	fmt.Printf("Before failure: %d nodes online\n", len(cluster.Nodes()))

	// Remove a node
	cluster.RemoveNode("node2")
	fmt.Printf("After removing node2: %d nodes online\n", len(cluster.Nodes()))

	// Data on removed node is redistributed
	fmt.Println("Redistributed data:")
	for _, key := range testKeys {
		target := cluster.GetNode(key)
		if target != nil {
			fmt.Printf("  %s -> %s\n", key, target.ID())
		}
	}

	fmt.Println()

	// Demonstrate cluster stats
	fmt.Println("--- Cluster Statistics ---")
	stats := cluster.Stats()
	fmt.Printf("Total Gets: %d\n", stats.Gets)
	fmt.Printf("Total Hits: %d\n", stats.Hits)
	if stats.Gets > 0 {
		fmt.Printf("Hit Ratio: %.2f%%\n", float64(stats.Hits)/float64(stats.Gets)*100)
	}
	fmt.Printf("Total Items: %d\n", stats.TotalItems)

	fmt.Println()

	// Demonstrate graceful degradation
	fmt.Println("--- Graceful Degradation ---")
	cluster.Set("critical", "important-data")
	if v, ok := cluster.Get("critical"); ok {
		fmt.Printf("Still accessible: critical = %s\n", v)
	}

	// Add node back
	cluster.AddNode("node2", 10)
	fmt.Printf("After adding node2 back: %d nodes online\n", len(cluster.Nodes()))

	// Wait for any background cleanup
	time.Sleep(50 * time.Millisecond)
}
