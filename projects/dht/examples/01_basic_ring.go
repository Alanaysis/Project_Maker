// Package main demonstrates a basic Chord ring with multiple nodes.
//
// This example shows:
// 1. Creating a Chord ring
// 2. Adding nodes to the ring
// 3. The ring structure and finger tables
// 4. Ring integrity verification
package main

import (
	"fmt"
	"dht/src"
)

func main() {
	fmt.Println("=== Chord DHT - Basic Ring Demo ===")
	fmt.Println()
	
	// Create a new ring simulator
	sim := chord.NewRingSimulator()
	
	// Join nodes to the ring
	fmt.Println("1. Joining nodes to the ring:")
	nodes := []string{
		"node-192.168.1.1",
		"node-192.168.1.2",
		"node-192.168.1.3",
		"node-192.168.1.4",
		"node-192.168.1.5",
	}
	
	for _, addr := range nodes {
		sim.JoinNode(addr)
	}
	
	// Print ring status
	sim.PrintStatus()
	
	// Verify ring integrity
	fmt.Println("2. Ring integrity check:")
	sim.Verify()
	fmt.Println()
	
	// Show finger tables
	fmt.Println("3. Finger tables:")
	for _, addr := range nodes {
		nodeID := chord.GenerateNodeID(addr)
		if node, ok := sim.ring.GetNode(nodeID); ok {
			fmt.Printf("\n%s (ID: %d):\n", addr, node.ID)
			fmt.Println(node.FingerTableString())
		}
	}
	
	fmt.Println("=== Demo Complete ===")
}
