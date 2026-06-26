// Package main demonstrates key lookup in a Chord DHT.
//
// This example shows:
// 1. Storing key-value pairs in the ring
// 2. Looking up keys to find responsible nodes
// 3. Verifying data retrieval
// 4. Understanding key distribution
package main

import (
	"fmt"
	"dht/src"
)

func main() {
	fmt.Println("=== Chord DHT - Key Lookup Demo ===")
	fmt.Println()
	
	// Create a new ring simulator
	sim := chord.NewRingSimulator()
	
	// Join 5 nodes
	fmt.Println("1. Joining nodes:")
	nodeAddrs := []string{
		"node-10.0.0.1",
		"node-10.0.0.2",
		"node-10.0.0.3",
		"node-10.0.0.4",
		"node-10.0.0.5",
	}
	for _, addr := range nodeAddrs {
		sim.JoinNode(addr)
	}
	sim.PrintStatus()
	
	// Store some key-value pairs
	fmt.Println("2. Storing key-value pairs:")
	keyValuePairs := map[string]string{
		"user:1":    "Alice",
		"user:2":    "Bob",
		"user:3":    "Charlie",
		"config:db": "postgres://localhost:5432",
		"config:api": "http://api.example.com",
		"cache:page": "<html>Hello</html>",
		"session:abc": "token123",
		"session:def": "token456",
		"file:readme": "DHT Tutorial",
		"file:license": "MIT",
	}
	
	for key, value := range keyValuePairs {
		sim.StoreKey(key, value)
		fmt.Printf("  Stored: %s = %s\n", key, value)
	}
	
	// Print ring status after storing
	sim.PrintStatus()
	
	// Look up keys
	fmt.Println("3. Looking up keys:")
	for key := range keyValuePairs {
		value, found := sim.RetrieveKey(key)
		if found {
			fmt.Printf("  Lookup %s -> %s (found)\n", key, value)
		} else {
			fmt.Printf("  Lookup %s -> NOT FOUND\n", key)
		}
	}
	
	// Look up non-existent key
	fmt.Println("\n4. Looking up non-existent key:")
	value, found := sim.RetrieveKey("user:99")
	if found {
		fmt.Printf("  Lookup user:99 -> %s\n", value)
	} else {
		fmt.Println("  Lookup user:99 -> NOT FOUND (expected)")
	}
	
	// Verify ring integrity
	fmt.Println("\n5. Ring integrity check:")
	sim.Verify()
	
	fmt.Println("\n=== Demo Complete ===")
}
